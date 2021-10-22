from unittest.mock import patch, mock_open

from django.test import TestCase, tag
from django.core import management

from api.products.models import Product, Location, Channel

json_data = """[
{"product_id": "1", "cume_dist_val": 0.5},
{"product_id": "2", "cume_dist_val": 0.6}
]
"""


@tag("unit")
class CommandTests(TestCase):
    command = "refresh_order_frequency_data"
    fake_path = "some/path"

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    def setUp(self, mock_register) -> None:
        p1 = Product(salesforce_id="1")
        p1.save()

        p3 = Product(salesforce_id="3")
        p3.save()

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_order_frequency(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        self.assertEquals(Product.objects.filter(salesforce_id="1").count(), 1)
        self.assertEquals(
            Product.objects.filter(salesforce_id="1").first().order_frequency, 0.5
        )

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_ignores_products_that_dont_exist_in_pkb(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        self.assertEquals(Product.objects.filter(salesforce_id="2").count(), 0)
