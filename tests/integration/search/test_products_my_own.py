from django.test import tag
from rest_framework.reverse import reverse

from api.tests.integration import force_user_login
from api.tests.integration.search import SearchTestCase

from api.products.models import Location, Product
from api.products.search.index import ProductIndex


@tag("algolia")
@tag("integration")
class MyOwnProductsTestCase(SearchTestCase):
    model_index_class_pairs = [(Product, ProductIndex)]

    @classmethod
    def setUpTestData(cls) -> None:

        # populate product locations
        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            canonical_name="UK",
        )
        united_kingdom.save()

        cls.my_own_product = Product.objects.create(
            status=Product.Status.ACTIVE,
            available_in_jmp=True,
            title="Own Product available in JMP",
            salesforce_id="available_jmp_product_1",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=90,
            customer_id="f17d9484-b9ba-5262-8f8e-b986e4b8c79d",
        )

        cls.my_own_product.locations.add(united_kingdom)
        cls.my_own_product.save()

        cls.not_my_own_product = Product.objects.create(
            status=Product.Status.ACTIVE,
            available_in_jmp=True,
            product_id="2",
            title="Product available in JMP",
            salesforce_id="available_jmp_product_2",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=90,
        )

    def test_cannot_see_my_own_products_in_list_view(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(reverse("api.products:products-list"))
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Product available in JMP")

    def test_can_see_product_when_searching(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?customerId=f17d9484-b9ba-5262-8f8e-b986e4b8c79d"
        )
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Own Product available in JMP")

    def test_can_see_product_in_detail_view(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.my_own_product.product_id},
            )
        )
        self.assertTrue(resp.status_code == 200)

    def test_can_see_product_in_multiple_view(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-multiple",
                kwargs={
                    "product_ids": f"{self.my_own_product.product_id},{self.not_my_own_product.product_id}"
                },
            )
        )
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(len(resp.json()["results"]), 2)

    def test_can_see_customer_id_in_response(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.my_own_product.product_id},
            )
        )
        self.assertTrue("customer_id" in resp.json())
        self.assertEqual(self.my_own_product.customer_id, resp.json()["customer_id"])

    def test_my_own_product_is_not_recommended(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse("api.products:products-list") + f"?recommended=true"
        )
        results = resp.json()["results"]
        self.assertEqual(1, len(results))
        self.assertEqual("Product available in JMP", results[0]["title"])
