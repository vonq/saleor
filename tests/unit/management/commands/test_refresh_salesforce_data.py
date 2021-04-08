from unittest.mock import patch, mock_open

from django.test import TestCase, tag
from django.core import management

from api.products.models import Product, Location, Channel

json_data = """{"salesforce_id": "1", "jmp_product_name": "Product 1"}
{"salesforce_id": "2", "jmp_product_name": "Product 2", "description": "New description"}
{"salesforce_id": "3", "jmp_product_name": "Product 3 - I'm new"}
{"salesforce_id": "4", "is_available_on_jmp": false}
{"salesforce_id": "5", "relevant_location_names": ["Brazil", "Netherlands"]}
{"salesforce_id": "6", "desq_id": "5432"}
{"salesforce_id": "7", "jmp_product_name": "Product 7", "channel_name": "Channel 1", "channel_id": "1"}
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

        p6 = Product(salesforce_id="6", desq_product_id="5432")
        p6.save()

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
    def test_builds_complete_title(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        self.assertEquals(Product.objects.filter(title="Product 7").count(), 1)
        self.assertEquals(
            Product.objects.filter(salesforce_id="7").first().title, "Product 7"
        )
        self.assertEquals(
            Product.objects.filter(salesforce_id="7").first().external_product_name,
            "Channel 1 - Product 7",
        )

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_creates_channel(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        self.assertEquals(Channel.objects.filter(salesforce_id="1").count(), 1)
        self.assertEquals(
            Channel.objects.filter(salesforce_id="1").first().name, "Channel 1"
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
    def test_sets_product_id(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="5").first()
        self.assertEquals(filtered.product_id, "5")

    @patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
    @patch("builtins.open", new_callable=mock_open, read_data=json_data)
    def test_prioritizes_desq_product_id(self, mock_file, mock_save):
        management.call_command(self.command, self.fake_path)
        filtered = Product.objects.filter(salesforce_id="6").first()
        self.assertEquals(filtered.product_id, "5432")
