from unittest.mock import patch, MagicMock

from django.test import TestCase, tag
from django.core import management

from api.products.models import Product


@tag("unit")
@patch("api.products.management.commands.migrate_desq_logos.Command._upload_logo")
@patch("requests.get")
@patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
class MigrateDesqLogosCommandTests(TestCase):
    command = "migrate_desq_logos"
    fake_path = "some/path"

    def test_it_skips_empty_logo_field(self, mock_save, mock_request, mock_upload):
        p1 = Product(product_id="1")
        p1.save()
        management.call_command(self.command)
        self.assertFalse(mock_request.called)

    def test_it_skips_not_found_logos(self, mock_save, mock_request, mock_upload):
        response = MagicMock
        response.status_code = 404
        response.ok = False
        mock_request.return_value = response
        p1 = Product(product_id="1", salesforce_logo_url="fake.png")
        p1.save()
        management.call_command(self.command)
        self.assertTrue(mock_request.called)
        self.assertFalse(mock_upload.called)

    def test_it_uploads_logos(self, mock_save, mock_request, mock_upload):
        response = MagicMock
        response.ok = True
        response.content = b"fake content"
        mock_request.return_value = response
        p1 = Product(product_id="1", salesforce_logo_url="fake.png")
        p1.save()
        management.call_command(self.command)
        self.assertTrue(mock_request.called)
        self.assertTrue(mock_upload.called)
