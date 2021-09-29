from django.test import TestCase
from algoliasearch_django.decorators import disable_auto_indexing
from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Product
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from api.tests.integration import force_user_login


@tag("unit")
@disable_auto_indexing
class ProductTestCase(TestCase):
    @patch("storages.backends.s3boto3.S3Boto3Storage._save")
    @patch("api.products.models.Product.generate_cropped_images")
    def test_it_sets_logo_url(self, mock_generate_cropped_images, mock_storage):
        mock_file_name = "mock_file_name"
        mock_storage.return_value = mock_file_name
        p1 = Product()
        file = SimpleUploadedFile(
            mock_file_name, b"file_content", content_type="text/plain"
        )
        p1.logo = file
        p1.cropping_rectangle = 2
        p1.cropping_square = 33
        p1.save()
        self.assertIn(mock_file_name, p1.logo_url)

    @patch("storages.backends.s3boto3.S3Boto3Storage._save")
    @patch("PIL.Image.open")
    def test_it_generates_cropped_images_when_there_is_logo(
        self, mock_open, mock_storage
    ):
        mock_file_name = "mock_file_name"
        mock_storage.return_value = mock_file_name
        p1 = Product()
        file = SimpleUploadedFile(
            mock_file_name, b"file_content", content_type="text/plain"
        )
        p1.logo = file
        p1.cropping_rectangle = p1.cropping_square = "1,2,3,4"
        p1.save()
        self.assertTrue(mock_open.called)

    @patch("storages.backends.s3boto3.S3Boto3Storage._save")
    @patch("PIL.Image.open")
    def test_it_generates_cropped_images_when_cropping_changed(
        self, mock_open, mock_storage
    ):
        mock_file_name = "mock_file_name"
        mock_storage.return_value = mock_file_name
        p1 = Product()
        file = SimpleUploadedFile(
            mock_file_name, b"file_content", content_type="text/plain"
        )
        p1.logo = file
        p1.cropping_rectangle = p1.cropping_square = "1,2,3,4"
        p1.save()
        p1.cropping_rectangle = p1.cropping_square = "4,4,4,4"
        p1.save()
        self.assertEqual(mock_open.call_count, 2)

    @patch("storages.backends.s3boto3.S3Boto3Storage._save")
    @patch("PIL.Image.open")
    def test_it_does_not_generate_cropped_images_when_there_is_no_logo(
        self, mock_open, mock_storage
    ):
        mock_file_name = "mock_file_name"
        mock_storage.return_value = mock_file_name
        p1 = Product()
        p1.save()
        self.assertFalse(mock_open.called)

    def test_it_uses_sf_logo_url_when_pkb_logo_is_not_available(self):
        sf_logo_url = "sf_logo"
        p1 = Product(salesforce_logo_url=sf_logo_url)
        p1.save()

        self.assertEquals(p1.logo_url, sf_logo_url)


class ProductSchemaSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.test_product = Product.objects.create(
            title="Test Product",
            salesforce_id="12345",
            status=Product.Status.ACTIVE,
            available_in_jmp=True,
            available_in_ats=True,
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            customer_id="12345",
            supplier_setup_time=20,
        )

    def test_internal_user_sees_salesforce_id(self):
        force_user_login(self.client, "internal")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.test_product.product_id},
            )
        )

        self.assertTrue("salesforce_id" in resp.json().keys())

    def test_jmp_user_sees_customer_id(self):
        force_user_login(self.client, "jmp")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.test_product.product_id},
            )
        )
        self.assertTrue("customer_id" in resp.json().keys())
        self.assertFalse("salesforce_id" in resp.json().keys())

    def test_hapi_doesnt_see_additional_fields(self):
        force_user_login(self.client, "mapi")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.test_product.product_id},
            )
        )
        self.assertFalse("customer_id" in resp.json().keys())
        self.assertFalse("salesforce_id" in resp.json().keys())

    def test_hapi_sees_setup_time(self):
        force_user_login(self.client, "mapi")
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": self.test_product.product_id},
            )
        )
        self.assertTrue("time_to_setup" in resp.json().keys())
        self.assertEqual({"range": "hours", "period": 20}, resp.json()["time_to_setup"])
