import time

from algoliasearch_django import algolia_engine
from django.test import TestCase, override_settings, tag
from django.conf import settings
from rest_framework.reverse import reverse

from api.products.index import ProductIndex
from api.products.models import Product, Industry, Location, JobFunction, JobTitle

NOW = int(time.time())
TEST_INDEX_SUFFIX = f"test_{NOW}"


@tag("algolia")
@tag("integration")
class ProductSearchTestCase(TestCase):
    """
    We need to gather all the product-search related tests into
    this one class, as we're hitting the live algolia index.
    This means that we need to create the index and populate
    it with test entities. This might take quite some time,
    and it's infeasible to do it on a setUp method.
    """

    @classmethod
    @override_settings(
        ALGOLIA={
            "INDEX_SUFFIX": TEST_INDEX_SUFFIX,
            "APPLICATION_ID": settings.ALGOLIA["APPLICATION_ID"],
            "API_KEY": settings.ALGOLIA["API_KEY"],
            "AUTO_INDEXING": True,
        }
    )
    def setUpClass(cls):
        super().setUpClass()
        algolia_engine.reset(settings.ALGOLIA)
        if not algolia_engine.is_registered(Product):
            algolia_engine.register(Product, ProductIndex)
            algolia_engine.reindex_all(Product)

        # populate industries
        cls.construction_industry = Industry(
            name_en="Construction", name_de="Konstruktion", name_nl="bouw"
        )
        cls.construction_industry.save()

        cls.engineering_industry = Industry(
            name_en="Engineering",
            name_de="...engineering in german",
            name_nl="...engineering in dutch",
        )
        cls.engineering_industry.save()

        cls.construction_board = Product(title="Construction board")
        cls.construction_board.save()
        cls.construction_board.industries.add(cls.construction_industry)
        cls.construction_board.save()

        cls.engineering_board = Product(title="Engineering Board")
        cls.engineering_board.save()
        cls.engineering_board.industries.add(cls.engineering_industry)
        cls.engineering_board.save()

        cls.general_board = Product(title="General")
        cls.general_board.save()
        cls.general_board.industries.set(
            [cls.engineering_industry, cls.construction_industry]
        )
        cls.general_board.save()

        cls.null_board = Product(title="Null")
        cls.null_board.save()

        # populate product locations
        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            # "continent" here only serves to allow test assertions
            # on sorting to work deterministically here
            mapbox_context=["continent.europe", "global"],
            # note that there is no "global" context for those...
        )
        united_kingdom.save()
        cls.united_kingdom_id = united_kingdom.id

        england = Location(
            mapbox_id="region.13483278848453920",
            mapbox_text="England",
            mapbox_context=["country.12405201072814600", "continent.europe", "global"],
        )
        england.save()
        cls.england_id = england.id

        reading = Location(
            mapbox_id="place.12006143788019830",
            mapbox_text="Reading",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
                "global",
            ],
        )
        reading.save()
        cls.reading_id = reading.id

        slough = Location(
            mapbox_id="place.17224449158261700",
            mapbox_text="Slough",
            mapbox_context=[
                "district.11228968263261700",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
                "global",
            ],
        )
        slough.save()
        cls.slough_id = slough.id

        global_location = Location(
            # global has a specific name to allow searching just for it
            mapbox_id="global",
            mapbox_text="global",
            mapbox_context=[],
        )
        global_location.save()
        cls.global_id = global_location.id

        product = Product(
            title="Something in the whole of the UK",
            url="https://vonq.com/somethinglkasjdfhg",
        )
        product.save()
        product.locations.add(united_kingdom)
        product.save()

        product2 = Product(
            title="Something in Reading", url="https://vonq.com/something"
        )
        product2.save()
        product2.locations.add(reading)
        product2.save()

        product3 = Product(
            title="Something in Slough", url="https://vonq.com/something2"
        )
        product3.save()
        product3.locations.add(slough)
        product3.save()

        product4 = Product(
            title="Something in Slough and Reading", url="https://vonq.com/something4"
        )

        product4.save()
        product4.locations.set([slough, reading])
        product4.save()

        global_product = Product(
            title="Something Global", url="https://vonq.com/somethingGlobal"
        )
        global_product.save()
        global_product.locations.add(global_location)
        global_product.save()

        # populate job functions
        software_engineering = JobFunction(name="Software Engineering",)
        software_engineering.save()

        construction = JobFunction(name="Construction")
        construction.save()

        cls.software_engineering_id = software_engineering.id

        python_developer = JobTitle(
            name="Python Developer", job_function_id=software_engineering.id
        )
        python_developer.save()
        cls.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer", job_function_id=software_engineering.id
        )
        java_developer.save()
        cls.java_developer_id = java_developer.id

        product = Product(title="A job board for developers",)
        product.save()
        product.job_functions.add(software_engineering)
        product.save()

        product2 = Product(title="A job board for construction jobs")
        product2.save()
        product2.job_functions.add(construction)
        product2.save()

        # it takes up to four seconds to actually reindex stuff
        time.sleep(4)

    def setUp(self) -> None:
        # populate mapbox locations contexts
        self.client.get(reverse("locations") + "?text=reading")
        self.client.get(reverse("locations") + "?text=england")
        self.client.get(reverse("locations") + "?text=slough")
        self.client.get(reverse("locations") + "?text=united%20kingdom")

    @classmethod
    @override_settings(
        ALGOLIA={
            "INDEX_SUFFIX": "test",
            "APPLICATION_ID": settings.ALGOLIA["APPLICATION_ID"],
            "API_KEY": settings.ALGOLIA["API_KEY"],
            "AUTO_INDEXING": True,
        }
    )
    def tearDownClass(cls):
        super().tearDownClass()
        algolia_engine.client.delete_index(
            f"{ProductIndex.index_name}_{TEST_INDEX_SUFFIX}"
        )
        algolia_engine.reset(settings.ALGOLIA)

    def test_can_fetch_all_industries(self):
        resp = self.client.get(reverse("api.products:industries-list"))
        self.assertEqual(len(resp.json()["results"]), 2)

    def test_can_filter_products_by_industry_id(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id}"
        )
        self.assertEqual(len(resp.json()["results"]), 2)

        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id},{self.engineering_industry.id}"
        )
        self.assertEqual(len(resp.json()["results"]), 3)

    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.reading_id}"
        )

        self.assertEquals(resp.status_code, 200)

        # must be 5, as we have product, product2, product3, product4, global
        self.assertEqual(len(resp.json()["results"]), 5)

        # the most specific location is at the top
        self.assertIn(
            resp.json()["results"][0]["title"],
            ["Something in Reading", "Something in Slough and Reading"],
        )

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.england_id}"
        )

        self.assertEquals(resp.status_code, 200)
        # they're 5, because now there's a "slough only" product
        self.assertEqual(len(resp.json()["results"]), 5)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 5)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.slough_id},{self.reading_id}"
        )
        self.assertEqual(len(resp.json()["results"]), 5)

    def test_return_all_products_with_no_locations(self):
        resp = self.client.get(reverse("api.products:products-list"))
        self.assertEquals(len(resp.json()["results"]), 11)

    def test_results_are_sorted_by_specificity(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        products = resp.json()["results"]
        self.assertTrue(len(products) > 1)

        # this is the board with the least context
        self.assertEqual(
            products[-1]["title"], "Something Global",
        )
        # these are the boards with the most specific context
        self.assertIn(
            products[0]["title"],
            [
                "Something in Reading",
                "Something in Slough",
                "Something in Slough and Reading",
            ],
        )

    def test_products_with_global_locations(self):
        resp_global = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.global_id}"
        )
        self.assertEquals(resp_global.status_code, 200)

        self.assertTrue(len(resp_global.json()["results"]) > 0)

        self.assertEquals(
            resp_global.json()["results"][-1]["title"], "Something Global"
        )

        # this is only supposed to return products for which we have a location
        # (4 products only have industries applied)
        self.assertEquals(len(resp_global.json()["results"]), 5)

    def test_products_can_offset_and_limit(self):
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

    def test_can_narrow_the_list_by_filter_by(self):
        resp_one = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        # five products, including global...
        self.assertEqual(resp_one.json()["count"], 5)

        filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}&exactLocationId={self.reading_id}"
        )
        # still five products, since the product for Reading
        # is already included in the UK-wide list
        self.assertEqual(filtered_response.json()["count"], 5)

        only_filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?exactLocationId={self.reading_id}"
        )
        self.assertEqual(only_filtered_response.json()["count"], 2)

        multiple_filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
            f"&exactLocationId={self.reading_id},{self.slough_id}"
        )
        # since include and exact work on an OR fashion,
        # we get all the five results we already got for the UK
        # (since reading and slough are already in that result set)
        self.assertEqual(multiple_filtered_response.json()["count"], 5)

        # sorted ranking:
        # the most relevant result satisfies filters for both exactLocation
        self.assertEqual(
            multiple_filtered_response.json()["results"][0]["title"],
            "Something in Slough and Reading",
        )
        # then we get two results where only one of the exactLocation match
        self.assertIn(
            multiple_filtered_response.json()["results"][1]["title"],
            ["Something in Slough", "Something in Reading"],
        )
        self.assertIn(
            multiple_filtered_response.json()["results"][2]["title"],
            ["Something in Reading", "Something in Slough"],
        )
        # then the results that match for the includeLocation and its context:
        # first the most specific
        self.assertEqual(
            multiple_filtered_response.json()["results"][3]["title"],
            "Something in the whole of the UK",
        )
        # ... and then the least specific
        self.assertEqual(
            multiple_filtered_response.json()["results"][4]["title"], "Something Global"
        )

    def test_product_search_can_filter_by_job_function(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobFunctionId={self.software_engineering_id}"
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.json()["results"]), 1)

    def test_product_search_can_filter_by_job_title(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobTitleId={self.python_developer_id}"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.json()["results"]), 1)

    def test_product_search_cannot_filter_by_both_job_title_and_job_function(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobTitleId={self.python_developer_id}&jobFunctionId={self.software_engineering_id}"
        )
        self.assertEqual(resp.status_code, 400)
