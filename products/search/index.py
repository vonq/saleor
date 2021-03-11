from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from api.products.models import JobTitle, Product

from django.conf import settings as django_settings


@register(Product)
class ProductIndex(AlgoliaIndex):
    fields = (
        "id",
        "title",
        "searchable_product_title",
        "url",
        "channel",
        "description",
        "logo_url",
        "is_active",
        "is_generic",
        "is_international",
        "duration_days",
        "available_in_ats",
        "salesforce_product_category",
        "similarweb_top_country_shares",
        "customer_id",
        # custom properties
        "channel_type",
        "searchable_industries_ids",
        "searchable_industries_names",
        "searchable_job_functions_ids",
        "searchable_job_functions_names",
        "searchable_job_titles_ids",
        "searchable_job_titles_names",
        "searchable_locations_ids",
        "searchable_locations_mapbox_ids",
        "searchable_locations_names",
        "searchable_locations_context_ids",  # do we need it?
        "searchable_locations_context_names",
        "searchable_locations_context_mapbox_ids",
        "primary_similarweb_location",
        "secondary_similarweb_location",
        "maximum_locations_cardinality",
        "filterable_status",
        "available_in_jmp",
        "is_addon",
        "is_product",
        "order_frequency",
        "is_my_own_product",
    )
    settings = {
        "minWordSizefor1Typo": 3,
        "minWordSizefor2Typos": 5,
        "hitsPerPage": 20,
        "maxValuesPerFacet": 100,
        "searchableAttributes": [
            "unordered(searchable_product_title)",
        ],
        "numericAttributesToIndex": ["maximum_locations_cardinality", "duration_days"],
        "attributesToRetrieve": None,
        "ignorePlurals": ["en", "de", "nl"],
        "advancedSyntax": True,
        "unretrievableAttributes": None,
        "optionalWords": None,
        "queryLanguages": ["de", "nl", "en"],
        "attributesForFaceting": [
            "searchable_industries_ids",
            "searchable_industries_names",
            "searchable_job_functions_ids",
            "searchable_job_functions_names",
            "searchable_job_titles_ids",
            "searchable_job_titles_names",
            "searchable_locations_ids",
            "searchable_locations_mapbox_ids",
            "searchable_locations_names",
            "searchable_locations_context_ids",  # do we need it?
            "searchable_locations_context_names",
            "searchable_locations_context_mapbox_ids",
            "is_active",
            "is_generic",
            "is_international",
            "filterable_status",
            "available_in_jmp",
            "is_addon",
            "is_product",
            "order_frequency",
            "channel_type",
            "customer_id",
            "is_my_own_product",
        ],
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 1000,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "attribute",
        "ranking": [
            "filters",
            "desc(order_frequency)",
            "desc(maximum_locations_cardinality)",
        ],
        "customRanking": [],
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
        "searchableAttributes": ["searchable_keywords"],
        "numericAttributesToIndex": ["maximum_locations_cardinality", "duration_days"],
        "attributesToRetrieve": None,
        "ignorePlurals": ["en", "nl", "de"],
        "decompoundedAttributes": {
            "de": ["searchable_keywords"],
            "nl": ["searchable_keywords"],
        },
        "advancedSyntax": True,
        "unretrievableAttributes": None,
        "optionalWords": None,
        "queryLanguages": ["en", "nl", "de"],
        "attributesForFaceting": ["searchable_keywords"],
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 10,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "attribute",
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
