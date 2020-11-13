from unittest.mock import patch, mock_open

from django.test import TestCase, tag
from django.core import management

from api.products.models import Product, Location

json_data = """{"salesforce_id": "1", "product_name": "Product 1"}
{"salesforce_id": "2", "product_name": "Product 2", "description": "New description"}
{"salesforce_id": "3", "product_name": "Product 3 - I'm new"}
{"salesforce_id": "4", "is_available_on_jmp": false}
{"salesforce_id": "5", "relevant_location_names": ["Brazil", "Netherlands"]}
"""


@tag("unit")
class CommandTests(TestCase):
    command = "refresh_salesforce_data"
    fake_path = "some/path"

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    def setUp(self, mock_register) -> None:
        p1 = Product(salesforce_id="1")
        p1.save()

        p2 = Product(salesforce_id="2", description="Old description")
        p2.save()

        p4 = Product(salesforce_id="4", available_in_jmp=True)
        p4.save()

        p5 = Product(salesforce_id="5")
        p5.save()
        l1 = Location(desq_name_en="Brazil")
        l1.save()
        p5.locations.add(l1)
        p5.save()

        l2 = Location(desq_name_en="Netherlands")
        l2.save()

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_title(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        self.assertEquals(Product.objects.filter(title="Product 1").count(), 1)
        self.assertEquals(
            Product.objects.filter(salesforce_id="1").first().title, "Product 1"
        )
        self.assertEquals(
            Product.objects.filter(salesforce_id="2").first().title, "Product 2"
        )

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_description(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="2")
        self.assertEquals(filtered.count(), 1)
        self.assertEquals(filtered.first().description, "New description")

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_missing_product(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="3")
        self.assertEquals(filtered.count(), 1)
        self.assertEquals(filtered.first().title, "Product 3 - I'm new")

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_updates_boolean_column(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="4").first()
        self.assertEquals(filtered.available_in_jmp, False)

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_adds_locations(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="5").first()
        locations = [location.desq_name_en for location in filtered.locations.all()]
        self.assertEquals(locations, ["Brazil", "Netherlands"])
