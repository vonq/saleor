from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Industry, Product


@tag('unit')
class IndustriesTestCase(TestCase):
    def setUp(self) -> None:
        self.construction = Industry(
            name_en="Construction",
            name_de="Konstruktion",
            name_nl="bouw"
        )
        self.construction.save()

        self.engineering = Industry(
            name_en="Engineering",
            name_de="...engineering in german",
            name_nl="...engineering in dutch"
        )
        self.engineering.save()

        self.construction_board = Product(
            title="Construction board"
        )
        self.construction_board.save()
        self.construction_board.industries.add(self.construction)
        self.construction_board.save()

        self.engineering_board = Product(
            title="Engineering Board"
        )
        self.engineering_board.save()
        self.engineering_board.industries.add(self.engineering)
        self.engineering_board.save()

        self.general_board = Product(
            title="General"
        )
        self.general_board.save()
        self.general_board.industries.set([self.engineering, self.construction])

        self.null_board = Product(
            title="Null"
        )
        self.null_board.save()

    def test_can_fetch_all_industries(self):
        resp = self.client.get(reverse('api.products:industries-list'))
        self.assertEqual(len(resp.json()['results']), 2)

    def test_can_filter_products_by_industry_id(self):
        resp = self.client.get(reverse('api.products:products-list') + f"?industryId={self.construction.id}")
        self.assertEqual(len(resp.json()['results']), 2)

        resp = self.client.get(reverse('api.products:products-list') + f"?industryId={self.construction.id},{self.engineering.id}")
        self.assertEqual(len(resp.json()['results']), 3)
