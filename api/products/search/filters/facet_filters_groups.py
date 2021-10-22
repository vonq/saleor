import itertools
from abc import abstractmethod
from collections import Counter
from typing import ClassVar, List, Optional, Type

from rest_framework.request import Request

from api.products.models import SEPARATOR
from api.products.search import SEARCH_QUERY_PARAMETERS, SEARCH_FILTERS_QUERY_PARAMS
from api.products.search.filters.facet_filters import (
    FacetFilter,
    InclusiveJobFunctionChildrenFilter,
    InclusiveLocationIdFacetFilter,
    IndustryFacetFilter,
    IsGenericFacetFilter,
    IsInternationalFacetFilter,
)
from api.products.search.filters.scores import (
    matches_generic_international_score,
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
        By default, all facet filters should be disabled when user searches by name
        @rtype: bool
        """
        return "name" not in cls.get_qp_keys(user_request)

    @classmethod
    def get_qp_keys(cls, user_request: Request) -> set:
        """
        Returns a list of query parameters that are defined
        for the current user request
        """
        return {
            ele
            for ele in user_request.query_params
            if user_request.query_params[ele] and ele in SEARCH_QUERY_PARAMETERS
        }


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


class JobFunctionIndustryAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_jobfunctions_industries_locations_combinations"
    facet_filters = [
        InclusiveJobFunctionChildrenFilter,
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_jobfunction_industry_and_location_score


class JobFunctionAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_jobfunctions_locations_combinations"
    facet_filters = [InclusiveJobFunctionChildrenFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_jobfunction_and_location_score


class GenericAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_isgeneric_locations_combinations"
    facet_filters = [IsGenericFacetFilter, InclusiveLocationIdFacetFilter]
    operator = "AND"
    score = matches_location_and_generic_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = cls.get_qp_keys(user_request)
        is_search_by_exact_location = "exactLocationId" in qp_keys
        return super().can_be_included(user_request) and not is_search_by_exact_location


class InternationalAndFunctionGroup(FacetFiltersGroup):
    parameter_name = "searchable_isinternational_jobfunctions_combinations"
    facet_filters = [IsInternationalFacetFilter, InclusiveJobFunctionChildrenFilter]
    operator = "AND"
    score = matches_jobfunction_and_international_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = cls.get_qp_keys(user_request)
        # Only apply the "is international" condition if there's
        # no other filter supplied apart from jobTitle and jobFunction
        return super().can_be_included(user_request) and qp_keys.issubset(
            {
                InclusiveJobFunctionChildrenFilter.parameter_name,
                InclusiveJobFunctionChildrenFilter.secondary_parameter_name,
            }
        )


class JobFunctionGroup(FacetFiltersGroup):
    """
    Pseudo-group to tackle the use case of an inclusive job function search
    that is not limited to international boards.

    Needs to be a filter group so that it can be toggled depending
    on the state of InternationalAndFunctionGroup :/
    """

    parameter_name = InclusiveJobFunctionChildrenFilter.filter_name
    facet_filters = [InclusiveJobFunctionChildrenFilter]
    operator = "AND"
    score = InclusiveJobFunctionChildrenFilter.score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = cls.get_qp_keys(user_request)
        return (
            super().can_be_included(user_request)
            and "jobFunctionId" in qp_keys
            and qp_keys.intersection(SEARCH_FILTERS_QUERY_PARAMS)
            and not InternationalAndFunctionGroup.can_be_included(user_request)
        )


class IndustryAndLocationGroup(FacetFiltersGroup):
    parameter_name = "searchable_industries_locations_combinations"
    facet_filters = [
        IndustryFacetFilter,
        InclusiveLocationIdFacetFilter,
    ]
    operator = "AND"
    score = matches_industry_and_location_score


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
        qp_keys = cls.get_qp_keys(user_request)
        return (
            super().can_be_included(user_request)
            and "jobFunctionId" not in qp_keys
            and "jobTitleId" not in qp_keys
        )


class GenericAndInternationalGroup(FacetFiltersGroup):
    parameter_name = "searchable_isgeneric_isinternational"
    facet_filters = [IsGenericFacetFilter, IsInternationalFacetFilter]
    operator = "AND"
    score = matches_generic_international_score

    @classmethod
    def can_be_included(cls, user_request: Request) -> bool:
        qp_keys = cls.get_qp_keys(user_request)

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
        is_search_for_my_own_contracts = "customerId" in qp_keys

        is_categorical_search = bool(
            set(list(qp_keys))
            & {
                "diversityId",
                "employmentTypeId",
                "seniorityId",
            }
        )

        return (
            super().can_be_included(user_request)
            and not is_search_by_exact_location
            and not is_search_by_name_and_exact_location
            and not is_search_by_inclusive_and_exact_location
            and not is_search_for_my_own_contracts
            and not is_categorical_search
        )


class WrongFacetFilterTypeError(TypeError):
    pass
