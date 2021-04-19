from django.test import tag
from django.urls import reverse

from api.products.models import Location, Product
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

        #######################

        Product.objects.create(
            title="Linkedin - Job posting",
            is_active=True,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        england = Location(
            mapbox_id="region.13483278848453920",
            canonical_name="England",
            mapbox_context=["country.12405201072814600", "continent.europe", "global"],
        )
        england.save()
        linkfinance = Product(
            title="Linkfinance - basic posting",
            is_active=True,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        linkfinance.save()
        linkfinance.locations.add(england)
        linkfinance.save()

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

    def test_ranks_products_with_lower_specificity_higher_than_products_with_typos(
        self,
    ):
        products = self.client.get(
            reverse("api.products:products-list") + f"?name=linkedin"
        ).json()["results"]

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["title"], "Linkedin - Job posting")
        self.assertEqual(products[1]["title"], "Linkfinance - basic posting")
