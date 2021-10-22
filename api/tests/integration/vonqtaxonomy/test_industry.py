from urllib.parse import quote_plus

from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Industry as PkbIndustry
from api.tests import AuthenticatedTestCase
from api.vonqtaxonomy.models import Industry as VonqIndustry


@tag("integration")
class IndustryTaxonomyTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        vonq_industry = VonqIndustry(
            name="Badabum industry", name_nl="Badabum in Dutch", mapi_id=1
        )
        vonq_industry.save()

        self.industry = PkbIndustry(
            name="Badabim & industry", vonq_taxonomy_value_id=vonq_industry.id
        )
        self.industry.save()

        self.industry.vonq_taxonomy_value = vonq_industry
        self.industry.save()

    def test_returns_right_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:industry")
            + "?industry_name="
            + quote_plus("Badabim & industry")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")
        self.assertEqual(response.json()["id"], 1)

    def test_returns_right_value_case_insensitive(self):
        response = self.client.get(
            reverse("vonqtaxonomy:industry")
            + "?industry_name="
            + quote_plus("baDaBiM & iNdUsTrY")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Badabum in Dutch")

    def test_returns_404_when_using_unknown_value(self):
        response = self.client.get(
            reverse("vonqtaxonomy:industry") + "?industry_name=foobar"
        )
        self.assertEqual(response.status_code, 404)
