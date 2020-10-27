from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from api.products.filters import (
    ExactLocationIdFilter,
    IncludeLocationIdFilter,
    OrderByCardinalityFilter,
    JobFunctionsTitleFilter,
    FiltersContainer,
)
from api.products.geocoder import Geocoder
from api.products.models import Location, Product, MapboxLocation
from api.products.paginators import StandardResultsSetPagination
from api.products.serializers import ProductSerializer, LocationSerializer


class LocationSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    http_method_names = ("get",)
    serializer_class = LocationSerializer
    search_parameters = [
        openapi.Parameter(
            "text",
            in_=openapi.IN_QUERY,
            description="Search text for a location name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ]
    geocoder_response = []

    def get_queryset(self):
        text = self.request.query_params.get("text")
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
    filter_backends = FiltersContainer(
        IncludeLocationIdFilter,
        ExactLocationIdFilter,
        JobFunctionsTitleFilter,
        OrderByCardinalityFilter,
    )
    queryset = Product.objects.all()

    @swagger_auto_schema(manual_parameters=filter_backends.get_schema_parameters())
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)
