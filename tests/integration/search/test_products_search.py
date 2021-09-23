from unittest import skip

from django.test import tag
from rest_framework.reverse import reverse

from api.products.geocoder import MAPBOX_INTERNATIONAL_PLACE_TYPE
from api.products.models import (
    Product,
    Industry,
    Location,
    JobFunction,
    JobTitle,
    Channel,
    Category,
)
from api.products.search.index import JobFunctionIndex, JobTitleIndex, ProductIndex
from api.tests.integration import force_user_login
from api.tests.integration.search import (
    how_many_products_with_value,
    is_generic_product,
    SearchTestCase,
)
from api.vonqtaxonomy.models import (
    JobCategory as VonqJobCategory,
    Industry as VonqIndustry,
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
class ProductSearchTestCase(SearchTestCase):
    model_index_class_pairs = [
        (
            Product,
            ProductIndex,
        ),
        (
            JobTitle,
            JobTitleIndex,
        ),
        (
            JobFunction,
            JobFunctionIndex,
        ),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
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
            status=Product.Status.ACTIVE,
            title="Construction board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.construction_board.save()
        cls.construction_board.industries.add(cls.construction_industry)
        cls.construction_board.save()

        low_duration_board = Product(
            status=Product.Status.ACTIVE,
            title="Low duration board",
            duration_days=10,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        low_duration_board.save()

        cls.engineering_board = Product(
            status=Product.Status.ACTIVE,
            title="Engineering Board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.engineering_board.save()
        cls.engineering_board.industries.add(cls.engineering_industry)
        cls.engineering_board.save()

        cls.general_board = Product(
            status=Product.Status.ACTIVE,
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
            status=Product.Status.ACTIVE,
            title="Null",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            duration_days=30,
        )
        cls.null_board.save()

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

        france = Location.objects.create(
            mapbox_id="country.19008108158641660",
            canonical_name="Omlette du fromage",
            mapbox_context=["continent.europe", "global"],
        )
        cls.france_id = france.id

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
            status=Product.Status.ACTIVE,
            title="Something in the whole of the UK",
            url="https://vonq.com/somethinglkasjdfhg",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product.save()
        product.locations.add(united_kingdom)
        product.save()

        product2 = Product(
            status=Product.Status.ACTIVE,
            title="Something in Reading",
            url="https://vonq.com/something",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product2.save()
        product2.locations.add(reading)
        product2.save()

        product3 = Product(
            status=Product.Status.ACTIVE,
            title="Something in Slough",
            url="https://vonq.com/something2",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product3.save()
        product3.locations.add(slough)
        product3.save()

        product4 = Product(
            status=Product.Status.ACTIVE,
            title="Something in Slough and Reading",
            url="https://vonq.com/something4",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        product4.save()
        product4.locations.set([slough, reading])
        product4.save()

        global_product = Product(
            status=Product.Status.ACTIVE,
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
            status=Product.Status.ACTIVE,
            title="A job board for developers",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product1.save()
        product1.job_functions.add(software_engineering)
        product1.save()

        product1_but_global = Product(
            status=Product.Status.ACTIVE,
            title="A global job board for developers",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product1_but_global.save()
        product1_but_global.locations.add(global_location)
        product1_but_global.job_functions.add(software_engineering)
        product1_but_global.save()

        product2 = Product(
            status=Product.Status.ACTIVE,
            title="A job board for construction jobs",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        product2.save()
        product2.job_functions.add(construction)
        product2.save()

        web_development_board = Product.objects.create(
            status=Product.Status.ACTIVE,
            title="A board for web developers",
            url="https://something.int/webDev",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        web_development_board.job_functions.add(cls.web_development)
        web_development_board.save()

        cls.french_board = Product.objects.create(
            status=Product.Status.ACTIVE,
            title="A job board for french developpeurs",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        cls.french_board.job_functions.add(software_engineering)
        cls.french_board.locations.add(france)
        cls.french_board.save()

        cls.uk_board = Product.objects.create(
            status=Product.Status.ACTIVE,
            title="A job board for english devs",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        cls.uk_board.job_functions.add(software_engineering)
        cls.uk_board.locations.add(united_kingdom)
        cls.uk_board.save()

        # my own products
        cls.my_own_product_1 = Product.objects.create(
            title="my_own_product",
            status=Product.Status.ACTIVE,
            salesforce_id="my_own_product",
            customer_id="f17d9484-b9ba-5262-8f8e-b986e4b8c79d",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )

        cls.my_own_product_2 = Product.objects.create(
            title="my_own_product",
            status=Product.Status.ACTIVE,
            salesforce_id="my_own_product_2",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            salesforce_product_solution=Product.SalesforceProductSolution.MY_OWN_CHANNEL,
        )

        cls.my_own_product_3 = Product.objects.create(
            title="my_own_product",
            status=Product.Status.ACTIVE,
            salesforce_id="my_own_product_3",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            salesforce_product_category=Product.SalesforceProductCategory.CUSTOMER_SPECIFIC,
        )

        cls.not_my_own_product = Product(
            title="not_my_own_product",
            status=Product.Status.ACTIVE,
            salesforce_id="not_my_own_product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            salesforce_product_solution=Product.SalesforceProductSolution.JOB_MARKETING,
            salesforce_product_category=Product.SalesforceProductCategory.GENERIC,
        )
        cls.not_my_own_product.save()

    def setUp(self) -> None:
        super().setUp()
        # populate mapbox locations contexts
        self.client.get(reverse("locations") + "?text=reading")
        self.client.get(reverse("locations") + "?text=england")
        self.client.get(reverse("locations") + "?text=slough")
        self.client.get(reverse("locations") + "?text=united%20kingdom")

    def test_can_define_mocs_correctly(self):
        self.assertTrue(
            all(
                (
                    self.my_own_product_1.is_my_own_product,
                    self.my_own_product_2.is_my_own_product,
                    self.my_own_product_3.is_my_own_product,
                )
            )
        )

        self.assertFalse(self.not_my_own_product.is_my_own_product)

    def test_mapi_does_not_receive_my_own_products_by_default(self):
        force_user_login(self.client, "mapi")
        resp = self.client.get(reverse("api.products:products-list") + f"?name=own")
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "not_my_own_product")

    def test_jmp_does_not_receive_my_own_products_by_default(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(reverse("api.products:products-list") + f"?name=own")
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "not_my_own_product")

    def test_jmp_can_retrieve_my_own_products_with_customer_id(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?customerId=f17d9484-b9ba-5262-8f8e-b986e4b8c79d"
        )
        results = resp.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "my_own_product")

    def test_my_own_products_are_hidden_when_no_parameters(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(reverse("api.products:products-list"))
        results = resp.json()["results"]
        product_titles = [result["title"] for result in results]
        self.assertFalse("my_own_product" in product_titles)

    def test_can_fetch_all_industries(self):
        resp = self.client.get(reverse("api.products:industries-list"))
        self.assertEqual(len(resp.json()), 3)

    def test_can_filter_products_by_industry_id(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id}&limit=50"
        )
        resp_json = resp.json()
        self.assertEqual(
            how_many_products_with_value(
                resp_json,
                "industries",
                (self.construction_industry.id,),
            ),
            2,
        )

        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?industryId={self.construction_industry.id},{self.engineering_industry.id}&limit=50"
        )
        resp_json = resp.json()

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "industries",
                (self.construction_industry.id, self.engineering_industry.id),
            ),
            3,
        )

        for product in resp_json["results"][:3]:
            self.assertFalse(is_generic_product(product))

        for product in resp_json["results"][3:]:
            self.assertTrue(is_generic_product(product))

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

    @tag("Requires review")
    @skip
    def test_return_all_products_with_no_locations(self):
        resp = self.client.get(reverse("api.products:products-list"))
        self.assertEquals(len(resp.json()["results"]), 18)

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

    def test_can_search_by_inclusive_location(self):
        resp_one = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        # 1 UK product, 8 global products
        self.assertEqual(resp_one.json()["count"], 8)

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

    @tag("PKB-631")
    def test_searching_by_job_function_and_location_does_not_return_products_from_other_locations(
        self,
    ):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobFunctionId={self.software_engineering_id}&includeLocationId={self.france_id}"
        )

        self.assertEqual(
            how_many_products_with_value(
                resp.json(),
                "job_functions",
                (self.software_engineering_id,),
            ),
            1,
        )
        self.assertEqual(
            how_many_products_with_value(
                resp.json(), "locations", (self.united_kingdom_id,)
            ),
            0,
        )

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

        # only generic and international boards get excluded
        self.assertEqual(len(resp_json["results"]), 1)
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
class ProductCategorySearchTestCase(SearchTestCase):
    model_index_class_pairs = [(Product, ProductIndex)]

    @classmethod
    def setUpTestData(cls) -> None:
        jobboard_channel = Channel.objects.create(type=Channel.Type.JOB_BOARD)
        community_channel = Channel.objects.create(type=Channel.Type.COMMUNITY)
        publication_channel = Channel.objects.create(type=Channel.Type.PUBLICATION)

        job_board = Product.objects.create(
            title="This is a job board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
            channel_id=jobboard_channel.id,
            unit_price=100,
        )
        community_product = Product.objects.create(
            title="This is a community product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
            channel_id=community_channel.id,
            unit_price=200,
        )

        publication_product = Product.objects.create(
            title="This is a publication product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
            channel_id=publication_channel.id,
            unit_price=300,
        )

        cls.senior_career_level = Category.objects.create(
            type=Category.Type.CAREER_LEVEL, name="senior"
        )
        cls.junior_career_level = Category.objects.create(
            type=Category.Type.CAREER_LEVEL, name="junior"
        )

        cls.permanent_job_type = Category.objects.create(
            type=Category.Type.JOB_TYPE,
            name="permanent",
        )

        cls.fixed_term_job_type = Category.objects.create(
            type=Category.Type.JOB_TYPE,
            name="fixed-term",
        )

        cls.permanent_job_board = Product.objects.create(
            title="A Permanent Job Board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
        )
        cls.permanent_job_board.categories.add(
            cls.permanent_job_type, cls.senior_career_level
        )
        cls.permanent_job_board.save()

        cls.fixed_term_job_poard = Product.objects.create(
            title="A Temporary Job Board",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
        )
        cls.fixed_term_job_poard.categories.add(
            cls.fixed_term_job_type, cls.junior_career_level
        )
        cls.fixed_term_job_poard.save()

    def test_can_filter_by_channel_type(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?channelType=job%20board"
        )
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertEqual(resp.json()["results"][0]["title"], "This is a job board")

    def test_can_filter_by_multiple_channel_type(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?channelType=job%20board,community"
        )
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEqual(
            resp.json()["results"][0]["title"], "This is a community product"
        )
        self.assertEqual(resp.json()["results"][1]["title"], "This is a job board")

    def test_cant_filter_by_invalid_channel_type(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + "?channelType=job%20board,randomstuff"
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual({"channelType": ["Invalid channel type!"]}, resp.json())

    def test_can_filter_by_career_level(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?seniorityId={self.senior_career_level.id}"
        )
        self.assertEqual(1, resp.json()["count"])
        self.assertEqual("A Permanent Job Board", resp.json()["results"][0]["title"])

    def test_can_filter_by_job_type(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?employmentTypeId={self.fixed_term_job_type.id}"
        )
        self.assertEqual(1, resp.json()["count"])
        self.assertEqual("A Temporary Job Board", resp.json()["results"][0]["title"])

    def test_can_filter_by_price(self):
        resp = self.client.get(
            reverse("api.products:products-list") + f"?priceFrom=200"
        )
        self.assertEqual(2, resp.json()["count"])

        resp = self.client.get(
            reverse("api.products:products-list") + f"?priceFrom=101&priceTo=299"
        )
        self.assertEqual(1, resp.json()["count"])

        resp = self.client.get(reverse("api.products:products-list") + f"?priceTo=90")
        self.assertEqual(0, resp.json()["count"])

    def test_returns_facet_counts(self):
        resp = self.client.get(
            reverse("api.products:products-list") + "?channelType=job%20board,community"
        )

        results = resp.json()
        self.assertIn("facets", results)
