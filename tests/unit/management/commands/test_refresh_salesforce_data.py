from unittest.mock import patch, mock_open

from django.test import TestCase, tag
from django.core import management

from api.products.models import Product

json_data = """{"salesforce_id": "1", "product_name": "Product 1"}
{"salesforce_id": "2", "product_name": "Product 2", "description": "New description"}
{"salesforce_id": "3", "product_name": "Product 3 - I'm new"}
"""


@tag('unit')
class CommandTests(TestCase):
    def setUp(self) -> None:
        p1 = Product(salesforce_id="1")
        p1.save()

        p2 = Product(salesforce_id="2", description="Old description")
        p2.save()

    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_title(self, mock_file):
        management.call_command('refresh_salesforce_data', "some/path")
        self.assertEquals(Product.objects.filter(title="Product 1").count(), 1)
        self.assertEquals(Product.objects.filter(salesforce_id="1").first().title, "Product 1")
        self.assertEquals(Product.objects.filter(salesforce_id="2").first().title, "Product 2")

    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_description(self, mock_file):
        management.call_command('refresh_salesforce_data', "some/path")
        filtered = Product.objects.filter(salesforce_id="2")
        self.assertEquals(filtered.count(), 1)
        self.assertEquals(filtered.first().description, "New description")

    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_missing_product(self, mock_file):
        management.call_command('refresh_salesforce_data', "some/path")
        filtered = Product.objects.filter(salesforce_id="3")
        self.assertEquals(filtered.count(), 1)
        self.assertEquals(filtered.first().title, "Product 3 - I'm new")
