import itertools

from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from api.products.filters import (
    ExactLocationIdFilter,
    IncludeLocationIdFilter,
    OrderByCardinalityFilter,
    JobFunctionsTitleFilter,
    FiltersContainer,
    IndustryFilter,
    OrderByLocationTrafficShare,
)
from api.products.geocoder import Geocoder
from api.products.models import Location, Product, MapboxLocation, JobTitle, JobFunction, Industry
from api.products.paginators import StandardResultsSetPagination, AutocompleteResultsSetPagination
from api.products.serializers import ProductSerializer, LocationSerializer, JobTitleSerializer, JobFunctionSerializer, IndustrySerializer


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

        # first attempt to match on continents
        continents = Geocoder.get_continents(text)

        self.geocoder_response = Geocoder.geocode(text)
        locations = Location.from_mapbox_response(self.geocoder_response)

        return list(itertools.chain(continents, locations))

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
        IndustryFilter,
        OrderByCardinalityFilter,
        OrderByLocationTrafficShare,
    )
    queryset = Product.objects.all()

    @swagger_auto_schema(manual_parameters=filter_backends.get_schema_parameters())
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTitleSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    http_method_names = ("get",)
    serializer_class = JobTitleSerializer
    pagination_class = AutocompleteResultsSetPagination
    search_parameters = [
        openapi.Parameter(
            "Accept-Language",
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            format="language tag",
            required=False,
        ),
        openapi.Parameter(
            "text",
            in_=openapi.IN_QUERY,
            description="Search text for a job title name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ]

    def get_queryset(self):
        text = self.request.query_params.get("text")
        if not text:
            return []
        return JobTitle.objects.filter_across_languages(name__icontains=text).order_by("-frequency")

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class JobFunctionsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = JobFunctionSerializer
    pagination_class = StandardResultsSetPagination
    http_method_names = ("get",)
    queryset = JobFunction.objects.all()

    search_parameters = [
        openapi.Parameter(
            "Accept-Language",
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            format="language tag",
            required=False,
        ),
    ]

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class IndustriesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = IndustrySerializer
    pagination_class = StandardResultsSetPagination
    http_method_names = ("get",)

    search_parameters = [
        openapi.Parameter(
            "Accept-Language",
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            format="language tag",
            required=False,
        ),
    ]

    def get_queryset(self):
        return Industry.objects.all()

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
