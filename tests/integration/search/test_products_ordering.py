from datetime import datetime

from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Industry, JobFunction, Location, Product
from api.products.search.index import ProductIndex
from api.tests import SearchTestCase
from api.vonqtaxonomy.models import (
    Industry as VonqIndustry,
    JobCategory as VonqJobCategory,
)


@tag("algolia")
@tag("integration")
class ProductSearchOrderByFrequencyTestCase(SearchTestCase):
    model_index_class_pairs = [
        (
            Product,
            ProductIndex,
        )
    ]

    @classmethod
    def setUpSearchClass(cls):
        pkb_industry = VonqIndustry.objects.create(mapi_id=1, name="Something")
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
            status=Product.Status.ACTIVE,
            salesforce_id="high",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.9,
        )
        high_frequency_product.save()

        high_frequency_product.industries.add(cls.recruitment_industry)
        high_frequency_product.locations.add(cls.brazil)
        high_frequency_product.save()

        medium_frequency_product = Product(
            title="frequency 2",
            status=Product.Status.ACTIVE,
            salesforce_id="medium",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.6,
        )
        medium_frequency_product.save()
        medium_frequency_product.industries.add(cls.recruitment_industry)
        medium_frequency_product.save()

        low_frequency_product = Product(
            title="frequency 3",
            status=Product.Status.ACTIVE,
            salesforce_id="low",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            order_frequency=0.3,
        )
        low_frequency_product.save()
        low_frequency_product.industries.add(cls.recruitment_industry)
        low_frequency_product.save()

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
            + f"?includeLocationId={self.brazil.id}&industryId={self.recruitment_industry.id}"
        )
        response = resp.json()["results"]

        self.assertEqual(response[0]["product_id"], "medium")
        self.assertEqual(response[1]["product_id"], "low")
        self.assertEqual(response[2]["product_id"], "high")


@tag("algolia")
@tag("integration")
class ProductSearchOrderByRecencyTestCase(SearchTestCase):
    model_index_class_pairs = [
        (
            Product,
            ProductIndex,
        )
    ]

    @classmethod
    def setUpSearchClass(cls):
        vonq_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Something")
        cls.job_function = JobFunction.objects.create(
            name_en="Some job function", vonq_taxonomy_value_id=vonq_job_category.id
        )

        cls.date_format = "%d/%m/%Y %H:%M:%S"
        cls.dates = [
            "01/01/1969 01:02:03",
            "01/01/2019 01:02:03",
            "01/01/2020 01:02:03",
            "01/01/2020 01:02:04",
            "01/01/2021 01:02:03",
            "01/01/2022 01:02:03",
        ]
        cls.dates.sort()

        for i in range(len(cls.dates)):
            Product.objects.create(
                created=datetime.strptime(cls.dates[i], cls.date_format),
                status=Product.Status.ACTIVE,
                title=cls.dates[i],
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                # newer products have lower order frequency
                order_frequency=1.0 - i / 10,
            )
            p = Product(
                created=datetime.strptime(cls.dates[i], cls.date_format),
                status=Product.Status.ACTIVE,
                title=cls.dates[i],
                salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                # newer products have lower order frequency
                order_frequency=1.0 - i / 10,
            )
            p.save()
            p.job_functions.add(cls.job_function)
            p.save()

    def test_it_sorts_all_products_by_recency_when_sortBy_parameter_is_used(self):
        def check_products_are_sorted_descending_by_created_date(products):
            for i in range(len(products) - 1):
                current_product_time = datetime.strptime(
                    products[i]["title"], self.date_format
                )
                next_product_time = datetime.strptime(
                    products[i + 1]["title"], self.date_format
                )
                self.assertGreaterEqual(current_product_time, next_product_time)

        products = self.client.get(
            reverse("api.products:products-list") + f"?sortBy=recent"
        ).json()["results"]

        check_products_are_sorted_descending_by_created_date(products)

        products = self.client.get(
            reverse("api.products:products-list")
            + f"?jobFunctionId={self.job_function.id}&sortBy=recent"
        ).json()["results"]

        check_products_are_sorted_descending_by_created_date(products)
