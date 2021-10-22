from django.test import TestCase, tag

from api.products.models import Industry
from api.vonqtaxonomy.models import Industry as VonqIndustry


@tag("unit")
class ModelTranslationTestCase(TestCase):
    def setUp(self) -> None:
        vonq_industry = VonqIndustry.objects.create(
            mapi_id=1,
            name="Whatever",
        )

        industry = Industry(
            name_en="Construction",
            name_de="Konstruktion",
            name_nl="bouw",
            vonq_taxonomy_value_id=vonq_industry.id,
        )
        industry.save()

    def test_can_query_across_languages(self):
        self.assertEqual(Industry.objects.all()[0].name, "Construction")

        self.assertEqual(
            Industry.objects.filter(name_nl__contains="bouw").first().name,
            "Construction",
        )

        self.assertEqual(
            Industry.objects.filter_across_languages(name__contains="bouw")
            .first()
            .name,
            "Construction",
        )

        self.assertEqual(
            Industry.objects.filter_across_languages(name="bouw").first().name,
            "Construction",
        )
