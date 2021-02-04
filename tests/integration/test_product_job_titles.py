from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction, JobTitle
from api.vonqtaxonomy.models import JobCategory as VonqJobCategory
from api.tests import AuthenticatedTestCase


@tag("integration")
class JobTitleSearchTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()

        pkb_job_category = VonqJobCategory.objects.create(
            mapi_id=1,
            name="Something"
        )

        software_development = JobFunction(name="Software Development")
        software_development.vonq_taxonomy_value = pkb_job_category
        software_development.save()
        self.software_development_id = software_development.id

        python_developer = JobTitle(
            name="Python Developer", name_de="Schlangenentwickler", frequency=1
        )

        snake_tamer = JobTitle(name="Snake tamer", frequency=1)

        python_developer.save()
        snake_tamer.save()
        self.snake_tamer_id = snake_tamer.id

        snake_tamer.job_function = software_development
        snake_tamer.alias_of = python_developer
        snake_tamer.save()

        self.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer", name_de="Arbeitslos", frequency=100000
        )

        self.java_developer_id = java_developer.id
        java_developer.save()

    def test_can_search_in_default_language(self):
        resp = self.client.get(reverse("job-titles") + f"?text=pyth")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEqual(resp.json()["results"][0]["name"], "Python Developer")

    def test_most_frequent_job_title_is_at_the_top(self):
        resp = self.client.get(reverse("job-titles") + f"?text=a")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 3)
        self.assertEqual(resp.json()["results"][0]["name"], "Java Developer")

    def test_can_search_across_languages(self):
        resp1 = self.client.get(reverse("job-titles") + f"?text=schlan")
        resp2 = self.client.get(reverse("job-titles") + f"?text=arbeit")
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(len(resp1.json()["results"]), 2)
        self.assertEqual(resp1.json()["results"][0]["name"], "Python Developer")

        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()["results"]), 1)
        self.assertEqual(resp2.json()["results"][0]["name"], "Java Developer")

    def test_matches_aliases_and_shows_them_first(self):
        resp = self.client.get(reverse("job-titles") + f"?text=python")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEqual(resp.json()["results"][0]["name"], "Python Developer")
        self.assertEqual(resp.json()["results"][1]["name"], "Snake tamer")

    def test_includes_job_function_where_available(self):
        resp = self.client.get(reverse("job-titles") + f"?text=python")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEqual(
            resp.json()["results"][1]["job_function"]["id"],
            self.software_development_id,
        )

        self.assertIsNone(resp.json()["results"][0]["job_function"], None)
