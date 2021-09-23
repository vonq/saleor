import itertools
from typing import ClassVar, Iterable, Type, Dict

from drf_yasg2 import openapi

from api.products.models import JobFunction, Location, Channel, Product
from api.products.search.filters.scores import (
    descendant_job_functions_score,
    exact_location_score,
    is_generic_score,
    is_international_score,
    job_function_score,
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
        description="Id for a Location to search products against. If no exact matches exist, search will be expanded "
        "to the Location's region and country. Optionally, a (comma-separated) array of values can be "
        "passed. Passing multiple values increases the number of search results.",
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
        self.filters = f'filterable_status:"{Product.Status.ACTIVE}"'


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


class PriceLessThanFacetFilter(FacetFilter):
    filter_name = "list_price"
    parameter_name = "priceTo"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products with a list price (in EUR) up to a certain figure",
        type=openapi.TYPE_INTEGER,
        required=False,
        explode=False,
    )
    operator = "AND"

    def __init__(self, value=None, **kwargs):
        self.filters = f"{self.filter_name}<={value}" if value else ""


class PriceMoreThanFacetFilter(FacetFilter):
    filter_name = "list_price"
    parameter_name = "priceFrom"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only products with a list price (in EUR) more than a certain figure",
        type=openapi.TYPE_INTEGER,
        required=False,
        explode=False,
    )
    operator = "AND"

    def __init__(self, value=None, **kwargs):
        self.filters = f"{self.filter_name}>={value}" if value else ""


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
                ).union(
                    set(
                        itertools.chain.from_iterable(
                            job_function.get_ancestors(include_self=False).values_list(
                                "pk", flat=True
                            )
                            for job_function in JobFunction.objects.filter(
                                id__in=values
                            )
                        )
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
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_STRING, enum=Channel.Type.values),
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


class IsNotMyOwnProductFilter(FacetFilter):
    filter_name = "is_my_own_product"
    parameter_name = "is_my_own_product"
    parameter = None
    operator = "AND"

    def __init__(self, **kwargs):
        self.filters = f"{self.filter_name}:false"


class DiversityFacetFilter(FacetFilter):
    filter_name = "diversity"
    parameter_name = "diversityId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Diversity category id",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_INTEGER),
        required=False,
        explode=False,
    )
    operator = "AND"
    score = 1


class EmploymentTypeFacetFilter(FacetFilter):
    filter_name = "employment_type"
    parameter_name = "employmentTypeId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Employment type category id",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_INTEGER),
        required=False,
        explode=False,
    )
    operator = "AND"
    score = 1


class SeniorityLevelFacetFilter(FacetFilter):
    filter_name = "seniority_level"
    parameter_name = "seniorityId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Seniority level category id",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_INTEGER),
        required=False,
        explode=False,
    )
    operator = "AND"
    score = 1


MAP_FILTER_NAME_TO_PARAMETERS: Dict[str, str] = {
    klass.filter_name: klass.parameter_name for klass in FacetFilter.__subclasses__()
}


def convert_facet_payload(facets: Dict[str, int]) -> Dict[str, int]:
    """
    A collection of facet counts returned from algolia will use
    the facet as named in the index, which is different from
    the parameter name we use in the API interface.
    """
    converted = {}
    for k, v in facets.items():
        if k in MAP_FILTER_NAME_TO_PARAMETERS.keys():
            converted[MAP_FILTER_NAME_TO_PARAMETERS[k]] = v
        else:
            converted[k] = v
    return converted
