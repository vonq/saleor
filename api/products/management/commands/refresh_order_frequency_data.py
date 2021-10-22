from django.core.management.base import BaseCommand
from api.products.models import Product
import json


class Command(BaseCommand):
    help = """
    Updates Products order frequency data given a file
    """

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="The path to the json file")

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]
        try:
            with open(json_file, mode="r") as fp:
                j = json.load(fp)
                for row in j:
                    self._update(row)
            self.stdout.write(self.style.SUCCESS("Success"))

        except OSError:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % json_file))

    def _update(self, row):
        product = Product.objects.all().filter(product_id=row["product_id"]).first()
        order_frequency = row["cume_dist_val"]
        if product and order_frequency != product.order_frequency:
            self.stdout.write(
                f"Updating product {product.product_id} with frequency {order_frequency}"
            )
            product.order_frequency = order_frequency
            product.save()
