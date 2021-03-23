import random
import time
from unittest import skip

from algoliasearch_django import algolia_engine
from django.conf import settings
from django.test import override_settings, tag
from rest_framework.reverse import reverse

from api.products.search.index import JobTitleIndex, ProductIndex
from api.products.models import (
    Product,
    Industry,
    Location,
    JobFunction,
    JobTitle,
    Channel,
)

from api.vonqtaxonomy.models import (
    JobCategory as VonqJobCategory,
    Industry as VonqIndustry,
)

from api.tests import AuthenticatedTestCase
from django.contrib.auth import get_user_model

from api.products.geocoder import MAPBOX_INTERNATIONAL_PLACE_TYPE

NOW = int(time.time())
TEST_INDEX_SUFFIX = f"test_{NOW}"


def how_many_products_with_value(
    product_search_response, key: str, values: tuple, name_key="id"
):
    count = 0
    for product in product_search_response["results"]:
        for item in product[key]:
            if item[name_key] in values:
                count += 1
    return count


def is_generic_product(product: dict) -> bool:
    return (
        0 == len(product["industries"])
        or any((industry["name"] == "Generic" for industry in product["industries"]))
        and 0 == len(product["job_functions"])
    )


INTERNATIONAL_LOCATION_NAME = "International"


def is_international_product(product: dict) -> bool:
    return 0 == len(product["locations"]) or any(
        (
            INTERNATIONAL_LOCATION_NAME == location["canonical_name"]
            for location in product["locations"]
        )
    )


@tag("algolia")
@tag("integration")
class ProductSearchTestCase(AuthenticatedTestCase):
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

        if not algolia_engine.is_registered(JobTitle):
            algolia_engine.register(JobTitle, JobTitleIndex)
            algolia_engine.reindex_all(JobTitle)

        pkb_industry = VonqIndustry.objects.create(mapi_id=1, name="Something")

        # populate industries
        cls.construction_industry = Industry(
            name_en="Construction",
            name_de="Konstruktion",
            name_nl="bouw",
            vonq_taxonomy_value_id=pkb_industry.id,
        )
        cls.construction_industry.save()

        cls.engineering_industry = Industry(
            name_en="Engineering",
            name_de="...engineering in german",
            name_nl="...engineering in dutch",
            vonq_taxonomy_value_id=pkb_industry.id,
        )
        cls.engineering_industry.save()

        cls.random_industry = Industry(
            name_en="Random",
            name_de="...random in german",
            name_nl="...random in dutch",
            vonq_taxonomy_value_id=pkb_industry.id,
        )
        cls.random_industry.save()

        cls.construction_board = Product(
            is_active=True,
            status="Negotiated",
            title="Construction board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.construction_board.save()
        cls.construction_board.industries.add(cls.construction_industry)
        cls.construction_board.save()

        low_duration_board = Product(
            is_active=True,
            status="Negotiated",
            title="Low duration board",
            duration_days=10,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        low_duration_board.save()

        cls.engineering_board = Product(
            is_active=True,
            status="Negotiated",
            title="Engineering Board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.engineering_board.save()
        cls.engineering_board.industries.add(cls.engineering_industry)
        cls.engineering_board.save()

        cls.general_board = Product(
            is_active=True,
            status="Negotiated",
            title="General",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=20,
        )
        cls.general_board.save()
        cls.general_board.industries.set(
            [cls.engineering_industry, cls.construction_industry]
        )
        cls.general_board.save()

        cls.null_board = Product(
            is_active=True,
            status="Negotiated",
            title="Null",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=30,
        )
        cls.null_board.save()

        cls.active_product = Product(
            is_active=True,
            status="Negotiated",
            salesforce_id="active_product",
            title="Negotiated product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=40,
        )
        cls.active_product.save()

        cls.inactive_product = Product(
            is_active=False,
            status="Negotiated",
            salesforce_id="inactive_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.inactive_product.save()

        cls.available_in_jmp_product = Product(
            is_active=True,
            status="Trial",
            available_in_jmp=True,
            title="Product available in JMP",
            salesforce_id="available_jmp_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=90,
        )
        cls.available_in_jmp_product.save()

        cls.unavailable_in_jmp_product = Product(
            is_active=True,
            status="Trial",
            available_in_jmp=False,
            salesforce_id="unavailable_jmp_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.unavailable_in_jmp_product.save()

        cls.unwanted_status_product = Product(
            is_active=True,
            status="Blacklisted",
            salesforce_id="unwanted_status_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.unwanted_status_product.save()

        # populate product locations
        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            canonical_name="UK",
            # "continent" here only serves to allow test assertions
            # on sorting to work deterministically here
            mapbox_context=["continent.europe", "global"],
            # note that there is no "global" context for those...
        )
        united_kingdom.save()
        cls.united_kingdom_id = united_kingdom.id

        england = Location(
            mapbox_id="region.13483278848453920",
            canonical_name="England",
            mapbox_context=["country.12405201072814600", "continent.europe", "global"],
        )
        england.save()
        cls.england_id = england.id

        reading = Location(
            mapbox_id="place.12006143788019830",
            canonical_name="Reading",
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
            canonical_name="Slough",
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
            # global has a specific mapbox place type to allow searching just for it
            canonical_name=INTERNATIONAL_LOCATION_NAME,
            mapbox_place_type=[MAPBOX_INTERNATIONAL_PLACE_TYPE],
            mapbox_context=[],
        )
        global_location.save()
        cls.global_id = global_location.id

        product = Product(
            is_active=True,
            title="Something in the whole of the UK",
            url="https://vonq.com/somethinglkasjdfhg",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product.save()
        product.locations.add(united_kingdom)
        product.save()

        product2 = Product(
            is_active=True,
            title="Something in Reading",
            url="https://vonq.com/something",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product2.save()
        product2.locations.add(reading)
        product2.save()

        product3 = Product(
            is_active=True,
            title="Something in Slough",
            url="https://vonq.com/something2",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product3.save()
        product3.locations.add(slough)
        product3.save()

        product4 = Product(
            is_active=True,
            title="Something in Slough and Reading",
            url="https://vonq.com/something4",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        product4.save()
        product4.locations.set([slough, reading])
        product4.save()

        global_product = Product(
            is_active=True,
            title="Something Global",
            url="https://vonq.com/somethingGlobal",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        global_product.save()
        global_product.locations.add(global_location)
        global_product.save()

        # populate job functions

        pkb_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Whatever")

        software_engineering = JobFunction(
            name="Software Engineering", vonq_taxonomy_value_id=pkb_job_category.id
        )
        software_engineering.save()

        construction = JobFunction(
            name="Construction", vonq_taxonomy_value_id=pkb_job_category.id
        )
        construction.save()

        cls.software_engineering_id = software_engineering.id

        cls.web_development = JobFunction.objects.create(
            name="Web Development",
            parent_id=software_engineering.id,
            vonq_taxonomy_value_id=pkb_job_category.id,
        )

        python_developer = JobTitle(
            name="Python Developer",
            job_function_id=software_engineering.id,
            canonical=True,
        )
        python_developer.save()
        cls.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer",
            job_function_id=software_engineering.id,
            canonical=True,
        )
        java_developer.save()
        cls.java_developer_id = java_developer.id

        product1 = Product(
            is_active=True,
            title="A job board for developers",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product1.save()
        product1.job_functions.add(software_engineering)
        product1.save()

        product1_but_global = Product(
            is_active=True,
            title="A global job board for developers",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product1_but_global.save()
        product1_but_global.locations.add(global_location)
        product1_but_global.job_functions.add(software_engineering)
        product1_but_global.save()

        product2 = Product(
            is_active=True,
            status="Trial",
            title="A job board for construction jobs",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product2.save()
        product2.job_functions.add(construction)
        product2.save()

        web_development_board = Product.objects.create(
            is_active=True,
            title="A board for web developers",
            url="https://something.int/webDev",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        web_development_board.job_functions.add(cls.web_development)
        web_development_board.save()

        # Frequency tests

        cls.recruitment_industry = Industry(
            name_en="Recruitment", vonq_taxonomy_value_id=pkb_industry.id
        )
        cls.recruitment_industry.save()

        cls.brazil = Location(
            mapbox_id="country.123",
            mapbox_text="BR",
            mapbox_context=["continent.south_america"],
        )
        cls.brazil.save()

        high_frequency_product = Product(
            title="frequency 1",
            is_active=True,
            salesforce_id="high",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.9,
        )
        high_frequency_product.save()

        high_frequency_product.industries.add(cls.recruitment_industry)
        high_frequency_product.save()

        medium_frequency_product = Product(
            title="frequency 2",
            is_active=True,
            salesforce_id="medium",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.6,
        )
        medium_frequency_product.save()
        medium_frequency_product.locations.add(cls.brazil)
        medium_frequency_product.industries.add(cls.recruitment_industry)
        medium_frequency_product.save()

        low_frequency_product = Product(
            title="frequency 3",
            is_active=True,
            salesforce_id="low",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.1,
        )
        low_frequency_product.save()
        low_frequency_product.industries.add(cls.recruitment_industry)
        low_frequency_product.locations.add(cls.brazil)
        low_frequency_product.save()

        # Light recommendations

        jobboard_channel = Channel(type=Channel.Type.JOB_BOARD)
        jobboard_channel.save()
        community_channel = Channel(type=Channel.Type.COMMUNITY)
        community_channel.save()
        publication_channel = Channel(type=Channel.Type.PUBLICATION)
        publication_channel.save()
        social_channel = Channel(type=Channel.Type.SOCIAL_MEDIA)
        social_channel.save()

        my_own_product = Product(
            title="my_own_product",
            is_active=True,
            salesforce_id="my_own_product",
            customer_id="f17d9484-b9ba-5262-8f8e-b986e4b8c79d",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            salesforce_product_solution=Product.SalesforceProductSolution.MY_OWN_CHANNEL,
            salesforce_product_category=Product.SalesforceProductCategory.CUSTOMER_SPECIFIC,
        )
        my_own_product.save()
        not_my_own_product = Product(
            title="not_my_own_product",
            is_active=True,
            salesforce_id="not_my_own_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            salesforce_product_solution=Product.SalesforceProductSolution.JOB_MARKETING,
            salesforce_product_category=Product.SalesforceProductCategory.GENERIC,
        )
        not_my_own_product.save()

        for channel in [
            jobboard_channel,
            community_channel,
            publication_channel,
            social_channel,
        ]:
            for i in range(0, 3):
                recommended_product = Product(
                    title=f"recommendation {channel.type} {i}",
                    is_active=True,
                    salesforce_id=f"recommendation {channel.type} {i}",
                    order_frequency=0.1 * i,
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                )

                recommended_product.save()
                recommended_product.channel = channel
                recommended_product.save()

        # it takes up to four seconds to actually reindex stuff
        time.sleep(4)

    def setUp(self) -> None:
        super().setUp()
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
        algolia_engine.client.delete_index(
            f"{JobTitleIndex.index_name}_{TEST_INDEX_SUFFIX}"
        )
        algolia_engine.reset(settings.ALGOLIA)

    def test_mapi_does_not_receive_my_own_products_by_default(self):
        User = get_user_model()
        mapi_user = User.objects.create(username="mapi", password="test")
        mapi_user.profile.type = "mapi"
        self.client.force_login(mapi_user)
        resp = self.client.get(reverse("api.products:products-list") + f"?name=own")
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "not_my_own_product")

    def test_jmp_does_not_receive_my_own_products_by_default(self):
        User = get_user_model()
        jmp_user = User.objects.create(username="jmp", password="test")
        jmp_user.profile.type = "jmp"
        self.client.force_login(jmp_user)
        resp = self.client.get(reverse("api.products:products-list") + f"?name=own")
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "not_my_own_product")

    def test_jmp_can_retrieve_my_own_products_with_customer_id(self):
        User = get_user_model()
        jmp_user = User.objects.create(username="jmp", password="test")
        jmp_user.profile.type = "jmp"
        self.client.force_login(jmp_user)
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?customerId=f17d9484-b9ba-5262-8f8e-b986e4b8c79d"
        )
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "my_own_product")

    def test_my_own_products_are_hidden_when_no_parameters(self):
        User = get_user_model()
        jmp_user = User.objects.create(username="jmp", password="test")
        jmp_user.profile.type = "jmp"
        self.client.force_login(jmp_user)
        resp = self.client.get(reverse("api.products:products-list"))
        results = resp.json()["results"]
        product_titles = [result["title"] for result in results]
        self.assertFalse("my_own_product" in product_titles)

    def test_can_recommend_products(self):
        def get_number_of_products_for_channel_type(response, channel_type):
            return len([r for r in response if r["channel"]["type"] == channel_type])

        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?name=recommendation&recommended=true"
        )
        response = resp.json()["results"]

        self.assertEqual(
            get_number_of_products_for_channel_type(response, Channel.Type.COMMUNITY), 2
        )
        self.assertEqual(
            get_number_of_products_for_channel_type(
                response, Channel.Type.SOCIAL_MEDIA
            ),
            2,
        )
        self.assertEqual(
            get_number_of_products_for_channel_type(response, Channel.Type.PUBLICATION),
            2,
        )
        # Only one because no products where created with job function (so none were categorized as niche)
        self.assertEqual(
            get_number_of_products_for_channel_type(response, Channel.Type.JOB_BOARD), 1
        )

    def test_all_products_are_sorted_by_order_frequency(self):
        def get_order_frequency(product_id):
            return (
                Product.objects.all()
                .filter(product_id=product_id)
                .first()
                .order_frequency
            )

        resp = self.client.get(reverse("api.products:products-list"))
        response = resp.json()["results"]

        for i in range(0, len(response) - 1):
            self.assertTrue(
                get_order_frequency(response[i]["product_id"])
                >= get_order_frequency(response[i + 1]["product_id"])
            )

    def test_can_prioritize_products_with_higher_order_frequency(self):
        resp = self.client.get(
            reverse("api.products:products-list") + f"?name=frequency"
        )
        response = resp.json()["results"]
        self.assertEqual(len(response), 3)
        self.assertEqual(response[0]["product_id"], "high")
        self.assertEqual(response[1]["product_id"], "medium")
        self.assertEqual(response[2]["product_id"], "low")

    def test_order_frequency_rank_does_not_outweigh_filters(self):
        """
        The product with the highest frequency only contains one of the filters, while the other two have both.
        We expect the ones that match both filters to appear first (ordered by frequency), followed by the product that
        only matches one filter.
        """
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?name=frequency&includeLocationId={self.brazil.id}&industryId={self.recruitment_industry.id}"
        )
        response = resp.json()["results"]

        self.assertEqual(len(response), 3)

        # TODO fix
        self.assertEqual(response[0]["product_id"], "medium")
        self.assertEqual(response[1]["product_id"], "low")
        self.assertEqual(response[2]["product_id"], "high")

    def test_can_fetch_all_industries(self):
        resp = self.client.get(reverse("api.products:industries-list"))
        self.assertEqual(len(resp.json()), 4)

    def test_can_filter_products_by_industry_id(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id}&limit=50"
        )

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "industries",
                (self.construction_industry.id,),
            ),
            2,
        )

        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id},{self.engineering_industry.id}&limit=50"
        )
        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "industries",
                (self.construction_industry.id, self.engineering_industry.id),
            ),
            4,
        )

    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.reading_id}"
        )

        self.assertEquals(resp.status_code, 200)
        correct_locations = {"Reading", "England", "UK", INTERNATIONAL_LOCATION_NAME}

        for product in resp.json()["results"]:
            product_locations = set(
                [location["canonical_name"] for location in product["locations"]]
            )
            # skip comparing products with no locations
            if not product_locations:
                continue
            self.assertTrue(product_locations & correct_locations)

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.england_id}"
        )

        self.assertEquals(resp.status_code, 200)
        correct_locations = {
            "Reading",
            "Slough",
            "England",
            "UK",
            INTERNATIONAL_LOCATION_NAME,
        }

        for product in resp.json()["results"]:
            product_locations = set(
                [location["canonical_name"] for location in product["locations"]]
            )
            if not product_locations:
                continue
            self.assertTrue(product_locations & correct_locations)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        self.assertEquals(resp.status_code, 200)

        for product in resp.json()["results"]:
            product_locations = set(
                [location["canonical_name"] for location in product["locations"]]
            )
            if not product_locations:
                continue
            self.assertTrue(product_locations & correct_locations)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.slough_id},{self.reading_id}"
        )

        for product in resp.json()["results"]:
            product_locations = set(
                [location["canonical_name"] for location in product["locations"]]
            )
            if not product_locations:
                continue
            self.assertTrue(product_locations & correct_locations)

    def test_return_all_products_with_no_locations(self):
        resp = self.client.get(reverse("api.products:products-list"))
        self.assertEquals(len(resp.json()["results"]), 25)

    def test_products_conform_to_required_specification(self):
        resp = self.client.get(reverse("api.products:products-list"))
        result = resp.json()["results"][0]

        self.assertCountEqual(
            result.keys(),
            [
                "title",
                "locations",
                "job_functions",
                "industries",
                "description",
                "homepage",
                "logo_url",
                "duration",
                "time_to_process",
                "product_id",
                "vonq_price",
                "ratecard_price",
                "type",
                "cross_postings",
                "channel",
                "logo_square_url",
                "logo_rectangle_url",
                "audience_group",
            ],
        )

    def test_products_with_global_locations(self):
        resp_global = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.global_id}"
        )
        all_products_are_global = all(
            is_international_product(product)
            for product in resp_global.json()["results"]
        )

        self.assertEquals(resp_global.status_code, 200)
        self.assertTrue(len(resp_global.json()["results"]) > 0)
        self.assertTrue(all_products_are_global)

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

    def test_can_search_by_inclusive_location(self):
        resp_one = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        # 1 UK product, 20 global products
        # TODO fix
        self.assertEqual(resp_one.json()["count"], 21)

    def test_can_search_by_exact_location(self):
        only_filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?exactLocationId={self.reading_id}"
        )
        self.assertEqual(only_filtered_response.json()["count"], 2)

    # TODO figure out logic when includeLocationId and exactLocationId are both included
    @skip
    def test_can_narrow_included_location_by_exact_location(self):
        filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}&exactLocationId={self.reading_id}"
        )
        # still 21, since the product for Reading
        # is already included in the UK-wide list
        self.assertEqual(filtered_response.json()["count"], 21)

        multiple_filtered_response = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
            f"&exactLocationId={self.reading_id},{self.slough_id}"
        )
        # since include and exact work on an OR fashion,
        # we get all the five results we already got for the UK
        # (since reading and slough are already in that result set)
        # TODO fix
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

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "job_functions",
                (self.software_engineering_id, self.web_development.id),
            ),
            3,
        )

    def test_product_search_can_filter_by_job_title(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobTitleId={self.python_developer_id}"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "job_functions",
                (self.software_engineering_id, self.web_development.id),
            ),
            3,
        )

    def test_product_search_cannot_filter_by_both_job_title_and_job_function(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobTitleId={self.python_developer_id}&jobFunctionId={self.software_engineering_id}"
        )
        self.assertEqual(resp.status_code, 400)

    def test_can_search_products_by_inclusive_job_function(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobFunctionId={self.software_engineering_id}"
        )

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "job_functions",
                (self.software_engineering_id, self.web_development.id),
            ),
            3,
        )

    def test_it_returns_available_products_in_jmp(self):
        User = get_user_model()
        user = User.objects.create(username="jmp", password="test")
        user.profile.type = "jmp"
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.available_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 200)

    def test_it_hides_unavailable_products_in_jmp(self):
        User = get_user_model()
        user = User.objects.create(username="jmp", password="test")
        user.profile.type = "jmp"
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.unavailable_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 404)

    def test_mapi_sees_jmp_products(self):
        User = get_user_model()
        mapi_user = User.objects.create(username="mapi", password="test")
        mapi_user.profile.type = "mapi"
        self.client.force_login(mapi_user)

        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.available_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 200)

        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.unavailable_in_jmp_product.product_id},
            )
        )

        self.assertEquals(resp.status_code, 404)

    def test_can_validate_existing_product_ids(self):
        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=[1, 2, 3],
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 403)

        User = get_user_model()
        mapi_user = User.objects.create(username="mapi", password="test")
        mapi_user.profile.type = "mapi"
        self.client.force_login(mapi_user)

        # fetch list of products available for jmp
        resp = self.client.get(reverse("api.products:products-list"))
        product_ids_available_in_mapi = [
            product["product_id"] for product in resp.json()["results"]
        ]

        random.sample(product_ids_available_in_mapi, 3)

        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=random.sample(product_ids_available_in_mapi, 3),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            reverse("api.products:products-validate"),
            data=random.sample(product_ids_available_in_mapi, 3)
            + [self.unavailable_in_jmp_product.product_id],
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 404)

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

    def test_can_search_for_product_name(self):
        resp = self.client.get(reverse("api.products:products-list") + f"?name=global")

        self.assertEqual(len(resp.json()["results"]), 2)

    def test_can_search_for_duration_from(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?durationFrom=20"
        )
        resp_json = resp.json()

        all_products_are_generic = all(
            [is_generic_product(product) for product in resp_json["results"]]
        )
        all_products_are_international = all(
            is_international_product(product) for product in resp_json["results"]
        )

        self.assertEqual(len(resp_json["results"]), 3)
        self.assertTrue(all_products_are_generic)
        self.assertTrue(all_products_are_international)

    def test_can_search_for_duration_to(self):
        resp = self.client.get(reverse("api.products:products-list") + "?durationTo=20")
        resp_json = resp.json()

        all_products_are_generic = all(
            [is_generic_product(product) for product in resp_json["results"]]
        )
        all_products_are_international = all(
            is_international_product(product) for product in resp_json["results"]
        )

        self.assertEqual(len(resp_json["results"]), 1)
        self.assertTrue(all_products_are_generic)
        self.assertTrue(all_products_are_international)

    def test_can_search_for_duration_boundaries(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?durationTo=90&durationFrom=40"
        )

        resp_json = resp.json()
        all_products_are_generic = all(
            [is_generic_product(product) for product in resp_json["results"]]
        )
        all_products_are_international = all(
            is_international_product(product) for product in resp_json["results"]
        )

        self.assertTrue(all_products_are_generic)
        self.assertTrue(all_products_are_international)


@tag("algolia")
@tag("integration")
class AddonSearchTestCase(AuthenticatedTestCase):
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

        addon_product_1 = Product.objects.create(
            title="This is an addon",
            salesforce_product_type=Product.SalesforceProductType.VONQ_SERVICES,
            is_active=True,
        )
        addon_product_1 = Product.objects.create(
            title="This is another addon",
            salesforce_product_type=Product.SalesforceProductType.IMAGE_CREATION,
            is_active=True,
        )

        proper_product = Product.objects.create(
            title="This is a product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            is_active=True,
        )

        proper_product2 = Product.objects.create(
            title="This is another product",
            salesforce_product_type=Product.SalesforceProductType.SOCIAL,
            is_active=True,
        )

        internal_product = Product.objects.create(
            title="Internal product",
            salesforce_product_type=Product.SalesforceProductType.FINANCE,
            is_active=True,
        )

        other_interal_product = Product.objects.create(
            title="Another internal product",
            salesforce_product_type=Product.SalesforceProductType.OTHER,
            is_active=True,
        )

        time.sleep(4)

    @classmethod
    @override_settings(
        ALGOLIA={
            "INDEX_SUFFIX": TEST_INDEX_SUFFIX,
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

    def test_can_list_all_products(self):
        resp = self.client.get(reverse("api.products:products-list"))
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertTrue(
            all(["product" in product["title"] for product in resp.json()["results"]])
        )

    def test_can_list_all_addons(self):
        resp = self.client.get(reverse("api.products:addons-list"))
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertTrue(
            all(["addon" in product["title"] for product in resp.json()["results"]])
        )


@tag("algolia")
@tag("integration")
class ChannelTypeSearchTestCase(AuthenticatedTestCase):
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

        jobboard_channel = Channel.objects.create(type=Channel.Type.JOB_BOARD)
        community_channel = Channel.objects.create(type=Channel.Type.COMMUNITY)
        publication_channel = Channel.objects.create(type=Channel.Type.PUBLICATION)

        job_board = Product.objects.create(
            title="This is a job board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            is_active=True,
            status="Negotiated",
            channel_id=jobboard_channel.id,
        )
        community_product = Product.objects.create(
            title="This is a community product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status="Negotiated",
            is_active=True,
            channel_id=community_channel.id,
        )

        publication_product = Product.objects.create(
            title="This is a publication product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status="Negotiated",
            is_active=True,
            channel_id=publication_channel.id,
        )

        time.sleep(4)

    def setUp(self) -> None:
        super().setUp()

    @classmethod
    @override_settings(
        ALGOLIA={
            "INDEX_SUFFIX": TEST_INDEX_SUFFIX,
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

    def test_can_filter_by_channel_type(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?channelType=job%20board"
        )
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertEqual(resp.json()["results"][0]["title"], "This is a job board")
