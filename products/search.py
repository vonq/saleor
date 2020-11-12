from functools import partial
from multiprocessing.pool import ThreadPool
from typing import List, Type, ClassVar

from algoliasearch_django import raw_search

from api.products.filters import FacetFilter


def get_facet_filter(
    facet_filter_class: ClassVar, parameters: str
) -> Type[FacetFilter]:
    parameter_ids = parameters.split(",") if parameters else []
    return facet_filter_class(*parameter_ids)


def paginated_search_wrapper(model_class, params, page_number):
    new_params = dict(params, **{"hitsPerPage": 200, "page": page_number})
    return raw_search(model_class, params=new_params)


def search_all_pages(model_class: ClassVar, params: dict) -> List[dict]:
    """
    NOTE: This will only return a maximum of paginationLimitedTo items
    (which might be what we want – or not).
    """
    results = []

    result = raw_search(model_class, params=params)
    hits = result.get("hits")
    results.extend(hits)

    total_pages = result.get("nbPages")

    if total_pages and total_pages > 1:
        pool = ThreadPool(total_pages - 1)
        response = pool.map(
            func=partial(paginated_search_wrapper, model_class, params),
            iterable=range(2, total_pages + 1),
        )

        for page in response:
            results.extend(page.get("hits"))

    return results


def get_results_ids(results):
    return [result["id"] for result in results]
