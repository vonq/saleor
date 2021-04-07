import time

from algoliasearch_django import algolia_engine
from django.test import override_settings, tag
from django.urls import reverse

from api import settings
from api.products.models import JobFunction, Location, Product
from api.products.search.index import ProductIndex
from api.tests import AuthenticatedTestCase

from api.vonqtaxonomy.models import JobCategory as VonqJobCategory

NOW = int(time.time())
TEST_INDEX_SUFFIX = f"jobfunction_location_test_{NOW}"


@tag("algolia")
@tag("integration")
class ProductSearchWithNestedJobFunctionAndLocationTest(AuthenticatedTestCase):
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

        # dummy desq job category
        desq_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Something")

        root_job_function = JobFunction(
            name="Root job function", vonq_taxonomy_value_id=desq_job_category.id
        )
        root_job_function.save()
        cls.root_job_function = root_job_function.id

        # job functions tree
        child_level_1_job_function = JobFunction(
            name="Child level 1 job function",
            vonq_taxonomy_value_id=desq_job_category.id,
        )
        child_level_1_job_function.insert_at(
            root_job_function, position="last-child", save=True
        )
        cls.child_level_1_job_function = child_level_1_job_function.id

        child_level_2_job_function = JobFunction(
            name="Child level 2 job function",
            vonq_taxonomy_value_id=desq_job_category.id,
        )
        child_level_2_job_function.insert_at(
            child_level_1_job_function, position="last-child", save=True
        )
        cls.child_level_2_job_function = child_level_2_job_function.id

        cls.all_job_functions_ordered_by_specificity = [
            cls.child_level_2_job_function,
            cls.child_level_1_job_function,
            cls.root_job_function,
        ]

        # location hiearchy
        continent = Location(mapbox_id="continent.europe", canonical_name="Europe")
        continent.save()
        cls.continent = continent.id

        country = Location(
            mapbox_id="country.netherlands",
            canonical_name="Netherlands",
        )
        country.save()
        country.mapbox_within = continent
        country.mapbox_context = [continent.mapbox_id]
        country.save()
        cls.country = country.id

        city = Location(
            mapbox_id="city.rotterdam",
            canonical_name="Rotterdam",
        )
        city.save()
        city.mapbox_within = country
        city.mapbox_context = [country.mapbox_id, continent.mapbox_id]
        city.save()
        cls.city = city.id

        cls.all_locations_ordered_by_specificity = [city.id, country.id, continent.id]

        for location in Location.objects.all():
            for job_function in JobFunction.objects.all():
                product = Product(
                    is_active=True,
                    status="Negotiated",
                    title=f"Product - {job_function.name} - {location.canonical_name}",
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                )
                product.save()
                product.job_functions.add(job_function)
                product.locations.add(location)
                product.save()

        algolia_engine.reindex_all(Product)

    def test_products_match_job_function_whole_hiearchy(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?&jobFunctionId={self.child_level_1_job_function}&includeLocationId={self.city}"
        )
        products_job_function_ids = {
            job_function["id"]
            for product in resp.json()["results"]
            for job_function in product["job_functions"]
        }
        self.assertSetEqual(
            products_job_function_ids,
            set(self.all_job_functions_ordered_by_specificity),
        )

    def test_products_are_ordered_by_job_function_then_location_specificity(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?&jobFunctionId={self.child_level_1_job_function}&includeLocationId={self.city}"
        )
        products = resp.json()["results"]

        counter = 0
        for location_id in self.all_locations_ordered_by_specificity:
            for job_function_id in self.all_job_functions_ordered_by_specificity:
                self.assertEqual(
                    products[counter]["job_functions"][0]["id"], job_function_id
                )
                self.assertEqual(products[counter]["locations"][0]["id"], location_id)
                counter += 1
