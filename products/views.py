import itertools
from collections import defaultdict
from json import JSONDecodeError
from typing import List, Iterable, Type, Tuple

from django.db.models import Case, When
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.utils import json

from api.products.apps import ProductsConfig
from api.products.docs import CommonParameters
from api.products.search.filters import (
    FacetFilter,
    InclusiveJobFunctionChildrenFilter,
    InclusiveLocationIdFacetFilter,
    FacetFilterCollection,
    ExactLocationIdFacetFilter,
    IsGenericFacetFilter,
    IsInternationalFacetFilter,
    JobFunctionsFacetFilter,
    JobTitlesFacetFilter,
    DescendentJobTitlesFacetFilter,
    IndustryFacetFilter,
    PrimarySimilarWebFacetFilter,
    SecondarySimilarWebFacetFilter,
    IsActiveFacetFilter,
    StatusFacetFilter,
    IsAvailableInJmpFacetFilter,
    ProductsOnlyFacetFilter,
    AddonsOnlyFacetFilter,
    DurationMoreThanFacetFilter,
    DurationLessThanFacetFilter,
    ChannelTypeFilter,
    CustomerIdFilter,
    IsMyOwnProductFilter,
)
from api.products.geocoder import Geocoder
from api.products.models import (
    Location,
    Product,
    JobTitle,
    JobFunction,
    Industry,
    Profile,
    Channel,
)
from api.products.paginators import (
    StandardResultsSetPagination,
    AutocompleteResultsSetPagination,
    SearchResultsPagination,
)
from api.products.search.search import query_search_index, get_results_ids

from api.products.serializers import (
    ProductSerializer,
    LocationSerializer,
    JobTitleSerializer,
    JobFunctionTreeSerializer,
    IndustrySerializer,
    ProductSearchSerializer,
    ChannelSerializer,
)


class IsMapiOrJmpUser(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, "profile"):
            return False
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.profile.type in [Profile.Type.JMP, Profile.Type.MAPI],
        )


class LocationSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Location.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ("get",)
    serializer_class = LocationSerializer
    search_parameters = (
        CommonParameters.ACCEPT_LANGUAGE,
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

        # first attempt to match on continents
        continents = Geocoder.get_continents(text)

        geocoder_response = Geocoder.geocode(text)
        locations = Location.from_mapbox_autocomplete_response(geocoder_response)

        serializer = self.get_serializer(
            itertools.chain(continents, locations), many=True
        )
        return Response(serializer.data)


class ProductsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    http_method_names = ("get", "post")
    queryset = Product.objects.all().prefetch_related(
        "locations", "industries", "job_functions"
    )
    lookup_field = "product_id"
    recommendation_search_limit = (
        500  # Number of products to be retrieved on a recommendation query
    )

    search_results_count: int = None

    is_recommendation: bool = False
    is_my_own_product_request: bool = False

    search_filters: Tuple[Type[FacetFilter]] = (
        InclusiveLocationIdFacetFilter,
        ExactLocationIdFacetFilter,
        JobFunctionsFacetFilter,
        InclusiveJobFunctionChildrenFilter,
        JobTitlesFacetFilter,
        DescendentJobTitlesFacetFilter,
        IndustryFacetFilter,
        PrimarySimilarWebFacetFilter,
        SecondarySimilarWebFacetFilter,
        DurationMoreThanFacetFilter,
        DurationLessThanFacetFilter,
        IsActiveFacetFilter,
        # TODO: Re-enable them after we're done
        #       with the search relevancy re-haul
        # IsInternationalFacetFilter,
        # IsGenericFacetFilter,
        StatusFacetFilter,
        ProductsOnlyFacetFilter,
        ChannelTypeFilter,
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
        queryset = (
            self.queryset.filter(is_active=True)
            .filter(
                salesforce_product_type__in=Product.SalesforceProductType.products()
            )
            .exclude(status__in=[Product.Status.BLACKLISTED, Product.Status.DISABLED])
        )

        if self.request.user.profile.type in [Profile.Type.JMP, Profile.Type.MAPI]:
            queryset = queryset.filter(available_in_jmp=True).exclude(
                salesforce_product_category=Product.SalesforceProductCategory.CUSTOMER_SPECIFIC,
                salesforce_product_solution=Product.SalesforceProductSolution.MY_OWN_CHANNEL,
            )
            queryset = queryset.filter(available_in_jmp=True)

        if self.is_recommendation:
            queryset = self.add_recommendation_filter(queryset)

        return queryset.order_by("-order_frequency")

    def get_all_filters(self):
        if self.request.user.profile.type == Profile.Type.MAPI:
            return self.search_filters + (
                IsAvailableInJmpFacetFilter,
                IsMyOwnProductFilter,
            )
        elif self.request.user.profile.type == Profile.Type.JMP:
            if self.is_my_own_product_request:
                return self.search_filters + (
                    IsAvailableInJmpFacetFilter,
                    CustomerIdFilter,
                )
            else:
                return self.search_filters + (
                    IsAvailableInJmpFacetFilter,
                    IsMyOwnProductFilter,
                )
        return self.search_filters

    @staticmethod
    def add_recommendation_filter(queryset):
        is_generic = lambda: Q(job_functions=None, industries=None) | Q(
            # Generic industry
            industries__in=[29]
        )
        jobboard_generic_filter = queryset.filter(
            channel__type=Channel.Type.JOB_BOARD
        ).filter(is_generic())[:1]
        jobboard_niche_filter = queryset.filter(
            channel__type=Channel.Type.JOB_BOARD
        ).exclude(is_generic())[:1]
        publication_filter = queryset.filter(channel__type=Channel.Type.PUBLICATION)[:2]
        community_filter = queryset.filter(channel__type=Channel.Type.COMMUNITY)[:2]
        social_filter = queryset.filter(channel__type=Channel.Type.SOCIAL_MEDIA)[:2]
        return publication_filter.union(
            jobboard_generic_filter,
            jobboard_niche_filter,
            community_filter,
            social_filter,
        )

    def search_queryset(self, queryset):
        if self.is_recommendation:
            limit = self.recommendation_search_limit
            offset = 0
        else:
            limit = SearchResultsPagination().get_limit(self.request)
            offset = SearchResultsPagination().get_offset(self.request)
        filter_collection = FacetFilterCollection.build_filter_collection_from_request(
            request=self.request,
            filters=self.get_all_filters(),
            limit=limit,
            offset=offset,
        )
        product_name = self.request.query_params.get("name", "")

        self.search_results_count, results = query_search_index(
            Product, params=filter_collection.query(), query=product_name
        )
        ids = get_results_ids(results)

        queryset = self.queryset.filter(pk__in=ids).order_by(
            Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        )

        if self.is_recommendation:
            queryset = self.add_recommendation_filter(queryset)
            self.search_results_count = queryset.count()

        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(is_active=True).exclude(
            status__in=[Product.Status.BLACKLISTED, Product.Status.DISABLED]
        )

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.user.profile.type == Profile.Type.JMP and not obj.available_in_jmp:
            raise NotFound()

    @action(detail=False, methods=["post"], permission_classes=[IsMapiOrJmpUser])
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
        manual_parameters=(CommonParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="multiple/(?P<product_ids>(.+,?)+)",
    )
    def multiple(self, request, **kwargs):
        product_ids = kwargs.get("product_ids")
        if not product_ids:
            raise NotFound

        product_ids = product_ids.split(",")
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
            CommonParameters.ACCEPT_LANGUAGE,
            CommonParameters.PRODUCT_NAME,
            CommonParameters.CURRENCY,
        ],
        tags=[ProductsConfig.verbose_name],
        responses={
            400: openapi.Response(description="In case of a bad request."),
            200: openapi.Response(
                schema=serializer_class(many=True),
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
        self.is_recommendation = search_serializer.is_recommendation
        self.is_my_own_product_request = search_serializer.is_my_own_product_request

        queryset = self.get_queryset()
        if search_serializer.is_search_request:
            # a pure list view doesn't need to hit the search index
            queryset = self.search_queryset(queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_id="Retrieve Product details",
        operation_summary="This endpoint retrieves a Product by its id.",
        operation_description="Sometimes you already have access to the Identification code of any particular Product and you want to retrieve the most up-to-date information about it.",
        manual_parameters=(CommonParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class AddonsViewSet(ProductsViewSet):
    search_filters: Tuple[Type[FacetFilter]] = (
        InclusiveLocationIdFacetFilter,
        ExactLocationIdFacetFilter,
        JobFunctionsFacetFilter,
        JobTitlesFacetFilter,
        IndustryFacetFilter,
        PrimarySimilarWebFacetFilter,
        SecondarySimilarWebFacetFilter,
        IsActiveFacetFilter,
        StatusFacetFilter,
        AddonsOnlyFacetFilter,
    )
    http_method_names = ("get",)

    def get_queryset(self):
        active_products = (
            self.queryset.filter(is_active=True)
            .filter(salesforce_product_type__in=Product.SalesforceProductType.addons())
            .exclude(status__in=[Product.Status.BLACKLISTED, Product.Status.DISABLED])
        )
        if self.request.user.profile.type in [Profile.Type.JMP, Profile.Type.MAPI]:
            return active_products.filter(available_in_jmp=True)
        return active_products


class JobTitleSearchViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [IsAuthenticated]
    http_method_names = ("get",)
    serializer_class = JobTitleSerializer
    pagination_class = AutocompleteResultsSetPagination
    search_parameters = [
        CommonParameters.ACCEPT_LANGUAGE,
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
    permission_classes = [IsAuthenticated]
    serializer_class = JobFunctionTreeSerializer
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
        manual_parameters=[CommonParameters.ACCEPT_LANGUAGE],
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
        job_functions_tree = self.job_functions_tree_builder(queryset)
        serializer = self.serializer_class(job_functions_tree, many=True)
        return Response(serializer.data)


class IndustriesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [IsAuthenticated]
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
        manual_parameters=[CommonParameters.ACCEPT_LANGUAGE],
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
    permission_classes = [IsAuthenticated]
    http_method_names = ("get",)
    pagination_class = StandardResultsSetPagination
    queryset = Channel.objects.filter(is_active=True)
    serializer_class = ChannelSerializer

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of channels with products associated.
        """,
        operation_id="Channels list",
        manual_parameters=[CommonParameters.ACCEPT_LANGUAGE],
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
        manual_parameters=(CommonParameters.ACCEPT_LANGUAGE,),
        tags=[ProductsConfig.verbose_name],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
