from django.core.management.base import BaseCommand
from api.products.models import Product
import requests
import tempfile
from django.core.files import File
from django.db.models import Q


class Command(BaseCommand):
    help = """
    Migrates desq logos to S3 by downloading the files from `salesforce_logo_url` and setting the django logo fields
    """

    def handle(self, *args, **kwargs):
        products = (
            Product.objects.filter(
                Q(logo_rectangle_uncropped__isnull=True)
                | Q(logo_rectangle_uncropped="")
            )
            .exclude(salesforce_logo_url__isnull=True)
            .all()
        )
        skipped_count = 0

        for product in products:
            self.stdout.write(f"Downloading logo for product {product.product_id}")
            try:
                r = requests.get(product.salesforce_logo_url, allow_redirects=True)
                if not r.ok:
                    skipped_count += 1
                    self.stdout.write(
                        f"Skipping product {product.product_id}. Status code was {r.status_code}"
                    )
                else:
                    self._upload_logo(product, r.content)
            except Exception as e:
                self.stdout.write(
                    f"Unable to request {product.salesforce_logo_url} for product {product.product_id}. Exception:\n{e}"
                )
                skipped_count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Success. {skipped_count} files skipped.")
        )

    def _upload_logo(self, product: Product, content):
        """
        Creates a temporary file with a given content and sets a product logo with it (triggering its upload to S3)
        :param product: The product to be updated
        :param content: The file content to be used
        :return:
        """
        with tempfile.NamedTemporaryFile() as temp:
            self.stdout.write(f"Writing response to temporary file")
            temp.write(content)
            temp.flush()
            self.stdout.write(f"Uploading logo for product {product.product_id}")
            file_name = product.logo_url.split("/")[-1]
            product.logo_rectangle_uncropped = File(temp, name=file_name)
            product.save()
