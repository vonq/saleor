from typing import Dict, List, Tuple

from algoliasearch.search_index import SearchIndex
from algoliasearch_django import AlgoliaIndex, algolia_engine
from algoliasearch_django.decorators import register

from api.products.models import JobTitle, Product, JobFunction

from django.conf import settings as django_settings


class SortingReplicaIndex(AlgoliaIndex):
    """
    Like an AlgoliaIndex, but with a twist to automatically setup
    and initialise virtual replicas
    """

    SORTING_REPLICAS: Dict[str, List[str]] = {}

    def reindex_all(self, batch_size=1000):
        """
        Apply cascade replica settings on reindex
        """
        for replica_name, replica_settings in self.SORTING_REPLICAS.items():
            index = self._AlgoliaIndex__client.init_index(
                self.get_replica_index_name(replica_name)
            )  # type: SearchIndex
            index.set_settings(replica_settings)

        # needed to make sure the replica settings is
        # taking note of the optional settings' SUFFIX
        self.settings["replicas"] = get_replicas()
        counts = super().reindex_all(batch_size)
        return counts

    def raw_search_sorted(
        self, sort_index: str, query="", params=None
    ) -> Tuple[int, List[dict], Dict[str, int]]:
        """
        As opposed to standard "relevant" search
        """
        if params is None:
            params = {}
        if sort_index not in self.SORTING_REPLICAS.keys():
            raise ValueError(f"Can't sort for {sort_index}")
        adapter = algolia_engine.client.init_index(
            self.get_replica_index_name(sort_index)
        )
        result = adapter.search(query, params)
        hits = result.get("hits", [])
        total_hits = result.get("nbHits")
        facets = result.get("facets")
        return total_hits, hits, facets

    def get_replica_index_name(self, replica_name):
        return f"{self.index_name}_{replica_name}"


def get_replica_name_for_settings(replica_name):
    env = django_settings.ENV
    model = "Product"
    suffix = django_settings.ALGOLIA.get("INDEX_SUFFIX")
    if suffix:
        return f"{env}_{model}_{suffix}_{replica_name}"
    return f"{env}_{model}_{replica_name}"


def get_replicas():
    """
    Needed to make sure that integration tests
    are able to use the prefixed indices for replicas
    """
    return [
        f"virtual({get_replica_name_for_settings('order_frequency.desc')})",
        f"virtual({get_replica_name_for_settings('order_frequency.asc')})",
        f"virtual({get_replica_name_for_settings('created.desc')})",
        f"virtual({get_replica_name_for_settings('created.asc')})",
        f"virtual({get_replica_name_for_settings('list_price.desc')})",
        f"virtual({get_replica_name_for_settings('list_price.asc')})",
    ]


@register(Product)
class ProductIndex(SortingReplicaIndex):
    SORTING_REPLICAS = {
        "order_frequency.desc": {"customRanking": ["desc(order_frequency)"]},
        "order_frequency.asc": {"customRanking": ["asc(order_frequency)"]},
        "created.desc": {"customRanking": ["desc(created)"]},
        "created.asc": {"customRanking": ["asc(created)"]},
        "list_price.desc": {"customRanking": ["desc(list_price)"]},
        "list_price.asc": {"customRanking": ["asc(list_price)"]},
    }
    fields = (
        "id",
        "title",
        "searchable_product_title",
        "channel_name",
        "url",
        "channel",
        "is_active",
        "is_generic",
        "is_international",
        "duration_days",
        "available_in_ats",
        "salesforce_product_category",
        "similarweb_top_country_shares",
        "customer_id",
        "created",
        # custom properties
        "channel_type",
        "searchable_industries_ids",
        "searchable_job_functions_ids",
        "searchable_job_titles_ids",
        "searchable_locations_ids",
        "searchable_locations_mapbox_ids",
        "searchable_locations_names",
        "searchable_locations_names_de",
        "searchable_locations_names_nl",
        "searchable_locations_context_mapbox_ids",
        "primary_similarweb_location",
        "secondary_similarweb_location",
        "maximum_jobfunctions_depth",
        "maximum_locations_cardinality",
        "filterable_status",
        "available_in_jmp",
        "available_in_ats",
        "is_addon",
        "is_product",
        "order_frequency",
        "is_my_own_product",
        "diversity",
        "employment_type",
        "seniority_level",
        "list_price",
        "searchable_jobfunctions_industries_locations_combinations",
        "searchable_jobfunctions_locations_combinations",
        "searchable_isgeneric_locations_combinations",
        "searchable_isinternational_jobfunctions_combinations",
        "searchable_industries_locations_combinations",
        "searchable_industries_isinternational_combinations",
        "searchable_isgeneric_isinternational",
    )
    settings = {
        "minWordSizefor1Typo": 5,
        "minWordSizefor2Typos": 8,
        "hitsPerPage": 20,
        "maxValuesPerFacet": 100,
        "searchableAttributes": [
            "channel_name",
            "title",
        ],
        "numericAttributesToIndex": [
            "maximum_locations_cardinality",
            "maximum_jobfunctions_depth",
            "duration_days",
            "list_price",
        ],
        "attributesToRetrieve": None,
        "ignorePlurals": ["en", "de", "nl"],
        "advancedSyntax": True,
        "unretrievableAttributes": None,
        "optionalWords": None,
        "queryLanguages": ["de", "nl", "en"],
        "attributesForFaceting": [
            "searchable_industries_ids",
            "searchable_job_functions_ids",
            "searchable_job_titles_ids",
            "searchable_locations_ids",
            "searchable_locations_mapbox_ids",
            "searchable_locations_names",
            "searchable_locations_names_de",
            "searchable_locations_names_nl",
            "searchable_locations_context_mapbox_ids",
            "diversity",
            "employment_type",
            "seniority_level",
            "is_active",
            "is_generic",
            "is_international",
            "filterable_status",
            "available_in_jmp",
            "available_in_ats",
            "is_addon",
            "is_product",
            "order_frequency",
            "channel_type",
            "customer_id",
            "is_my_own_product",
            "searchable_jobfunctions_industries_locations_combinations",
            "searchable_jobfunctions_locations_combinations",
            "searchable_isgeneric_locations_combinations",
            "searchable_isinternational_jobfunctions_combinations",
            "searchable_industries_locations_combinations",
            "searchable_industries_isinternational_combinations",
            "searchable_isgeneric_isinternational",
        ],
        "replicas": get_replicas(),
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 1000,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "word",
        "ranking": [
            "typo",
            "exact",
            "words",
            "attribute",
            "proximity",
            "filters",
            "custom",
        ],
        "customRanking": [
            "desc(maximum_locations_cardinality)",
            "desc(maximum_jobfunctions_depth)",
            "desc(order_frequency)",
        ],
        "separatorsToIndex": "",
        "removeWordsIfNoResults": "lastWords",
        "queryType": "prefixLast",
        "highlightPreTag": "<em>",
        "highlightPostTag": "</em>",
        "snippetEllipsisText": "",
        "alternativesAsExact": ["ignorePlurals", "singleWordSynonym"],
        "indexLanguages": ["en", "nl", "de"],
    }

    index_name = f"{django_settings.ENV}_Product"


@register(JobTitle)
class JobTitleIndex(AlgoliaIndex):
    should_index = "active_and_canonical"
    fields = ("id", "name", "searchable_keywords", "frequency")
    settings = {
        "minWordSizefor1Typo": 5,
        "minWordSizefor2Typos": 8,
        "hitsPerPage": 5,
        "maxValuesPerFacet": 100,
        "minProximity": 10,
        "searchableAttributes": ["unordered(searchable_keywords)"],
        "numericAttributesToIndex": ["maximum_locations_cardinality", "duration_days"],
        "attributesToRetrieve": None,
        "ignorePlurals": ["en", "nl", "de"],
        "advancedSyntax": True,
        "unretrievableAttributes": None,
        "optionalWords": None,
        "queryLanguages": ["en", "nl", "de"],
        "attributesForFaceting": ["searchable_keywords"],
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 10,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "word",
        "ranking": [
            "typo",
            "exact",
            "words",
            "attribute",
            "proximity",
            "filters",
            "custom",
        ],
        "customRanking": ["desc(frequency)"],
        "separatorsToIndex": "",
        "removeWordsIfNoResults": "allOptional",
        "queryType": "prefixLast",
        "highlightPreTag": "<em>",
        "highlightPostTag": "</em>",
        "snippetEllipsisText": "",
        "alternativesAsExact": ["ignorePlurals", "singleWordSynonym"],
        "indexLanguages": ["en", "nl", "de"],
    }
    index_name = f"{django_settings.ENV}_JobTitle"


@register(JobFunction)
class JobFunctionIndex(AlgoliaIndex):
    fields = ("id", "name", "all_job_titles")
    settings = {
        "minWordSizefor1Typo": 5,
        "minWordSizefor2Typos": 8,
        "hitsPerPage": 5,
        "searchableAttributes": ["unordered(all_job_titles)"],
        "attributesToRetrieve": None,
        "ignorePlurals": ["en", "nl", "de"],
        "decompoundedAttributes": {
            "de": ["all_job_titles"],
            "nl": ["all_job_titles"],
        },
        "advancedSyntax": True,
        "unretrievableAttributes": None,
        "optionalWords": [
            "asia",
            "adviseur",
            "advisor",
            "assistant",
            "associate",
            "consultant",
            "executive",
            "corporate",
            "global",
            "officer",
            "de",
            "e",
            "m",
            "f",
            "x",
            "person",
            "operator",
            "digital",
            "online",
            "ervaran",
            "expert",
            "interim",
            "internship",
            "junior",
            "senior",
            "leader",
            "manager",
            "medeworker",
            "medior",
            "regional",
            "service",
            "specialist",
            "strategisch",
            "supervisor",
            "technisch",
            "teamleider",
            "teammanager",
            "toezichthouder",
            "trainee",
            "jobs",
            "of",
            "werkvoorbereider",
            "general",
            "duties",
            "duty",
            "worker",
            "fulltime",
            "full time",
            "parttime",
            "part time",
        ],
        "queryLanguages": ["en", "nl", "de"],
        "attributesForFaceting": ["all_job_titles"],
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 10,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "word",
        "ranking": [
            "typo",
            "exact",
            "words",
            "attribute",
            "proximity",
            "filters",
            "custom",
        ],
        "customRanking": ["desc(frequency)"],
        "separatorsToIndex": "",
        "removeWordsIfNoResults": "allOptional",
        "queryType": "prefixLast",
        "highlightPreTag": "<em>",
        "highlightPostTag": "</em>",
        "snippetEllipsisText": "",
        "alternativesAsExact": ["ignorePlurals", "singleWordSynonym"],
        "indexLanguages": ["en", "nl", "de"],
    }
    index_name = f"{django_settings.ENV}_JobFunction"
