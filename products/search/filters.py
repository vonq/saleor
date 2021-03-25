import itertools
from abc import abstractmethod
from collections import Counter
from typing import ClassVar, Iterable, List, Optional, Type

from drf_yasg2 import openapi
from rest_framework.request import Request

from api.products.models import JobFunction, Location, Channel, SEPARATOR
from api.products.search.scores import (
    descendant_job_functions_score,
    exact_location_score,
    is_generic_score,
    is_international_score,
    job_function_score,
    matches_industry_and_international,
    matches_industry_and_location,
    matches_jf_and_location,
    matches_jf_industry_and_location,
    matches_jf_location_and_generic,
    primary_similarweb_location,
    secondary_similarweb_location,
)


class FacetFilter:
    operator: str = "OR"
    filter_name: str
    parameter_name: str
    parameter_values: Iterable = tuple()
    secondary_parameter_name = ""
    secondary_parameter_values = tuple()
    filters: str = ""
    parameter: openapi.Parameter
    score: int

    def __init__(self, *values, secondary_values: Iterable = ()):
        """
        @param: secondary_values - an Iterable of values corresponding to secondary_parameter_name when primary_parameter_name cannot be found in request query args. Used to derive primary_values
        """
        self.parameter_values = values if isinstance(values, Iterable) else [values]

        if not self.parameter_values and secondary_values:
            secondary_values = (
                secondary_values if isinstance(values, Iterable) else [secondary_values]
            )
            self.parameter_values = self.get_primary_from_secondary_values(
                secondary_values
            )

        self.filters = f" OR ".join(
            [
                f'{self.filter_name}:"{value}"<score={self.score}>'
                for value in self.parameter_values
            ]
        )

    def get_primary_from_secondary_values(self, values):
        raise NotImplementedError("Method must be implemented in child classes")


def get_facet_filter(
    facet_filter_class: ClassVar, parameters: str, secondary_parameters: str
) -> Type[FacetFilter]:
    parameter_ids = parameters.split(",") if parameters else []
    secondary_parameter_ids = (
        secondary_parameters.split(",") if secondary_parameters else []
    )
    return facet_filter_class(*parameter_ids, secondary_values=secondary_parameter_ids)


class InclusiveLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_mapbox_ids"
    parameter_name = "includeLocationId"
    operator = "OR"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Id for a Location to search products against. If no exact matches exist, search will be expanded to the Location's region and country. Optionally, a (comma-separated) array of values can be passed. Passing multiple values increases the number of search results.",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_STRING),
        required=False,
        explode=False,
    )
    score = 1  # inclusive_location_score

    def __init__(self, *values, **kwargs):
        """
        Here we're passed a list of location ids, for which we want to
        retrieve the entire family (ascendants and descendants)
        """
        locations_and_contexts = Location.list_context_locations_ids(values)
        child_locations = Location.list_child_locations(
            values, only_associated_to_products=True
        )
        all_locations = list(set(locations_and_contexts + child_locations))
        super().__init__(*all_locations)


class ExactLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_ids"
    operator = "AND"
    parameter_name = "exactLocationId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products specifically assigned to a Location.",
        type=openapi.TYPE_STRING,
        required=False,
        explode=False,
    )
    score = exact_location_score


class PrimarySimilarWebFacetFilter(FacetFilter):
    filter_name = "primary_similarweb_location"
    parameter_name = "includeLocationId"
    parameter = None
    score = primary_similarweb_location

    def __init__(self, *values, **kwargs):
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
    score = secondary_similarweb_location


class IsActiveFacetFilter(FacetFilter):
    filter_name = "is_active"
    parameter_name = "is_active"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
        self.filters = f"{self.parameter_name}:true"


class IsAvailableInJmpFacetFilter(FacetFilter):
    filter_name = "available_in_jmp"
    parameter_name = "available_in_jmp"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
        self.filters = f"{self.filter_name}:true"


class IsGenericFacetFilter(FacetFilter):
    filter_name = "is_generic"
    parameter_name = "is_generic"
    parameter_values = "True"
    parameter = None
    operator = "OR"

    def __init__(self, **kwargs):
        super().__init__(self.parameter_values)

    score = is_generic_score


class IsInternationalFacetFilter(FacetFilter):
    filter_name = "is_international"
    parameter_name = "is_international"
    parameter_values = "True"
    parameter = None
    operator = "OR"

    def __init__(self, **kwargs):
        super().__init__(self.parameter_values)

    score = is_international_score


class StatusFacetFilter(FacetFilter):
    filter_name = "filterable_status"
    parameter_name = "status"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
        self.filters = 'filterable_status:"None" OR filterable_status:"Trial" OR filterable_status:"Negotiated"'


class ProductsOnlyFacetFilter(FacetFilter):
    filter_name = "is_product"
    parameter_name = "is_product"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
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

    def __init__(self, value=None, **kwargs):
        self.filters = f"{self.filter_name}>={value}" if value else ""


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

    def __init__(self, value=None, **kwargs):
        self.filters = f"{self.filter_name}<={value}" if value else ""


class AddonsOnlyFacetFilter(FacetFilter):
    filter_name = "is_addon"
    parameter_name = "is_addon"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
        self.filters = f"{self.filter_name}:true"


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
    score = job_function_score


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
    score = 1  # industry_score


class InclusiveJobFunctionChildrenFilter(FacetFilter):
    filter_name = "searchable_job_functions_ids"
    parameter_name = "jobFunctionId"
    secondary_parameter_name = "jobTitleId"
    score = descendant_job_functions_score
    parameter = None
    operator = "OR"

    def __init__(self, *values, secondary_values=(), **kwargs):
        """
        @param values: jobfunction ids
        @type values: Iterable
        @param secondary_values: jobtitle ids - if user request does not have parameter_name as query arg,
        secondary_parameter_name will be used instead, with its values passed to secondary_values arg
        @type secondary_values: Iterable
        """
        if not values and secondary_values:
            values = self.get_primary_from_secondary_values(secondary_values)

        child_job_functions = (
            list(
                set(
                    itertools.chain.from_iterable(
                        job_function.get_descendants(include_self=True).values_list(
                            "pk", flat=True
                        )
                        for job_function in JobFunction.objects.filter(id__in=values)
                    )
                )
            )
            or values
        )
        super().__init__(*child_job_functions)

    def get_primary_from_secondary_values(self, values: list):
        return JobFunction.objects.filter(jobtitle__id__in=values)


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

    def __init__(self, **kwargs):
        self.filters = f"{self.filter_name}:false"


class WrongFacetFilterTypeError(TypeError):
    pass


class GroupFacetFilter:
    parameter_name: str
    facet_filters: List[Type[FacetFilter]]
    filters: str
    operator: str
    score: int

    def __init__(self, *values: FacetFilter):
        for value in values:
            if type(value) not in self.facet_filters:
                raise WrongFacetFilterTypeError(f"Invalid facet filter: {type(value)}")
        combinations = set(
            itertools.product(*[value.parameter_values for value in values])
        )
        self.filters = " OR ".join(
            [
                f' {self.parameter_name}: "{SEPARATOR.join(map(str, combination))}"<score={self.score}>'
                for combination in combinations
            ]
        )

    @classmethod
    @abstractmethod
    def can_be_included(cls, user_request: Request) -> bool:
        """
        Helper function to conditionally allow including a group filter in the index query.
        @rtype: bool
        """
        pass


def get_group_facet_filter(
    group_facet_filter_class: ClassVar, user_request: Request, all_facet_filters
) -> Optional[Type[GroupFacetFilter]]:
    facet_filters, facet_filters_types = [], []

    for facet_filter_type in group_facet_filter_class.facet_filters:
        try:
            facet_filter_instance = next(
                ff
                for ff in all_facet_filters
                if ff.parameter_values and type(ff) == facet_filter_type
            )
        except StopIteration:
            continue
        if facet_filter_instance.filters:
            facet_filters.append(facet_filter_instance)
            facet_filters_types.append(facet_filter_type)

    all_facet_filters_have_values = Counter(
        group_facet_filter_class.facet_filters
    ) == Counter(facet_filters_types)
    if (
        group_facet_filter_class.can_be_included(user_request)
        and all_facet_filters_have_values
    ):
        return group_facet_filter_class(*facet_filters)
    return None


class JobFunctionIndustryAndLocationGroup(GroupFacetFilter):
    parameter_name = "searchable_jobfunctions_industries_locations_combinations"
    facet_filters = [
        InclusiveJobFunctionChildrenFilter,
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_jf_industry_and_location

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class JobFunctionAndLocationGroup(GroupFacetFilter):
    parameter_name = "searchable_jobfunctions_locations_combinations"
    facet_filters = [InclusiveJobFunctionChildrenFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_jf_and_location

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class GenericAndLocationGroup(GroupFacetFilter):
    parameter_name = "searchable_isgeneric_locations_combinations"
    facet_filters = [IsGenericFacetFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_jf_location_and_generic

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = user_request.query_params.keys()
        is_search_by_exact_location = "exactLocationId" in list(qp_keys)
        return not is_search_by_exact_location


class InternationalAndFunctionGroup(GroupFacetFilter):
    parameter_name = "searchable_isinternational_jobfunctions_combinations"
    facet_filters = [IsInternationalFacetFilter, InclusiveJobFunctionChildrenFilter]
    operator = "AND"
    score = is_international_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class IndustryAndLocationGroup(GroupFacetFilter):
    parameter_name = "searchable_industries_locations_combinations"
    facet_filters = [
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_industry_and_location

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class IndustryAndInternationalGroup(GroupFacetFilter):
    parameter_name = "searchable_industries_isinternational_combinations"
    facet_filters = [
        IndustryFacetFilter,
        IsInternationalFacetFilter,
    ]
    operator = "AND"
    score = matches_industry_and_international

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class GenericAndInternationalGroup(GroupFacetFilter):
    parameter_name = "searchable_isgeneric_isinternational"
    facet_filters = [IsGenericFacetFilter, IsInternationalFacetFilter]
    operator = "AND"
    score = is_generic_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = user_request.query_params.keys()

        is_search_by_name = len(qp_keys) == 1 and list(qp_keys)[0] == "name"
        is_search_by_exact_location = (
            len(qp_keys) == 1 and list(qp_keys)[0] == "exactLocationId"
        )
        is_search_by_name_and_exact_location = set(list(qp_keys)) == {
            "exactLocationId",
            "name",
        }
        is_search_by_inclusive_and_exact_location = set(list(qp_keys)) == {
            "exactLocationId",
            "includeLocationId",
        }
        return (
            not is_search_by_name
            and not is_search_by_exact_location
            and not is_search_by_name_and_exact_location
            and not is_search_by_inclusive_and_exact_location
        )


class FacetFilterCollection:
    def __init__(
        self,
        facet_filters: Iterable[Type[FacetFilter]],
        group_facet_filters: Iterable[Type[GroupFacetFilter]],
        limit: int = 50,
        offset: int = 0,
    ):
        self.facet_filters = facet_filters
        self.group_facet_filters = group_facet_filters
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

        group_filters = " OR ".join(
            f"({group_facet_filter.filters})"
            for group_facet_filter in self.group_facet_filters
        )

        filters = and_filters + (" AND ({})".format(or_filters) if or_filters else "")

        if group_filters:
            filters += f"AND {group_filters}"

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
                "searchable_locations_mapbox_ids",
            ],
            "filters": filters,
            "sumOrFiltersScores": False,
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
        group_filters: Iterable[Type[GroupFacetFilter]],
        limit: int,
        offset: int,
    ):
        facet_filters = [
            get_facet_filter(
                item,
                request.query_params.get(item.parameter_name),
                request.query_params.get(item.secondary_parameter_name),
            )
            for item in filters
        ]

        all_filters = [
            get_facet_filter(
                item,
                request.query_params.get(item.parameter_name),
                request.query_params.get(item.secondary_parameter_name),
            )
            for item in FacetFilter.__subclasses__()
        ]

        group_facet_filters = list(
            filter(
                None,
                [
                    get_group_facet_filter(item, request, all_filters)
                    for item in group_filters
                ],
            )
        )
        return cls(
            facet_filters=facet_filters,
            group_facet_filters=group_facet_filters,
            limit=limit,
            offset=offset,
        )
