from django.test import tag
from django.urls import reverse

from api.products.models import Location, Product, Channel
from api.products.search.index import ProductIndex
from api.tests.integration.search import SearchTestCase


@tag("algolia")
@tag("integration")
class ProductSearchByTextTest(SearchTestCase):
    model_index_class_pairs = [
        (Product, ProductIndex),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        Product.objects.create(
            title="Reddit - job ad",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        Product.objects.create(
            title="Efinancialcareers - job credit",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        Product.objects.create(
            title="Linkedin - Job posting",
            status=Product.Status.ACTIVE,
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
            status=Product.Status.ACTIVE,
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

    def test_ignores_all_filters_when_searching_by_name(self):
        products = self.client.get(
            reverse("api.products:products-list")
            + f"?name=linkedin&includeLocationId=123&jobFunctionId=234"
        ).json()["results"]
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["title"], "Linkedin - Job posting")
        self.assertEqual(products[1]["title"], "Linkfinance - basic posting")


class MatchingChannelTitleNameTestCase(SearchTestCase):
    model_index_class_pairs = [
        (Product, ProductIndex),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.jobboost = Channel.objects.create(name="JobBoost.io")

        cls.joblift = Channel.objects.create(name="Joblift | Germany")

        cls.socialmedia = Channel.objects.create(name="Social Media")

        cls.medienjobs = Channel.objects.create(name="Medien Jobs | Austria")

        cls.boost_product = Product.objects.create(
            # Joblift | Germany - Job boost
            title="Job boost",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.joblift.id,
        )

        cls.different_product = Product.objects.create(
            # JobBoost.io - Sponsored Job
            title="Sponsored Job",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.jobboost.id,
        )

        cls.socialmedia_product = Product.objects.create(
            # Social Media - Sponsored Job Ad
            title="Sponsored Job Ad",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.socialmedia.id,
        )

        cls.medien_product = Product.objects.create(
            # Medien Jobs | Austria - Social Media Package
            title="Social Media Package",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.medienjobs.id,
        )

    def test_channel_name_is_higher_priority(self):
        products = self.client.get(
            reverse("api.products:products-list") + f"?name=jobboost"
        ).json()["results"]

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["title"], "JobBoost.io - Sponsored Job")
        self.assertEqual(products[1]["title"], "Joblift | Germany - Job boost")


class TitleDescriptionTestCase(SearchTestCase):
    model_index_class_pairs = [
        (Product, ProductIndex),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.linkedin = Channel.objects.create(name="Linkedin")
        cls.jobboost = Channel.objects.create(name="JobBoost.io")
        cls.medienjobs = Channel.objects.create(name="Medien Jobs")

        cls.linkedin_product = Product.objects.create(
            title="Linkedin",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.linkedin.id,
        )

        cls.jobboost_product = Product.objects.create(
            # JobBoost.io - Sponsored Job
            title="JobBoost",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.jobboost.id,
        )

        cls.medien_product = Product.objects.create(
            # Medien Jobs | Austria - Social Media Package
            title="Social Media Package",
            status=Product.Status.ACTIVE,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            channel_id=cls.medienjobs.id,
            description="This description contains the word Linkedin, but not in the title",
        )

    def test_name_search_can_match_descriptions(self):
        products = self.client.get(
            reverse("api.products:products-list") + f"?name=linkedin"
        ).json()["results"]

        # should match cls.linkedin_product (first) and cls.medien_product (second)
        self.assertEqual(2, len(products))

        self.assertEqual("Linkedin - Linkedin", products[0]["title"])
        self.assertEqual("Medien Jobs - Social Media Package", products[1]["title"])
