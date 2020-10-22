import itertools

from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from api.products.geocoder import Geocoder
from api.products.models import Location, Product, MapboxLocation
from api.products.paginators import StandardResultsSetPagination
from api.products.serializers import ProductSerializer, LocationSerializer


class LocationSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    http_method_names = ("get",)
    serializer_class = LocationSerializer
    search_parameters = [
        openapi.Parameter(
            'text',
            in_=openapi.IN_QUERY,
            description='Search text for a location name',
            type=openapi.TYPE_STRING,
            required=True
        ),
    ]
    geocoder_response = []

    def get_queryset(self):
        text = self.request.query_params.get('text')
        if not text:
            return []
        self.geocoder_response = Geocoder.geocode(text)
        locations = Location.from_mapbox_response(self.geocoder_response)
        return locations

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        MapboxLocation.save_mapbox_response(*self.geocoder_response)
        return response


class ProductsViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    http_method_names = ("get",)
    search_parameters = [
        openapi.Parameter(
            'locationId',
            in_=openapi.IN_QUERY,
            description='Id for a location. Optionally, a (comma-separated) array of values can be passed.',
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            required=False
        ),
    ]

    def get_queryset(self):
        return Product.objects.all()

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        # we need to support both locationId=x&locationId=y and locationId=x,y
        location_ids = list(itertools.chain.from_iterable(
            [loc.split(',') for loc in self.request.query_params.getlist('locationId')]
        ))

        locations_and_contexts = location_ids + MapboxLocation.list_context_locations_ids(location_ids)
        queryset = self.get_queryset().by_location_ids(locations_and_contexts)

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)
