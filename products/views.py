import itertools

from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.response import Response

from api.products.geocoder import Geocoder
from api.products.models import Location, Product
from api.products.serializers import ProductSerializer, LocationSerializer


class LocationSearchViewSet(viewsets.ModelViewSet):
    http_method_names = ("get",)
    models = Location

    def get_queryset(self):
        text = self.request.query_params.get('text')
        if not text:
            return []
        response = Geocoder.geocode(text)
        location = Location.from_mapbox_response(response)
        return location

    def get_serializer_class(self):
        return LocationSerializer


class ProductsViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
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
        locations = list(itertools.chain.from_iterable(
            [loc.split(',') for loc in self.request.query_params.getlist('locationId')]
        ))

        queryset = self.get_queryset().by_location_ids(locations)
        serializer = ProductSerializer(queryset[:10], many=True)
        return Response(serializer.data)
