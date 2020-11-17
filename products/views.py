import itertools
from typing import List

from django.db.models import Case, When
from django.db.models import Q
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from api.products.filters import (
    InclusiveLocationIdFacetFilter,
    FacetFilterCollection,
    ExactLocationIdFacetFilter,
    JobFunctionsFacetFilter,
    JobTitlesFacetFilter,
    IndustryFacetFilter,
    PrimarySimilarWebFacetFilter,
    SecondarySimilarWebFacetFilter,
)
from api.products.geocoder import Geocoder
from api.products.models import Location, Product, JobTitle, JobFunction, Industry
from api.products.paginators import (
    StandardResultsSetPagination,
    AutocompleteResultsSetPagination,
    SearchResultsPagination,
)
from api.products.search import query_search_index, get_results_ids
from api.products.serializers import (
    ProductSerializer,
    LocationSerializer,
    JobTitleSerializer,
    JobFunctionSerializer,
    IndustrySerializer,
    ProductSearchSerializer,
)


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
    locations = []

    def get_queryset(self):
        text = self.request.query_params.get("text")
        if not text:
            return []

        # first attempt to match on continents
        continents = Geocoder.get_continents(text)
        world = Location(
            mapbox_placename="The entire world",
            canonical_name="Global",
            mapbox_id="world",
            mapbox_context=[],
            mapbox_place_type=[],
        )

        # avoid hitting mapbox or the database again
        # when serializing a response
        if not self.geocoder_response:
            self.geocoder_response = Geocoder.geocode(text)
        if not self.locations:
            self.locations = Location.from_mapbox_response(self.geocoder_response)

        return list(itertools.chain(continents, self.locations, [world]))

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ProductsViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    http_method_names = ("get",)
    queryset = Product.objects.all()
    ids: List[int] = []
    lookup_field = "product_id"

    search_results_count: int = None

    search_filters = (
        InclusiveLocationIdFacetFilter,
        ExactLocationIdFacetFilter,
        JobFunctionsFacetFilter,
        JobTitlesFacetFilter,
        IndustryFacetFilter,
        PrimarySimilarWebFacetFilter,
        SecondarySimilarWebFacetFilter,
    )

    @property
    def paginator(self):
        if not hasattr(self, "_paginator"):
            self._paginator = (
                SearchResultsPagination()
                if self.search_results_count
                else StandardResultsSetPagination()
            )
        return self._paginator

    def get_queryset(self):
        filter_collection = FacetFilterCollection.build_filter_collection_from_request(
            request=self.request,
            filters=self.search_filters,
            limit=SearchResultsPagination().get_limit(self.request),
            offset=SearchResultsPagination().get_offset(self.request),
        )

        if not filter_collection:
            # a list request doesn't need
            # to go through algolia
            # before we can serialise it
            return self.queryset

        if not self.ids:
            self.search_results_count, results = query_search_index(
                Product, params=filter_collection.query()
            )
            self.ids = get_results_ids(results)

        return self.queryset.filter(pk__in=self.ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(self.ids)])
        )

    @swagger_auto_schema(
        manual_parameters=[item.parameter for item in search_filters if item.parameter]
    )
    def list(self, request, *args, **kwargs):
        ProductSearchSerializer(data=self.request.query_params).is_valid(
            raise_exception=True
        )
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
        # TODO ugly hack until filter_across_languages gets more sophisticated
        return JobTitle.objects.filter(
            Q(name_en__icontains=text)
            | Q(name_nl__icontains=text)
            | Q(name_de__icontains=text)
            | Q(alias_of__name_en__icontains=text)
            | Q(alias_of__name_nl__icontains=text)
            | Q(alias_of__name_de__icontains=text)
        ).order_by("-frequency")

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
        return Industry.objects.all().order_by("name")

    @swagger_auto_schema(manual_parameters=search_parameters)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
