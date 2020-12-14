from typing import List, ClassVar, Tuple

from algoliasearch_django import raw_search


def query_search_index(
    model_class: ClassVar, params: dict, query: str = ""
) -> Tuple[int, List[dict]]:
    """
    NOTE: This will only return a maximum of paginationLimitedTo items
    (which might be what we want – or not).
    """
    if query:
        result = raw_search(model_class, query=query, params=params)
    else:
        result = raw_search(model_class, params=params)

    hits = result.get("hits", [])
    total_hits = result.get("nbHits")

    return total_hits, hits


def get_results_ids(results) -> List[int]:
    return [result["id"] for result in results]
