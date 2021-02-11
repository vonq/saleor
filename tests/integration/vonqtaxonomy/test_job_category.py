from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction as PkbJobFunction
from api.tests import AuthenticatedTestCase
from api.vonqtaxonomy.models import JobCategory as VonqJobCategory


@tag("integration")
class JobCategoryTaxonomyTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        vonq_industry = VonqJobCategory(
            name="Badabum", name_nl="Badabum in Dutch", mapi_id=1
        )
        vonq_industry.save()

        self.industry = PkbJobFunction(
            name="Badabim", vonq_taxonomy_value_id=vonq_industry.id
        )
        self.industry.save()

        self.industry.vonq_taxonomy_value = vonq_industry
        self.industry.save()

    def test_returns_right_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category") + "?job_function_name=Badabim"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")
        self.assertEqual(response.json()["id"], 1)

    def test_returns_right_value_case_insensitive(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category") + "?job_function_name=baDaBiM"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")

    def test_returns_404_when_using_unknown_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category") + "?job_function_name=foobar"
        )
        self.assertEqual(response.status_code, 404)
