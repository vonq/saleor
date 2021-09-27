import itertools
from collections import defaultdict
from json import JSONDecodeError
from typing import Iterable, List, Tuple, Type, Dict, Optional

from algoliasearch.exceptions import RequestException
from algoliasearch_django import algolia_engine
from django.contrib.auth import get_user_model
from django.db.models import Case, Q, When, QuerySet
from django.http import JsonResponse, HttpResponse
from django.views import View
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.utils import json

from api.products.apps import ProductsConfig
from api.products.delivery_time import calculate_delivery_time
from api.products.docs import CommonOpenApiParameters
from api.products.geocoder import Geocoder
from api.products.models import (
    Channel,
    Industry,
    JobFunction,
    JobTitle,
    Location,
    Product,
    Profile,
    Category,
)
from api.products.paginators import (
    AutocompleteResultsSetPagination,
    SearchResultsPagination,
    StandardResultsSetPagination,
)
from api.products.search.docs import ProductsOpenApiParameters
from api.products.search.filter_collection import FacetFilterCollection
from api.products.search.filters.facet_filters import (
    AddonsOnlyFacetFilter,
    ChannelTypeFilter,
    CustomerIdFilter,
    DurationLessThanFacetFilter,
    DurationMoreThanFacetFilter,
    ExactLocationIdFacetFilter,
    FacetFilter,
    IsActiveFacetFilter,
    IsAvailableInJmpFacetFilter,
    IsNotMyOwnProductFilter,
    ProductsOnlyFacetFilter,
    StatusFacetFilter,
    IndustryFacetFilter,
    PriceMoreThanFacetFilter,
    PriceLessThanFacetFilter,
    DiversityFacetFilter,
    EmploymentTypeFacetFilter,
    SeniorityLevelFacetFilter,
    convert_facet_payload,
)
from api.products.search.filters.facet_filters_groups import (
    FacetFiltersGroup,
    GenericAndInternationalGroup,
    GenericAndLocationGroup,
    IndustryAndInternationalGroup,
    IndustryAndLocationGroup,
    InternationalAndFunctionGroup,
    JobFunctionAndLocationGroup,
    JobFunctionIndustryAndLocationGroup,
    JobFunctionGroup,
)
from api.products.search.search import (
    get_results_ids,
    query_search_index,
    query_parser_index,
)
from api.products.serializers import (
    ChannelSerializer,
    IndustrySerializer,
    JobFunctionTreeSerializer,
    LimitedJobFunctionSerializer,
    JobTitleSerializer,
    LocationSerializer,
    ProductJmpSerializer,
    ProductSearchSerializer,
    ProductSerializer,
    JobFunctionSerializer,
    InternalUserSerializer,
    CategorySerializer,
    TotalDeliveryTimeSerializer,
)

MY_OWN_PRODUCTS = (
    Q(salesforce_product_category=Product.SalesforceProductCategory.CUSTOMER_SPECIFIC)
    | Q(salesforce_product_solution=Product.SalesforceProductSolution.MY_OWN_CHANNEL)
    | Q(customer_id__isnull=False)
)

User = get_user_model()


class IsMapiOrJmpUser(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, "profile"):
            return False
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.profile.type in [Profile.Type.JMP, Profile.Type.MAPI],
        )


class UserStrategy:
    def __init__(self, request_user: User):
        self._request_user = request_user

    def is_mapi(self) -> bool:
        return (
            self._request_user.is_authenticated
            and self._request_user.profile.type == Profile.Type.MAPI
        )

    def is_jmp(self) -> bool:
        return not self._request_user.is_authenticated or (
            self._request_user.profile.type == Profile.Type.JMP
        )

    def is_internal(self) -> bool:
        return (
            self._request_user.is_authenticated
            and self._request_user.profile.type == Profile.Type.INTERNAL
        )


class IndexView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(
            """
        A name indicates what we seek.
        An address indicates where it is.
        A route indicates how we get there.
        """,
            content_type="text/plain",
        )


class DeliveryTimeViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()

    @swagger_auto_schema(
        operation_id="Retrieve time to process and setup for a list of products.",
        operation_summary="This endpoint calculates total number of days to process and setup a campaign containing a list of Products, given a comma-separated list of their ids.",
        operation_description="To be used to display this information in the campaign basket and on the Operation Team's SLA performance dashboard.",
        tags=[ProductsConfig.verbose_name],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="(?P<product_ids>.+)",
    )
    def totaldeliverytime(self, request, product_ids=None):
        product_ids = product_ids.split(",")
        if len(product_ids) > 50:
            return JsonResponse(
                data={
                    "error": "Cannot calculate delivery time for more than 50 products at a time"
                },
                status=HTTP_400_BAD_REQUEST,
            )
        products = list(self.get_queryset().filter(product_id__in=product_ids))

        if len(products) < len(product_ids):
            raise NotFound
        return Response(
            TotalDeliveryTimeSerializer(calculate_delivery_time(products)).data
        )


class LocationSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Location.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ("get",)
    serializer_class = LocationSerializer
    search_parameters = (
        CommonOpenApiParameters.ACCEPT_LANGUAGE,
        openapi.Parameter(
            "text",
            in_=openapi.IN_QUERY,
            description="Search text for a location name in either English, Dutch, German, French and Italian. Partial recognition of 20 other languages.",
            type=openapi.TYPE_STRING,
            required=True,
            example="Amst",
        ),
    )
    geocoder_response = []
    locations = []

    @swagger_auto_schema(
        operation_id="Locations",
        operation_summary="Search for any Location by a given text.",
        operation_description="""
                        This endpoint takes any text as input and returns a list of Locations matching the query, ordered by popularity.
                        Each response will include the entire world as a Location, even no Locations match the text query.
                        Use the <code>id</code> key of each object in the response to search for a Product.
                        Supports text input in English, Dutch and German.
                        """,
        manual_parameters=search_parameters,
        tags=[ProductsConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="In case of a successful request.",
                examples={
                    "application/json": [
                        {
                            "id": 3088,
                            "fully_qualified_place_name": "Amsterdam, North Holland, Netherlands",
                            "canonical_name": "Amsterdam",
                            "place_type": ["place"],
                            "within": None,
                        },
                        {
                            "id": 3081,
                            "fully_qualified_place_name": "Schiphol, North Holland, Netherlands",
                            "canonical_name": "Schiphol",
                            "place_type": ["place"],
                            "within": None,
                        },
                        {
                            "id": 3094,
                            "fully_qualified_place_name": "International",
                            "canonical_name": "The entire world",
                            "place_type": ["global"],
                            "within": None,
                        },
                    ]
                },
            )
        },
    )
    def list(self, request, *args, **kwargs):
        text = self.request.query_params.get("text")
        if not text:
            return Response(
                data={"text": ["This field is required"]}, status=HTTP_400_BAD_REQUEST
            )

        accept_language = self.request.LANGUAGE_CODE

        # first attempt to match on continents
        continents = Geocoder.get_continents(text)
        geocoder_response = Geocoder.geocode(text, primary_language=accept_language)
        locations = Location.from_mapbox_autocomplete_response(geocoder_response)

        serializer = self.get_serializer(
            itertools.chain(continents, locations), many=True
        )
        return Response(serializer.data)


class CategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    @swagger_auto_schema(
        operation_id="Categories",
        operation_summary="List available categories.",
        operation_description="""
                           Returns a list of categories available for filtering
                           """,
        tags=[ProductsConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="In case of a successful request.",
                examples={
                    "application/json": {
                        "career level": [
                            {"name": "Senior level", "type": "career level", "id": 1},
                            {
                                "name": "Graduates and Trainees",
                                "type": "career level",
                                "id": 2,
                            },
                        ],
                        "job type": [
                            {"name": "Remote only", "type": "job type", "id": 3},
                            {"name": "Part time", "type": "job type", "id": 4},
                        ],
                        "diversity": [
                            {"name": "LGBTQ+", "type": "diversity", "id": 7},
                            {"name": "Disabled", "type": "diversity", "id": 8},
                        ],
                    }
                },
            )
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        grouped_categories = defaultdict(list)
        for category in serializer.data:
            grouped_categories[category["type"] or "other"].append(category)
        return Response(grouped_categories)


class ProductsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializers = {
        "default": None,
    }
    http_method_names = ("get", "post")
    queryset = Product.objects.all().prefetch_related(
        "locations",
        "industries",
        "job_functions",
        "categories",
        "posting_requirements",
        "channel",
    )
    lookup_field = "product_id"
    recommendation_search_limit = (
        500  # Number of products to be retrieved on a recommendation query
    )

    search_results_count: int = None

    search_serializer: Optional[ProductSearchSerializer] = None

    search_filters: Tuple[Type[FacetFilter]] = (
        IsActiveFacetFilter,
        StatusFacetFilter,
        ProductsOnlyFacetFilter,
        ChannelTypeFilter,
        ExactLocationIdFacetFilter,
        DurationMoreThanFacetFilter,
        DurationLessThanFacetFilter,
        DiversityFacetFilter,
        EmploymentTypeFacetFilter,
        SeniorityLevelFacetFilter,
        PriceMoreThanFacetFilter,
        PriceLessThanFacetFilter,
    )
    search_group_filters: Tuple[Type[FacetFiltersGroup]] = (
        JobFunctionIndustryAndLocationGroup,
        JobFunctionAndLocationGroup,
        GenericAndLocationGroup,
        InternationalAndFunctionGroup,
        JobFunctionGroup,
        IndustryAndLocationGroup,
        IndustryAndInternationalGroup,
        GenericAndInternationalGroup,
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

    def get_serializer_class(self):
        user = UserStrategy(self.request.user)
        if self.request.user.is_authenticated:
            if user.is_jmp():
                return ProductJmpSerializer
            if user.is_mapi():
                return ProductSerializer
            if user.is_internal():
                return InternalUserSerializer
        # A non-authenticated user is assumed to be JMP
        # See https://qandidate.atlassian.net/browse/CHEC-804 and linked
        # for the rationale behind this
        return ProductJmpSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(
            status=Product.Status.ACTIVE,
            salesforce_product_type__in=Product.SalesforceProductType.products(),
        )

        user = UserStrategy(self.request.user)

        if user.is_jmp() or user.is_mapi():
            queryset = queryset.filter(available_in_jmp=True)

        if user.is_mapi():
            # MAPI (or HAPI) is only required to show Job Boards, Social or Google products
            queryset = queryset.filter(
                Q(salesforce_product_type=Product.SalesforceProductType.JOB_BOARD)
                | Q(salesforce_product_type=Product.SalesforceProductType.SOCIAL)
                | Q(salesforce_product_type=Product.SalesforceProductType.GOOGLE)
            )

        return queryset.order_by("-order_frequency", "id")

    def get_all_filters(self):
        user = UserStrategy(self.request.user)
        if user.is_mapi():
            return self.search_filters + (
                IsAvailableInJmpFacetFilter,
                IsNotMyOwnProductFilter,
            )
        elif user.is_jmp():
            if self.search_serializer.is_my_own_product_request:
                return self.search_filters + (
                    IsAvailableInJmpFacetFilter,
                    CustomerIdFilter,
                )
            else:
                return self.search_filters + (
                    IsAvailableInJmpFacetFilter,
                    IsNotMyOwnProductFilter,
                )
        return self.search_filters

    def get_all_group_filters(self):
        return self.search_group_filters

    @staticmethod
    def add_recommendation_filter(queryset):
        def is_not_free_except_for_my_own_products():
            return Q(purchase_price__gt=0) | ~Q(
                salesforce_product_category=Product.SalesforceProductCategory.GENERIC
            )

        def is_generic():
            return Q(job_functions=None, industries=None) | Q(
                # Generic industry
                industries__in=[29]
            )

        def is_not_social():
            return ~Q(channel__type=Channel.Type.SOCIAL_MEDIA)

        queryset = queryset.exclude(MY_OWN_PRODUCTS).filter(
            is_not_free_except_for_my_own_products()
        )
        generic_filter = queryset.filter(is_generic()).filter(is_not_social())[:2]
        niche_filter = queryset.filter(is_not_social()).exclude(is_generic())[:2]
        social_filter = queryset.exclude(is_not_social()).order_by("-order_frequency")[
            :2
        ]

        return niche_filter.union(
            generic_filter,
            social_filter,
        )

    def search_queryset(self, queryset) -> Tuple[QuerySet, Dict[str, int]]:
        """
        Operates on a subset of the dabase
        after we selected the products available
        to the requesting user's class in get_queryset
        """
        if self.search_serializer.is_recommendation:
            limit = self.recommendation_search_limit
            offset = 0
        else:
            limit = SearchResultsPagination().get_limit(self.request)
            offset = SearchResultsPagination().get_offset(self.request)

        filter_collection = FacetFilterCollection.build_filter_collection_from_request(
            request=self.request,
            filters=self.get_all_filters(),
            group_filters=self.get_all_group_filters(),
            limit=limit,
            offset=offset,
        )
        product_name = self.request.query_params.get(
            ProductsOpenApiParameters.PRODUCT_NAME.name, ""
        )

        if self.search_serializer.data["sortBy"] != "relevant":
            # use a replica index for non-default ranking requests
            adapter = algolia_engine.get_adapter(Product)

            sort_index = self.search_serializer.data["sortBy"]

            # MAPI offers a "recent" sorting option rather
            # than the aptly named "created.desc"
            if sort_index == "recent":
                sort_index = "created.desc"
            self.search_results_count, results, facets = adapter.raw_search_sorted(
                sort_index=sort_index,
                query=product_name,
                params=filter_collection.query(),
            )
        else:
            # use the default index for relevant-only ranking (default behaviour)
            self.search_results_count, results, facets = query_search_index(
                Product, params=filter_collection.query(), query=product_name
            )
        ids = get_results_ids(results)

        queryset = queryset.filter(pk__in=ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        )

        recommendation_queryset = self.add_recommendation_filter(queryset)
        if self.search_serializer.is_recommendation:
            self.search_results_count = recommendation_queryset.count()
            return recommendation_queryset, facets

        if self.search_serializer.excludes_recommendations:
            exclude_ids = recommendation_queryset.values_list("pk", flat=True)
            self.search_results_count -= len(exclude_ids)
            queryset = queryset.exclude(pk__in=exclude_ids)

        return queryset, facets

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(status=Product.Status.ACTIVE)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if UserStrategy(request.user).is_jmp() and not obj.available_in_jmp:
            raise NotFound()

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def validate(self, request, **kwargs):
        """
        A simple endpoint to quickly check whether a list of product ids is valid
        and available for MAPI to further process.

        This replaces a database check against portfolio service.
        """
        try:
            validating_product_ids = json.loads(request.body)  # type: List[int]
        except JSONDecodeError:
            return JsonResponse(
                data={"error": "Invalid request body"}, status=HTTP_400_BAD_REQUEST
            )
        all_products_valid = self.get_queryset().filter(
            product_id__in=validating_product_ids
        ).count() == len(validating_product_ids)
        if all_products_valid:
            return JsonResponse(
                data={"status": "Valid product ids"}, status=HTTP_200_OK
            )
        return JsonResponse(
            data={"status": "Invalid product ids"}, status=HTTP_404_NOT_FOUND
        )

    @swagger_auto_schema(
        operation_id="Retrieve multiple Product details",
        operation_summary="This endpoint retrieves a list of Products, given a comma-separated list of their ids.",
        operation_description="Sometimes you already have access to the Identification code of any particular Product and you want to retrieve the most up-to-date information about it.",
        manual_parameters=(CommonOpenApiParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="multiple/(?P<product_ids>.+)",
    )
    def multiple(self, request, product_ids=None):
        if not product_ids:
            raise NotFound

        product_ids = product_ids.split(",")
        if len(product_ids) > 50:
            return JsonResponse(
                data={"error": "Cannot fetch more than 50 products at a time"},
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.get_queryset().filter(product_id__in=product_ids)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of Products with the options to search by Location, Job Title, Job Function and Industry. as it is configured for every Partner individually.
        Products are ranked by their relevancy to the search terms.
        Optionally, products can filtered by Location.
        Values for each parameter can be fetched by calling the other endpoints in this section.
        Calling this endpoint will guarantee that the Products you see are configured for you as our Partner.
        """,
        operation_id="Products Search",
        operation_summary="Search and filter for products by various criteria.",
        manual_parameters=[item.parameter for item in search_filters if item.parameter]
        + [
            CommonOpenApiParameters.ACCEPT_LANGUAGE,
            ProductsOpenApiParameters.PRODUCT_NAME,
            ProductsOpenApiParameters.ONLY_RECOMMENDED,
            ProductsOpenApiParameters.EXCLUDE_RECOMMENDED,
            CommonOpenApiParameters.CURRENCY,
            ProductsOpenApiParameters.SORT_BY,
            IndustryFacetFilter.parameter,
        ],
        tags=[ProductsConfig.verbose_name],
        responses={
            400: openapi.Response(description="In case of a bad request."),
            200: openapi.Response(
                schema=ProductJmpSerializer(many=True),
                description="In case of a successful search.",
                examples={
                    "application/json": {
                        "count": 286,
                        "next": "http://host/products/?includeLocationId=2384&limit=1&offset=1",
                        "previous": None,
                        "results": [
                            {
                                "title": "Job board name - Premium Job",
                                "locations": [
                                    {
                                        "id": 2378,
                                        "fully_qualified_place_name": "United Kingdom",
                                        "canonical_name": "United Kingdom",
                                        "place_type": ["country"],
                                        "within": {
                                            "id": 2483,
                                            "fully_qualified_place_name": "Europe",
                                            "canonical_name": "Europe",
                                            "place_type": ["continent"],
                                            "within": None,
                                        },
                                    },
                                ],
                                "job_functions": {"id": 36, "name": "Tax", "parent": 9},
                                "industries": [],
                                "description": "Description",
                                "homepage": "https://www.example.com",
                                "logo_url": [
                                    {
                                        "url": "https://example.com/logo.png",
                                    }
                                ],
                                "duration": {"range": "days", "period": None},
                                "time_to_process": {"range": "hours", "period": None},
                                "time_to_setup": {"range": "hours", "period": None},
                                "product_id": "ab379c3b-600d-5592-9f9d-3c4805086364",
                                "vonq_price": [{"amount": 123, "currency": "EUR"}],
                                "ratecard_price": [{"amount": 234, "currency": "EUR"}],
                                "type": None,
                                "cross_postings": [],
                                "channel": {
                                    "name": "Channel Name",
                                    "url": "https://www.channel.jobs/",
                                    "type": "job board",
                                    "id": 12,
                                },
                            }
                        ],
                    }
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        search_serializer = ProductSearchSerializer(data=self.request.query_params)
        search_serializer.is_valid(raise_exception=True)
        self.search_serializer = search_serializer

        queryset = self.get_queryset()
        facets = {}  # a standard list catalogue view can't return facets

        if search_serializer.is_search_request:
            # a pure list view doesn't need to hit the search index
            try:
                queryset, facets = self.search_queryset(queryset)
            except RequestException:
                return JsonResponse(
                    data={"error": "Invalid request"}, status=HTTP_400_BAD_REQUEST
                )
        else:
            user = UserStrategy(self.request.user)
            if user.is_jmp() or user.is_mapi():
                if not self.search_serializer.is_recommendation:
                    queryset = queryset.exclude(MY_OWN_PRODUCTS)
                else:
                    queryset = self.add_recommendation_filter(queryset)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data, facets)

    def get_paginated_response(self, data, facets=None):
        response = super().get_paginated_response(data)
        if facets:
            facets = convert_facet_payload(facets)
        response.data["facets"] = facets
        return response

    @swagger_auto_schema(
        operation_id="Retrieve Product details",
        operation_summary="This endpoint retrieves a Product by its id.",
        operation_description="Sometimes you already have access to the Identification code of any particular Product and you want to retrieve the most up-to-date information about it.",
        manual_parameters=(CommonOpenApiParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class AddonsViewSet(ProductsViewSet):
    search_filters: Tuple[Type[FacetFilter]] = (
        IsActiveFacetFilter,
        StatusFacetFilter,
        AddonsOnlyFacetFilter,
        DurationMoreThanFacetFilter,
        DurationLessThanFacetFilter,
    )
    http_method_names = ("get",)

    def get_queryset(self):
        active_products = self.queryset.filter(
            status=Product.Status.ACTIVE,
            salesforce_product_type__in=Product.SalesforceProductType.addons(),
        )
        user = UserStrategy(self.request.user)
        if user.is_mapi() or user.is_jmp():
            return active_products.filter(available_in_jmp=True).exclude(
                MY_OWN_PRODUCTS
            )
        return active_products

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of Products with the options to search by Location, Job Title, Job Function and Industry. as it is configured for every Partner individually.
        Products are ranked by their relevancy to the search terms.
        Optionally, products can filtered by Location.
        Values for each parameter can be fetched by calling the other endpoints in this section.
        Calling this endpoint will guarantee that the Products you see are configured for you as our Partner.
        """,
        operation_id="Addons Search",
        operation_summary="Search and filter for addons by various criteria.",
        manual_parameters=[item.parameter for item in search_filters if item.parameter]
        + [
            CommonOpenApiParameters.ACCEPT_LANGUAGE,
            ProductsOpenApiParameters.PRODUCT_NAME,
            ProductsOpenApiParameters.ONLY_RECOMMENDED,
            ProductsOpenApiParameters.EXCLUDE_RECOMMENDED,
            CommonOpenApiParameters.CURRENCY,
            ProductsOpenApiParameters.SORT_BY,
        ],
        tags=[ProductsConfig.verbose_name],
        responses={
            400: openapi.Response(description="In case of a bad request."),
            200: openapi.Response(
                schema=ProductJmpSerializer(many=True),
                description="In case of a successful search.",
                examples={
                    "application/json": {
                        "count": 286,
                        "next": "http://host/products/?includeLocationId=2384&limit=1&offset=1",
                        "previous": None,
                        "results": [
                            {
                                "title": "Job board name - Premium Job",
                                "locations": [
                                    {
                                        "id": 2378,
                                        "fully_qualified_place_name": "United Kingdom",
                                        "canonical_name": "United Kingdom",
                                        "place_type": ["country"],
                                        "within": {
                                            "id": 2483,
                                            "fully_qualified_place_name": "Europe",
                                            "canonical_name": "Europe",
                                            "place_type": ["continent"],
                                            "within": None,
                                        },
                                    },
                                ],
                                "job_functions": {"id": 36, "name": "Tax", "parent": 9},
                                "industries": [],
                                "description": "Description",
                                "homepage": "https://www.example.com",
                                "logo_url": [
                                    {
                                        "url": "https://example.com/logo.png",
                                    }
                                ],
                                "duration": {"range": "days", "period": None},
                                "time_to_process": {"range": "hours", "period": None},
                                "time_to_setup": {"range": "hours", "period": None},
                                "product_id": "ab379c3b-600d-5592-9f9d-3c4805086364",
                                "vonq_price": [{"amount": 123, "currency": "EUR"}],
                                "ratecard_price": [{"amount": 234, "currency": "EUR"}],
                                "type": None,
                                "cross_postings": [],
                                "channel": {
                                    "name": "Channel Name",
                                    "url": "https://www.channel.jobs/",
                                    "type": "job board",
                                    "id": 12,
                                },
                            }
                        ],
                    }
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="Retrieve Addon details",
        operation_summary="This endpoint retrieves an Addon by its id.",
        operation_description="Sometimes you already have access to the Identification code of any particular Addon and you want to retrieve the most up-to-date information about it.",
        manual_parameters=(CommonOpenApiParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="Retrieve multiple Addons details",
        operation_summary="This endpoint retrieves a list of Addons, given a comma-separated list of their ids.",
        operation_description="Sometimes you already have access to the Identification code of any particular Addon and you want to retrieve the most up-to-date information about it.",
        manual_parameters=(CommonOpenApiParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="multiple/(?P<product_ids>.+)",
    )
    def multiple(self, request, product_ids=None):
        return super().multiple(request, product_ids)


class JobTitleSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = JobTitle.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ("get",)
    serializer_class = JobTitleSerializer
    pagination_class = AutocompleteResultsSetPagination
    search_parameters = [
        CommonOpenApiParameters.ACCEPT_LANGUAGE,
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
        _, results, _ = query_search_index(
            JobTitle,
            query=text,
            params={
                "getRankingInfo": True,
                "analytics": True,
                "enableABTest": False,
                "hitsPerPage": 10,
                "attributesToRetrieve": "id",
                "attributesToSnippet": "*:20",
                "snippetEllipsisText": "…",
                "responseFields": "*",
                "explain": "*",
                "page": 0,
                "maxValuesPerFacet": 5,
                "facets": ["*"],
            },
        )
        ids = get_results_ids(results)

        return self.queryset.filter(pk__in=ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        )

    @swagger_auto_schema(
        operation_description="""
                    This endpoint takes any text as input and returns a list of supported Job Titles matching the query, ordered by popularity.
                    Use the <code>id</code> key of each object in the response to search for a Product.
                    Supports text input in English, Dutch and German.
                    """,
        operation_id="Job Titles",
        operation_summary="Search for a job title.",
        tags=[ProductsConfig.verbose_name],
        manual_parameters=search_parameters,
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="In case of a successful request.",
                examples={
                    "application/json": {
                        "count": 787,
                        "next": "http://host/job-titles/?limit=10&offset=10&text=ent",
                        "previous": None,
                        "results": [
                            {"id": 1, "name": "Recruitment Consultant"},
                            {"id": 3, "name": "Customer Assistant"},
                            {"id": 4, "name": "Business Development Manager"},
                        ],
                    }
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class JobFunctionsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [AllowAny]
    serializer_class = JobFunctionTreeSerializer
    flat_serializer_class = JobFunctionSerializer
    http_method_names = ("get",)
    queryset = JobFunction.objects.all()

    @staticmethod
    def job_functions_tree_builder(queryset: Iterable[JobFunction]) -> List[dict]:
        def get_nested_children_functions(inner_item: JobFunction):
            inner = {"id": inner_item.id, "name": inner_item.name, "children": []}
            if parent_functions_lookup_table[inner_item.id]:
                for nested_item in parent_functions_lookup_table[inner_item.id]:
                    inner_children = get_nested_children_functions(nested_item)
                    inner["children"].append(inner_children)
            return inner

        parent_functions_lookup_table = defaultdict(list)
        for function in queryset:
            if not function.parent:
                parent_functions_lookup_table[None].append(function)
                continue
            parent_functions_lookup_table[function.parent.id].append(function)

        tree_structure = []
        for root_function in parent_functions_lookup_table[None]:
            children_functions = get_nested_children_functions(root_function)
            tree_structure.append(children_functions)

        return tree_structure

    @swagger_auto_schema(
        operation_description="""
                    This endpoint returns a tree-like structure of supported Job Functions that can be used to search for Products.
                    Use the <code>id</code> key of any Job Function in the response to search for a Product.
                    """,
        operation_id="Job Functions",
        operation_summary="Search for a Job Function.",
        tags=[ProductsConfig.verbose_name],
        manual_parameters=[
            CommonOpenApiParameters.ACCEPT_LANGUAGE,
            openapi.Parameter(
                "text",
                in_=openapi.IN_QUERY,
                description="Search for function based on job title headline",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="In case of a successful request.",
                examples={
                    "application/json": [
                        {
                            "id": 8,
                            "name": "Education",
                            "children": [{"id": 5, "name": "Teaching", "children": []}],
                        }
                    ]
                },
            )
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not self.request.query_params.get("text"):
            job_functions_tree = self.job_functions_tree_builder(queryset)
            serializer = self.serializer_class(job_functions_tree, many=True)

        else:
            _, results, _ = query_search_index(
                JobFunction,
                query=self.request.query_params.get("text"),
                params={
                    "analytics": True,
                    "attributesToRetrieve": "id",
                    "hitsPerPage": 3,
                },
            )
            ids = get_results_ids(results)

            queryset = self.queryset.filter(pk__in=ids).order_by(
                Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
            )
            serializer = self.flat_serializer_class(queryset, many=True)

        return Response(serializer.data)


class FunctionFromTitleViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LimitedJobFunctionSerializer
    permission_classes = [AllowAny]
    search_parameters = [
        CommonOpenApiParameters.ACCEPT_LANGUAGE,
        openapi.Parameter(
            "headline",
            in_=openapi.IN_QUERY,
            description="Search for function based on job title headline",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ]
    http_method_names = ("get",)

    @swagger_auto_schema(
        operation_description="""
                   This endpoint takes a job title headline and returns a list of job functions, ordered by relevancy.
                    """,
        operation_id="Parse job titles",
        operation_summary="Parse job title and map to job function",
        tags=["Title Parser"],
        manual_parameters=[CommonOpenApiParameters.ACCEPT_LANGUAGE],
    )
    def list(self, request, *args, **kwargs):
        headline = self.request.query_params.get("text")

        self.search_results_count, results = query_parser_index(title=headline)
        ids = get_results_ids(results)

        queryset = self.queryset.filter(pk__in=ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        )

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class IndustriesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [AllowAny]
    serializer_class = IndustrySerializer
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

    @swagger_auto_schema(
        operation_description="""
                This endpoint returns a list of supported industry names that can be used to search for products. Results are ordered alphabetically.
                Use the <code>id</code> key of any Industry in the response to search for a product.
                """,
        operation_id="Industry names",
        operation_summary="List all industry names.",
        tags=[ProductsConfig.verbose_name],
        manual_parameters=[CommonOpenApiParameters.ACCEPT_LANGUAGE],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="In case of a successful request.",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {"id": 20, "name": "Accounting"},
                            {"id": 10, "name": "Advertising"},
                        ],
                    }
                },
            )
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ChannelsViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    http_method_names = ("get",)
    pagination_class = StandardResultsSetPagination
    queryset = Channel.objects.filter(is_active=True)
    serializer_class = ChannelSerializer

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of channels with products associated.
        """,
        operation_id="Channels list",
        manual_parameters=[CommonOpenApiParameters.ACCEPT_LANGUAGE],
        tags=[ProductsConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="Paginated list of channels",
                examples={
                    "application/json": {
                        "count": 1664,
                        "next": "http://host/channels/?limit=25&offset=25",
                        "previous": None,
                        "results": [
                            {
                                "id": 139,
                                "name": "Channel Name",
                                "url": "https://channel.com/",
                                "products": [
                                    {
                                        "locations": [],
                                        "job_functions": [],
                                        "industries": [],
                                        "duration": {"range": "days", "period": None},
                                        "time_to_process": {
                                            "range": "hours",
                                            "period": None,
                                        },
                                        "vonq_price": [
                                            {"amount": None, "currency": "EUR"}
                                        ],
                                        "ratecard_price": [
                                            {"amount": None, "currency": "EUR"}
                                        ],
                                        "cross_postings": [],
                                        "homepage": "http://www.product.com/product/",
                                        "type": "Finance",
                                        "logo_url": [{"url": None}],
                                        "title": "Product Name",
                                        "channel": {
                                            "name": "Channel Name",
                                            "url": "http://www.channel.com/",
                                            "type": "job board",
                                            "id": 1854,
                                        },
                                    }
                                ],
                                "type": "job board",
                            },
                        ],
                    }
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="Retrieve Channel details",
        operation_summary="This endpoint retrieves a Channel by its id.",
        manual_parameters=(CommonOpenApiParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
