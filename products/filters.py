import itertools
from typing import ClassVar, Iterable, Type

from drf_yasg2 import openapi
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from api.products.models import JobFunction, Location, Channel


class FacetFilter:
    operator: str = "OR"
    filter_name: str
    parameter_name: str
    filters: str = ""
    parameter: openapi.Parameter
    score: int

    def __init__(self, *values):
        self.filters = f" OR ".join(
            [f'{self.filter_name}:"{value}"<score={self.score}>' for value in values]
        )


def get_facet_filter(
    facet_filter_class: ClassVar, parameters: str
) -> Type[FacetFilter]:
    parameter_ids = parameters.split(",") if parameters else []
    return facet_filter_class(*parameter_ids)


class InclusiveLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_context_mapbox_ids"
    parameter_name = "includeLocationId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Id for a Location to search products against. If no exact matches exist, search will be expanded to the Location's region and country. Optionally, a (comma-separated) array of values can be passed. Passing multiple values increases the number of search results.",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_STRING),
        required=False,
        explode=False,
    )
    score = 9

    def __init__(self, *values):
        """
        Here we're passed a list of location ids, for which we want to
        retrieve their CONTEXT!
        """
        locations_and_contexts = Location.list_context_locations_ids(values) or values
        super().__init__(*locations_and_contexts)


class ExactLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_ids"
    parameter_name = "exactLocationId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products specifically assigned to a Location.",
        type=openapi.TYPE_STRING,
        required=False,
        explode=False,
    )
    score = 9


class PrimarySimilarWebFacetFilter(FacetFilter):
    filter_name = "primary_similarweb_location"
    parameter_name = "includeLocationId"
    parameter = None
    score = 9

    def __init__(self, *values):
        # filter out null country codes
        # (for locations that we haven't yet
        # fully annotated)
        country_codes = filter(
            None,
            Location.objects.filter(id__in=values).values_list(
                "country_code", flat=True
            ),
        )
        super().__init__(*country_codes)


class SecondarySimilarWebFacetFilter(PrimarySimilarWebFacetFilter):
    filter_name = "secondary_similarweb_location"
    parameter_name = "includeLocationId"
    parameter = None
    score = 7


class IsActiveFacetFilter(FacetFilter):
    filter_name = "is_active"
    parameter_name = "is_active"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = "is_active:true"


class IsAvailableInJmpFacetFilter(FacetFilter):
    filter_name = "available_in_jmp"
    parameter_name = "available_in_jmp"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = "available_in_jmp:true"


class StatusFacetFilter(FacetFilter):
    filter_name = "filterable_status"
    parameter_name = "status"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = 'filterable_status:"None" OR filterable_status:"Trial" OR filterable_status:"Negotiated"'


class ProductsOnlyFacetFilter(FacetFilter):
    filter_name = "is_product"
    parameter_name = "is_product"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = "is_product:true"


class DurationMoreThanFacetFilter(FacetFilter):
    filter_name = "duration_days"
    parameter_name = "durationFrom"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products with a duration more or equal than a certain number of days",
        type=openapi.TYPE_INTEGER,
        required=False,
        explode=False,
    )
    operator = "AND"

    def __init__(self, value=None):
        self.filters = f"duration_days>={value}" if value else ""


class DurationLessThanFacetFilter(FacetFilter):
    filter_name = "duration_days"
    parameter_name = "durationTo"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products with a duration up to a certain number of days",
        type=openapi.TYPE_INTEGER,
        required=False,
        explode=False,
    )
    operator = "AND"

    def __init__(self, value=None):
        self.filters = f"duration_days<={value}" if value else ""


class AddonsOnlyFacetFilter(FacetFilter):
    filter_name = "is_addon"
    parameter_name = "is_addon"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = "is_addon:true"


class JobFunctionsFacetFilter(FacetFilter):
    filter_name = "searchable_job_functions_ids"
    parameter_name = "jobFunctionId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Job Title id. Not to be used in conjunction with a Job Function id.",
        type=openapi.TYPE_STRING,
        required=False,
    )
    score = 10


class JobTitlesFacetFilter(FacetFilter):
    filter_name = "searchable_job_titles_ids"
    parameter_name = "jobTitleId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Job title id",
        type=openapi.TYPE_STRING,
        required=False,
    )
    score = 10

    def __init__(self, *values):
        if len(values) > 1:
            raise ValidationError(detail="Only one job title allowed per query")
        super().__init__(*values)


class DescendentJobTitlesFacetFilter(FacetFilter):
    filter_name = "searchable_job_functions_ids"
    parameter_name = "jobTitleId"
    parameter = None
    score = 4

    def __init__(self, *values):
        descendant_job_functions = (
            list(
                set(
                    itertools.chain.from_iterable(
                        job_function.get_descendants().values_list("pk", flat=True)
                        for job_function in JobFunction.objects.filter(
                            jobtitle__id__in=values
                        )
                    )
                )
            )
            or values
        )

        super().__init__(*descendant_job_functions)
        pass


class IndustryFacetFilter(FacetFilter):
    filter_name = "searchable_industries_ids"
    parameter_name = "industryId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Industry Id",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_STRING),
        required=False,
        explode=False,
    )
    score = 8


class InclusiveJobFunctionChildrenFilter(FacetFilter):
    filter_name = "searchable_job_functions_ids"
    parameter_name = "jobFunctionId"
    score = 10
    parameter = None
    operator = "OR"

    def __init__(self, *values):
        child_job_functions = (
            list(
                set(
                    itertools.chain.from_iterable(
                        job_function.get_descendants().values_list("pk", flat=True)
                        for job_function in JobFunction.objects.filter(id__in=values)
                    )
                )
            )
            or values
        )
        super().__init__(*child_job_functions)


class ChannelTypeFilter(FacetFilter):
    filter_name = "channel_type"
    parameter_name = "channelType"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Filter by channel type.",
        type=openapi.TYPE_STRING,
        enum=Channel.Type.values,
        required=False,
        explode=False,
    )
    operator = "AND"
    score = 0


class CustomerIdFilter(FacetFilter):
    filter_name = "customer_id"
    parameter_name = "customerId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Filter by customer id",
        type=openapi.TYPE_STRING,
        required=False,
        explode=False,
    )
    operator = "AND"
    score = 0


class IsMyOwnProductFilter(FacetFilter):
    filter_name = "is_my_own_product"
    parameter_name = "is_my_own_product"
    parameter = None
    operator = "AND"

    def __init__(self):
        self.filters = "is_my_own_product:false"


class FacetFilterCollection:
    def __init__(self, *facet_filters: FacetFilter, limit: int = 50, offset: int = 0):
        self.facet_filters = facet_filters
        self.limit = limit
        self.offset = offset

    def get_filters(self):
        and_filters = " AND ".join(
            [
                f"({facet_filter.filters})"
                for facet_filter in self.facet_filters
                if facet_filter.filters and facet_filter.operator.lower() == "and"
            ]
        )
        or_filters = " OR ".join(
            [
                f"({facet_filter.filters})"
                for facet_filter in self.facet_filters
                if facet_filter.filters and facet_filter.operator.lower() == "or"
            ]
        )
        filters = and_filters + (" AND ({})".format(or_filters) if or_filters else "")
        return filters

    def query(self):
        filters = self.get_filters()
        query = {
            "getRankingInfo": True,
            "analytics": False,
            "enableABTest": False,
            "attributesToRetrieve": "id",
            "attributesToSnippet": "*:20",
            "snippetEllipsisText": "…",
            "responseFields": "*",
            "facets": [
                "*",
                "searchable_industries_ids",
                "searchable_job_functions_ids",
                "searchable_job_titles_ids",
                "searchable_locations_context_ids",
                "searchable_locations_ids",
            ],
            "filters": filters,
            "sumOrFiltersScores": True,
            "length": self.limit,
            "offset": self.offset,
        }

        return query

    def __bool__(self):
        """
        A "falsy" FacetFilterCollection is a list of filters
        that don't filter anything. This will happen
        if you pass a request with no valid query parameters
        to the factory method.
        """
        return bool(self.query()["filters"])

    @classmethod
    def build_filter_collection_from_request(
        cls,
        request: "Request",
        filters: Iterable[Type[FacetFilter]],
        limit: int,
        offset: int,
    ):
        return cls(
            *[
                get_facet_filter(item, request.query_params.get(item.parameter_name))
                for item in filters
            ],
            limit=limit,
            offset=offset,
        )
