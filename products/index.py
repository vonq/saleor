from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from api.products.models import Product

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
        "duration_days",
        "available_in_ats",
        "salesforce_product_category",
        "similarweb_top_country_shares",
        # custom properties
        "searchable_industries_ids",
        "searchable_industries_names",
        "searchable_job_functions_ids",
        "searchable_job_functions_names",
        "searchable_job_titles_ids",
        "searchable_job_titles_names",
        "searchable_locations_ids",
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
    )
    settings = {
        "minWordSizefor1Typo": 4,
        "minWordSizefor2Typos": 8,
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
            "searchable_locations_names",
            "searchable_locations_context_ids",  # do we need it?
            "searchable_locations_context_names",
            "searchable_locations_context_mapbox_ids",
            "is_active",
            "filterable_status",
            "available_in_jmp",
            "is_addon",
            "is_product",
        ],
        "attributesToSnippet": None,
        "attributesToHighlight": None,
        "paginationLimitedTo": 1000,
        "attributeForDistinct": None,
        "exactOnSingleWordQuery": "attribute",
        "ranking": [
            "filters",
            "desc(maximum_locations_cardinality)",
        ],
        "customRanking": [
            "desc(filters)",
            "desc(maximum_locations_cardinality)",
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
