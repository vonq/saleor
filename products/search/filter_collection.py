from typing import Iterable, Type

from api.products.search.filters.facet_filters import FacetFilter, get_facet_filter
from api.products.search.filters.facet_filters_groups import (
    FacetFiltersGroup,
    get_group_facet_filter,
)


class FacetFilterCollection:
    def __init__(
        self,
        facet_filters: Iterable[Type[FacetFilter]],
        group_facet_filters: Iterable[Type[FacetFiltersGroup]],
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
            "analytics": True,
            "enableABTest": False,
            "attributesToRetrieve": "id",
            "attributesToSnippet": "*:20",
            "snippetEllipsisText": "…",
            "responseFields": "*",
            "facets": [
                # By default, the returned values are sorted by frequency,
                # but this can be changed to alphabetical with sortFacetValuesBy.
                "searchable_industries_ids",
                "searchable_job_functions_ids",
                "searchable_job_titles_ids",
                "searchable_locations_ids",
                "searchable_locations_names",
                "searchable_locations_names_nl",
                "searchable_locations_names_de",
                "category_ids",
                "order_frequency",
                "channel_type",
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
        group_filters: Iterable[Type[FacetFiltersGroup]],
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
