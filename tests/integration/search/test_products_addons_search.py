from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Product
from api.products.search.index import ProductIndex
from api.tests.integration.search import SearchTestCase


@tag("algolia")
@tag("integration")
class ProductsAddonSearchTestCase(SearchTestCase):
    model_index_class_pairs = [
        (
            Product,
            ProductIndex,
        ),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        addon_product_1 = Product.objects.create(
            title="This is an addon",
            salesforce_product_type=Product.SalesforceProductType.VONQ_SERVICES,
            status=Product.Status.ACTIVE,
        )
        addon_product_1 = Product.objects.create(
            title="This is another addon",
            salesforce_product_type=Product.SalesforceProductType.IMAGE_CREATION,
            status=Product.Status.ACTIVE,
        )

        proper_product = Product.objects.create(
            title="This is a product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
        )

        proper_product2 = Product.objects.create(
            title="This is another product",
            salesforce_product_type=Product.SalesforceProductType.SOCIAL,
            status=Product.Status.ACTIVE,
        )

        internal_product = Product.objects.create(
            title="Internal product",
            salesforce_product_type=Product.SalesforceProductType.FINANCE,
            status=Product.Status.ACTIVE,
        )

        other_interal_product = Product.objects.create(
            title="Another internal product",
            salesforce_product_type=Product.SalesforceProductType.OTHER,
            status=Product.Status.ACTIVE,
        )

    def test_can_list_all_products(self):
        resp = self.client.get(reverse("api.products:products-list"))
        # lists types of "other", "job board", "social"
        self.assertEqual(len(resp.json()["results"]), 3)
        self.assertTrue(
            all(["product" in product["title"] for product in resp.json()["results"]])
        )

    def test_can_list_all_addons(self):
        resp = self.client.get(reverse("api.products:addons-list"))
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertTrue(
            all(["addon" in product["title"] for product in resp.json()["results"]])
        )
