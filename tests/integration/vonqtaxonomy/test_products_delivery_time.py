from math import ceil

from algoliasearch_django.decorators import disable_auto_indexing
from django.test import tag
from django.urls import reverse

from api.products.models import Product
from api.products.search.index import ProductIndex
from api.tests.integration.search import SearchTestCase


@tag("integration")
class ProductsDeliveryTimeTestCase(SearchTestCase):
    model_index_class_pairs = [(Product, ProductIndex)]
    PRODUCTS_DELIVERY_TIME_VIEWNAME = "api.products:deliverytime-totaldeliverytime"

    @classmethod
    def setUpTestData(cls):
        with disable_auto_indexing():
            cls.product_1 = Product.objects.create(
                supplier_time_to_process=24,
                vonq_time_to_process=24,
                supplier_setup_time=72,
                status=Product.Status.ACTIVE,
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )

            cls.product_2 = Product.objects.create(
                supplier_time_to_process=24,
                vonq_time_to_process=24,
                supplier_setup_time=711,
                status=Product.Status.ACTIVE,
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )

            cls.product_3 = Product.objects.create(
                supplier_time_to_process=48,
                vonq_time_to_process=0,
                supplier_setup_time=2,
                status=Product.Status.ACTIVE,
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )

    def test_total_time_to_process_should_return_404_if_one_product_id_is_nonexistent(
        self,
    ):
        self.assertEqual(
            self.client.get(
                reverse(
                    self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                    kwargs={"product_ids": 1234},
                )
            ).status_code,
            404,
        )

        self.assertEqual(
            self.client.get(
                reverse(
                    self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                    kwargs={"product_ids": f"1234,{self.product_1.product_id}"},
                )
            ).status_code,
            404,
        )

    def test_returns_200_when_requesting_delivery_time_for_active_products(self):
        self.assertEqual(
            self.client.get(
                reverse(
                    self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                    kwargs={
                        "product_ids": f"{self.product_1.product_id},{self.product_2.product_id}"
                    },
                ),
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                    kwargs={"product_ids": f"{self.product_3.product_id}"},
                )
            ).status_code,
            200,
        )

    def test_returns_correct_total_processing_time_as_ceiled_max_processing_time_of_all_products(
        self,
    ):
        products_list = self.client.get(
            reverse(
                "api.products:products-multiple",
                kwargs={
                    "product_ids": f"{self.product_1.product_id},{self.product_1.product_id}"
                },
            )
        ).json()

        max_processing_time_in_hours = max(
            products_list["results"][0]["time_to_process"]["period"],
            products_list["results"][0]["time_to_process"]["period"],
        )

        delivery_time_response = self.client.get(
            reverse(
                self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                kwargs={
                    "product_ids": f"{self.product_1.product_id},{self.product_2.product_id}"
                },
            ),
        ).json()

        self.assertEqual(
            delivery_time_response["days_to_process"],
            ceil(max_processing_time_in_hours / 24),
        )

    def test_returns_correct_total_setup_time_as_ceiled_max_setup_time_of_all_products(
        self,
    ):
        delivery_time_response = self.client.get(
            reverse(
                self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                kwargs={
                    "product_ids": f"{self.product_2.product_id},{self.product_3.product_id}"
                },
            ),
        ).json()

        self.assertEqual(
            delivery_time_response["days_to_setup"],
            ceil((711 + 2) / 24),
        )

    def test_returns_correct_total_delivery_time_as_sum_of_days_to_process_and_setup(
        self,
    ):
        delivery_time_response = self.client.get(
            reverse(
                self.PRODUCTS_DELIVERY_TIME_VIEWNAME,
                kwargs={
                    "product_ids": f"{self.product_2.product_id},{self.product_3.product_id}"
                },
            ),
        ).json()

        self.assertEqual(
            delivery_time_response["total_days"],
            delivery_time_response["days_to_process"]
            + delivery_time_response["days_to_setup"],
        )
