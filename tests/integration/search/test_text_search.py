from django.test import tag
from django.urls import reverse

from api.products.models import Product
from api.products.search.index import ProductIndex
from api.tests import SearchTestCase


@tag("algolia")
@tag("integration")
class ProductSearchByTextTest(SearchTestCase):
    model_index_class_pairs = [
        (Product, ProductIndex),
    ]

    @classmethod
    def setUpSearchClass(cls):
        Product.objects.create(
            title="Reddit - job ad",
            is_active=True,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        Product.objects.create(
            title="Efinancialcareers - job credit",
            is_active=True,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

    def test_allows_max_1_typo_for_5_characters(self):
        products = self.client.get(
            reverse("api.products:products-list") + f"?name=redit"
        ).json()["results"]

        self.assertEqual(products[0]["title"], "Reddit - job ad")

        products = self.client.get(
            reverse("api.products:products-list") + f"?name=redt"
        ).json()["results"]

        self.assertEqual(len(products), 0)

    def test_allows_max_2_typos_for_8_characters(self):
        products = self.client.get(
            reverse("api.products:products-list") + f"?name=efinacialcarers"
        ).json()["results"]

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["title"], "Efinancialcareers - job credit")

        products = self.client.get(
            reverse("api.products:products-list") + f"?name=efiacialcarers"
        ).json()["results"]

        self.assertEqual(len(products), 0)
