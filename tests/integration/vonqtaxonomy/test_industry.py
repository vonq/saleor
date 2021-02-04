from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Industry as PkbIndustry
from api.tests import AuthenticatedTestCase
from api.vonqtaxonomy.models import Industry as VonqIndustry


@tag("integration")
class IndustryTaxonomyTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        vonq_industry = VonqIndustry(name="Badabum", name_nl="Badabum in Dutch", mapi_id=1)
        vonq_industry.save()

        self.industry = PkbIndustry(name="Badabim", vonq_taxonomy_value_id=vonq_industry.id)
        self.industry.save()

        self.industry.vonq_taxonomy_value = vonq_industry
        self.industry.save()

    def test_returns_right_value(self):
        response = self.client.get(reverse("vonqtaxonomy:industry") + "?industry_name=Badabim")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")

    def test_returns_right_value_case_insensitive(self):
        response = self.client.get(reverse("vonqtaxonomy:industry") + "?industry_name=baDaBiM")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")

    def test_returns_404_when_using_unknown_value(self):
        response = self.client.get(reverse("vonqtaxonomy:industry") + "?industry_name=foobar")
        self.assertEqual(response.status_code, 404)
