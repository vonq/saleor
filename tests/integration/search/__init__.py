import time
from contextlib import contextmanager
from typing import List, Tuple

from django.test import override_settings
from api.tests import AuthenticatedTestCase
from algoliasearch_django import AlgoliaIndex, algolia_engine
from django.db.models import Model
from django.conf import settings


def how_many_products_with_value(
    product_search_response, key: str, values: tuple, name_key="id"
):
    count = 0
    for product in product_search_response["results"]:
        for item in product[key]:
            if item[name_key] in values:
                count += 1
                break
    return count


def is_generic_product(product: dict) -> bool:
    """

    @rtype: object
    """
    return (
        0 == len(product["industries"])
        or any((industry["name"] == "Generic" for industry in product["industries"]))
        and 0 == len(product["job_functions"])
    )


@contextmanager
def setup_algolia(cls):
    with override_settings(
        ALGOLIA={
            "INDEX_SUFFIX": f"{__name__}_{cls.now}",
            "APPLICATION_ID": settings.ALGOLIA["APPLICATION_ID"],
            "API_KEY": settings.ALGOLIA["API_KEY"],
            "AUTO_INDEXING": False,
        }
    ):
        algolia_engine.reset(settings.ALGOLIA)
        for model_index_pair in cls.model_index_class_pairs:
            model_class, index_class = model_index_pair
            if not algolia_engine.is_registered(model_class):
                algolia_engine.register(model_class, index_class)
                algolia_engine.reindex_all(model_class)

        yield

        for model_index_pair in cls.model_index_class_pairs:
            model_class, _ = model_index_pair
            algolia_engine.reindex_all(model_class)


class SearchTestCase(AuthenticatedTestCase):
    """
    We need to gather all the product-search related tests into
    this one class, as we're hitting the live algolia index.
    This means that we need to create the index and populate
    it with test entities. This might take quite some time,
    and it's infeasible to do it on a setUp method.
    """

    model_index_class_pairs: List[Tuple[Model, AlgoliaIndex]]
    now: int

    @classmethod
    def setUpClass(cls) -> None:
        cls.now = int(time.time())
        with setup_algolia(cls):
            super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for model_index_pair in cls.model_index_class_pairs:
            _, index_class = model_index_pair
            algolia_engine.client.init_index(
                f"{index_class.index_name}_{__name__}_{cls.now}"
            ).delete()

            indices = algolia_engine.client.list_indices()
            ops = []

            for index in indices["items"]:
                index_name = index["name"]
                if f"{index_class.index_name}_{__name__}_{cls.now}" in index_name:
                    ops.append(
                        {
                            "indexName": index_name,
                            "action": "delete",
                        }
                    )

            algolia_engine.client.multiple_batch(ops)

        algolia_engine.reset(settings.ALGOLIA)
