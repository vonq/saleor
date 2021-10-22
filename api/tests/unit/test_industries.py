from django.test import TestCase

from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Industry
from api.vonqtaxonomy.models import Industry as VonqIndustry


@tag("unit")
class JobFunctionViewTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()

        vonq_industry = VonqIndustry.objects.create(mapi_id=1, name="Something")

        i1 = Industry(name="B Industry", vonq_taxonomy_value_id=vonq_industry.id)
        i2 = Industry(name="A Industry", vonq_taxonomy_value_id=vonq_industry.id)
        i2.save()
        i1.save()

    def test_can_list_in_default_language(self):
        resp = self.client.get(reverse("api.products:industries-list"))

        self.assertEqual(resp.status_code, 200)
        results = resp.json()

        self.assertEqual(results[0]["name"], "A Industry")
        self.assertEqual(results[1]["name"], "B Industry")
