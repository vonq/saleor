from typing import List, ClassVar, Tuple, Dict

from algoliasearch_django import raw_search

import requests
import urllib.parse
from django.conf import settings


def query_search_index(
    model_class: ClassVar, params: dict, query: str = ""
) -> Tuple[int, List[dict], Dict[str, int]]:
    """
    NOTE: This will only return a maximum of paginationLimitedTo items
    (which might be what we want – or not).
    """
    if query:
        result = raw_search(model_class, query=query, params=params)
    else:
        result = raw_search(model_class, params=params)

    if not result:
        # raw_search can return a None
        # instead of an empty result set
        # if using empty search parameters
        return 0, [], {}

    hits = result.get("hits", [])
    total_hits = result.get("nbHits")
    facets = result.get("facets")

    return total_hits, hits, facets


def query_parser_index(title: str) -> Tuple[int, List]:
    """
    NOTE: Quick and dirty implementation, ready for refactoring by someone with more familiarity of back-end.
    """
    headers = {
        "X-Algolia-API-Key": settings.ALGOLIA["API_KEY"],
        "X-Algolia-Application-Id": settings.ALGOLIA["APPLICATION_ID"],
        # "X-Algolia-UserToken": "testbench",
    }
    r = requests.post(
        "https://OWF766BMHV-dsn.algolia.net/1/indexes/parser/query",
        '{ "params": "query='
        + urllib.parse.quote(title)
        + '&hitsPerPage=2&getRankingInfo=1" }',
        headers=headers,
    )
    hits = r.json()["hits"]
    return len(hits), hits


def get_results_ids(results) -> List[int]:
    return [result["id"] for result in results]
