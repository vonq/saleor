import itertools
from typing import Type

from drf_yasg2 import openapi
from rest_framework.exceptions import ValidationError

from api.products.models import Location


class FacetFilter:
    filter_name: str
    parameter_name: str
    filters: str
    parameter: openapi.Parameter
    score: int

    def __init__(self, *values):
        self.filters = f" OR ".join(
            [f'{self.filter_name}:"{value}"<score={self.score}>' for value in values]
        )


class InclusiveLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_context_mapbox_ids"
    parameter_name = "includeLocationId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Id for a location. Optionally, a (comma-separated) array of values can be passed.",
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
        locations_and_contexts = Location.list_context_locations_ids(values)
        super().__init__(*locations_and_contexts)


class ExactLocationIdFacetFilter(FacetFilter):
    filter_name = "searchable_locations_ids"
    parameter_name = "exactLocationId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Match only for products assigned to a location id",
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
        if len(values) > 1:
            self.filters = ""
            return
        country_codes = Location.objects.filter(id__in=values).values_list(
            "country_code", flat=True
        )
        super().__init__(*country_codes)


class SecondarySimilarWebFacetFilter(PrimarySimilarWebFacetFilter):
    filter_name = "secondary_similarweb_location"
    parameter_name = "includeLocationId"
    parameter = None
    score = 7


class JobFunctionsFacetFilter(FacetFilter):
    filter_name = "searchable_job_functions_ids"
    parameter_name = "jobFunctionId"
    parameter = openapi.Parameter(
        parameter_name,
        in_=openapi.IN_QUERY,
        description="Job title id",
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


class FacetFilterCollection:
    def __init__(self, *facet_filters: FacetFilter):
        self.facet_filters = facet_filters

    def query(self):
        return {
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
            "filters": " OR ".join(
                [
                    facet_filter.filters
                    for facet_filter in self.facet_filters
                    if facet_filter.filters
                ]
            ),
            "sumOrFiltersScores": True,
        }
