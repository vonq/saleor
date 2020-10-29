from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction


@tag("unit")
class JobFunctionViewTestCase(TestCase):
    def setUp(self) -> None:
        engineering = JobFunction(
            name="Engineering",
            name_de="Schlangenentwickler"
        )
        engineering.save()
        self.engineering = engineering.id

        software_engineering = JobFunction(
            name="Software Engineering",
            name_de="Arbeitslos",
            parent=engineering
        )

        self.software_engineering = software_engineering.id
        software_engineering.save()

    def test_can_list_in_default_language(self):
        resp = self.client.get(reverse("job-functions"))

        self.assertEqual(resp.status_code, 200)
        results = resp.json()['results']

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], "Engineering")
        self.assertEqual(results[0]['parent'], None)
        self.assertEqual(results[1]['name'], "Software Engineering")
        self.assertEqual(results[1]['parent'], self.engineering)
