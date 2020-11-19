from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Industry
from api.tests import AuthenticatedTestCase


@tag("unit")
class JobFunctionViewTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        i1 = Industry(
            name="B Industry",
        )
        i2 = Industry(
            name="A Industry",
        )
        i2.save()
        i1.save()

    def test_can_list_in_default_language(self):
        resp = self.client.get(reverse("api.products:industries-list"))

        self.assertEqual(resp.status_code, 200)
        results = resp.json()["results"]

        self.assertEqual(results[0]["name"], "A Industry")
        self.assertEqual(results[1]["name"], "B Industry")
