from urllib.parse import quote_plus

from algoliasearch_django.decorators import disable_auto_indexing
from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction as PkbJobFunction
from api.tests import AuthenticatedTestCase
from api.vonqtaxonomy.models import JobCategory as VonqJobCategory


@tag("integration")
@disable_auto_indexing
class JobCategoryTaxonomyTestCase(AuthenticatedTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        vonq_industry = VonqJobCategory(
            name="Badabum Job Function", name_nl="Badabum in Dutch", mapi_id=1
        )
        vonq_industry.save()

        cls.industry = PkbJobFunction(
            name="Badabim & Job Function", vonq_taxonomy_value_id=vonq_industry.id
        )
        cls.industry.save()

        cls.industry.vonq_taxonomy_value = vonq_industry
        cls.industry.save()

    def test_returns_right_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category")
            + "?job_function_name="
            + quote_plus("Badabim & Job Function")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")
        self.assertEqual(response.json()["id"], 1)

    def test_returns_right_value_case_insensitive(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category")
            + "?job_function_name="
            + quote_plus("baDaBiM & JOB functiON")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")

    def test_returns_404_when_using_unknown_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category") + "?job_function_name=foobar"
        )
        self.assertEqual(response.status_code, 404)

    def test_handles_missing_category(self):
        response = self.client.get(
            reverse("vonqtaxonomy:job-category") + "?industry_name=foobar"
        )
        self.assertEqual(response.status_code, 400)
