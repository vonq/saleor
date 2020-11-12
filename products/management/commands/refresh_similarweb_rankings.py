import time
from urllib.parse import urlparse

from django.core.management import BaseCommand

from api.products.models import Product
from api.products.traffic import SimilarWebApiClient, ApiUnavailableException


class Command(BaseCommand):
    help = """
    This command is meant to refresh the traffic rankings of a product in our database 
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            default=100,
            type=int,
            help="Limit the number of entities to change",
        )
        parser.add_argument(
            "-o",
            "--offset",
            default=0,
            type=int,
            help="Offset for the number of entities to process",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]

        products = Product.objects.all()[offset:limit]

        client = SimilarWebApiClient()

        for product in products:
            url = product.url
            if not url:
                self.stdout.write(
                    self.style.ERROR(f"Product {product.title} has no url")
                )
                continue

            domain = urlparse(url).netloc

            time.sleep(1)
            try:
                resp = client.get_country_share_for_domain(domain)
            except ApiUnavailableException as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Product {product.title} triggered a SW error: {e}"
                    )
                )
                continue
            # convert a list of two-keys dicts into a dict of k,v
            product.similarweb_top_country_shares = {
                item["country"]: item["share"] for item in resp
            }
            product.save()
            self.stdout.write(
                self.style.SUCCESS(f"Product {product.title} successfully updated")
            )
