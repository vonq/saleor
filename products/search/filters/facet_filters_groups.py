import itertools
from abc import abstractmethod
from collections import Counter
from typing import ClassVar, List, Optional, Type

from rest_framework.request import Request

from api.products.models import SEPARATOR
from api.products.search.filters.facet_filters import (
    FacetFilter,
    InclusiveJobFunctionChildrenFilter,
    InclusiveLocationIdFacetFilter,
    IndustryFacetFilter,
    IsGenericFacetFilter,
    IsInternationalFacetFilter,
)
from api.products.search.filters.scores import (
    is_generic_score,
    matches_industry_and_international_score,
    matches_industry_and_location_score,
    matches_jobfunction_and_international_score,
    matches_jobfunction_and_location_score,
    matches_jobfunction_industry_and_location_score,
    matches_location_and_generic_score,
)


class FacetFiltersGroup:
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


class JobFunctionIndustryAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_jobfunctions_industries_locations_combinations"
    facet_filters = [
        InclusiveJobFunctionChildrenFilter,
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_jobfunction_industry_and_location_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


def get_group_facet_filter(
    group_facet_filter_class: ClassVar, user_request: Request, all_facet_filters
) -> Optional[Type[FacetFiltersGroup]]:
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


class JobFunctionAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_jobfunctions_locations_combinations"
    facet_filters = [InclusiveJobFunctionChildrenFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_jobfunction_and_location_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class GenericAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_isgeneric_locations_combinations"
    facet_filters = [IsGenericFacetFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_location_and_generic_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = user_request.query_params.keys()
        is_search_by_exact_location = "exactLocationId" in list(qp_keys)
        return not is_search_by_exact_location


class InternationalAndFunctionGroup(FacetFiltersGroup):
    parameter_name = "searchable_isinternational_jobfunctions_combinations"
    facet_filters = [IsInternationalFacetFilter, InclusiveJobFunctionChildrenFilter]
    operator = "AND"
    score = matches_jobfunction_and_international_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class IndustryAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_industries_locations_combinations"
    facet_filters = [
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_industry_and_location_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class IndustryAndInternationalGroup(FacetFiltersGroup):
    parameter_name = "searchable_industries_isinternational_combinations"
    facet_filters = [
        IndustryFacetFilter,
        IsInternationalFacetFilter,
    ]
    operator = "AND"
    score = matches_industry_and_international_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        return True


class GenericAndInternationalGroup(FacetFiltersGroup):
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


class WrongFacetFilterTypeError(TypeError):
    pass
