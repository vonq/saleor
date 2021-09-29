import random
from django.test import TestCase

from algoliasearch_django.decorators import disable_auto_indexing
from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Product
from api.products.serializers import ProductJmpSerializer, ProductSerializer
from api.tests.integration import force_user_login


@tag("integration")
class ProductsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        with disable_auto_indexing():
            cls.active_product = Product(
                status=Product.Status.ACTIVE,
                salesforce_id="active_product",
                title="Negotiated product",
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                duration_days=40,
            )
            cls.active_product.save()

            cls.inactive_product = Product(
                status="Disabled",
                salesforce_id="inactive_product",
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )
            cls.inactive_product.save()

            cls.available_in_jmp_product = Product(
                status=Product.Status.ACTIVE,
                available_in_jmp=True,
                available_in_ats=False,
                title="Product available in JMP",
                salesforce_id="available_jmp_product",
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                duration_days=90,
            )
            cls.available_in_jmp_product.save()

            cls.unavailable_in_jmp_product = Product(
                status=Product.Status.ACTIVE,
                available_in_jmp=False,
                salesforce_id="unavailable_jmp_product",
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )
            cls.unavailable_in_jmp_product.save()

            cls.unavailable_in_hapi_product = Product(
                status=Product.Status.ACTIVE,
                available_in_jmp=True,
                title="Product unavailable in HAPI",
                salesforce_id="unavailable_in_hapi_product",
                salesforce_product_type=Product.SalesforceProductType.FINANCE,
                duration_days=90,
            )
            cls.unavailable_in_hapi_product.save()

            cls.unwanted_status_product = Product(
                status=Product.Status.BLACKLISTED,
                salesforce_id="unwanted_status_product",
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            )
            cls.unwanted_status_product.save()

    def test_products_can_offset_and_limit(self):
        force_user_login(self.client, "internal")
        resp_one = self.client.get(reverse("api.products:products-list"))

        resp_two = self.client.get(reverse("api.products:products-list") + "?limit=1")

        resp_three = self.client.get(
            reverse("api.products:products-list") + "?limit=1&offset=2"
        )

        self.assertNotEqual(len(resp_one.json()["results"]), 1)
        self.assertEquals(len(resp_two.json()["results"]), 1)
        self.assertEquals(len(resp_three.json()["results"]), 1)
        self.assertNotEqual(
            resp_two.json()["results"][0]["title"],
            resp_three.json()["results"][0]["title"],
        )

    def test_returns_an_active_product(self):
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.active_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 200)

    def test_hides_an_inactive_product(self):
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.inactive_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 404)

    def test_hides_an_product_with_unwanted_status(self):
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.unwanted_status_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 404)

    def test_products_conform_to_required_specification(self):
        resp = self.client.get(reverse("api.products:products-list"))
        results = resp.json()["results"]
        serialized_products = ProductSerializer(data=results, many=True)
        self.assertTrue(serialized_products.is_valid())

    def test_products_conform_to_required_specification_when_user_type_is_jmp(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(reverse("api.products:products-list"))
        results = resp.json()["results"]
        serialized_products = ProductJmpSerializer(data=results, many=True)
        self.assertTrue(serialized_products.is_valid())

    def test_can_retrieve_multiple_products(self):
        resp = self.client.get(
            reverse(
                "api.products:products-multiple",
                kwargs={
                    "product_ids": f"{self.active_product.product_id},{self.available_in_jmp_product.product_id}"
                },
            )
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)

    def test_it_returns_available_products_in_jmp(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.available_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 200)

    def test_it_returns_jmp_products_to_unauthenticated_user(self):
        force_user_login(self.client, "jmp")
        jmp_resp = self.client.get(
            reverse(
                "api.products:products-list",
            )
        )

        self.client.logout()
        public_resp = self.client.get(reverse("api.products:products-list"))
        self.assertEqual(jmp_resp.json(), public_resp.json())

    def test_it_hides_unavailable_products_in_jmp(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.unavailable_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 404)

    def test_hapi_sees_only_products_available_in_ats(self):
        force_user_login(self.client, "mapi")

        resp = self.client.get(reverse("api.products:products-list"))
        products = resp.json()["results"]

        self.assertEqual(2, len(products))

    def test_hapi_can_see_jmp_board_products(self):
        force_user_login(self.client, "mapi")

        resp = self.client.get(reverse("api.products:products-list"))

        products = resp.json()["results"]
        self.assertTrue(
            self.unavailable_in_hapi_product.product_id not in [prod["product_id"]]
            for prod in products
        )

    def test_can_validate_existing_product_ids(self):
        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=[1, 2, 3],
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 404)

        force_user_login(self.client, "mapi")

        # fetch list of products available for jmp
        resp = self.client.get(reverse("api.products:products-list"))
        product_ids_available_in_hapi = [
            product["product_id"] for product in resp.json()["results"]
        ]

        random.sample(product_ids_available_in_hapi, 2)

        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=random.sample(product_ids_available_in_hapi, 2),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=random.sample(product_ids_available_in_hapi, 2)
            + [self.unwanted_status_product.product_id],
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 404)


@tag("integration")
class ProductsTimeToProcessTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product.objects.create(
            supplier_time_to_process=24,
            vonq_time_to_process=24,
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

    def test_total_time_to_process_should_sum_supplier_and_vonq_time_to_process(self):
        products = self.client.get(reverse("api.products:products-list")).json()[
            "results"
        ]
        self.assertEqual(products[0]["time_to_setup"]["range"], "hours")
        self.assertEqual(products[0]["time_to_process"]["period"], 48)
        self.assertEqual(products[0]["time_to_process"]["range"], "hours")
