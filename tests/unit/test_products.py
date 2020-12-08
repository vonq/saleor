from django.test import tag
from api.products.models import Product
from api.tests import AuthenticatedTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


@tag("unit")
class ProductTestCase(AuthenticatedTestCase):
    @patch("storages.backends.s3boto3.S3Boto3Storage._save")
    def test_it_sets_logo_url(self, mock_storage):
        mock_file_name = "mock_file_name"
        mock_storage.return_value = mock_file_name
        p1 = Product()
        file = SimpleUploadedFile(
            mock_file_name, b"file_content", content_type="text/plain"
        )
        p1.logo = file
        p1.save()
        self.assertIn(mock_file_name, p1.logo_url)

    def test_it_uses_sf_logo_url_when_pkb_logo_is_not_available(self):
        sf_logo_url = "sf_logo"
        p1 = Product(salesforce_logo_url=sf_logo_url)
        p1.save()

        self.assertEquals(p1.logo_url, sf_logo_url)
