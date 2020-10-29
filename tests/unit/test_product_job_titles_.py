from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import JobTitle


@tag("unit")
class JobTitleSearchTestCase(TestCase):
    def setUp(self) -> None:

        python_developer = JobTitle(
            name="Python Developer",
            name_de="Schlangenentwickler",
            frequency=1
        )
        python_developer.save()
        self.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer",
            name_de="Arbeitslos",
            frequency=100000
        )

        self.java_developer_id = java_developer.id
        java_developer.save()

    def test_can_search_in_default_language(self):
        resp = self.client.get(
            reverse("job-titles")
            + f"?text=pyth"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 1)
        self.assertEqual(resp.json()['results'][0]['name'], "Python Developer")

    def test_most_frequent_job_title_is_at_the_top(self):
        resp = self.client.get(
            reverse("job-titles")
            + f"?text=a"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 2)
        self.assertEqual(resp.json()['results'][0]['name'], "Java Developer")

    def test_can_search_across_languages(self):
        resp1 = self.client.get(
            reverse("job-titles")
            + f"?text=schlan"
        )

        resp2 = self.client.get(
            reverse("job-titles")
            + f"?text=arbeit"
        )

        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(len(resp1.json()['results']), 1)
        self.assertEqual(resp1.json()['results'][0]['name'], "Python Developer")

        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()['results']), 1)
        self.assertEqual(resp2.json()['results'][0]['name'], "Java Developer")
