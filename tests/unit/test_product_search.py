from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import JobTitle, JobFunction, Product


@tag("unit")
class ProductJobTitleSearchTestCase(TestCase):
    def setUp(self) -> None:
        software_engineering = JobFunction(name="Software Engineering",)
        software_engineering.save()

        construction = JobFunction(name="Construction")
        construction.save()

        self.software_engineering_id = software_engineering.id

        python_developer = JobTitle(
            name="Python Developer", job_function_id=software_engineering.id
        )
        python_developer.save()
        self.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer", job_function_id=software_engineering.id
        )
        java_developer.save()
        self.java_developer_id = java_developer.id

        product = Product(title="A job board for developers",)
        product.save()
        product.job_functions.add(software_engineering)
        product.save()

        product2 = Product(title="A job board for construction jobs")
        product2.save()
        product2.job_functions.add(construction)
        product2.save()

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
