import json
import os
from unittest import skipUnless

from django.conf import settings
from jsonschema import validate
from rest_framework.reverse import reverse

from api.products.models import Product
from api.tests import AuthenticatedTestCase


def load_json_schema():
    try:
        with open(os.path.join(os.path.dirname(__file__), "mapi_schema.json")) as f:
            schema = json.loads(f.read())
    except OSError:
        raise Exception("Cannot load json schema, have you imported the MAPI schema?")

    return schema


@skipUnless(settings.ENV == "ci", "Only run this test in CI")
class TestSchemaIntegration(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        Product.objects.bulk_create(
            [
                Product(
                    status=Product.Status.ACTIVE,
                    title="A board for web developers",
                    url="https://something.int/webDev",
                    product_id="1",
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                ),
                Product(
                    status=Product.Status.ACTIVE,
                    title="A board for java developers",
                    url="https://something.int/javaDev",
                    product_id="2",
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                ),
            ],
        )

        self.schema = load_json_schema()

    def test_products_list(self):
        resp = self.client.get(reverse("api.products:products-list"))
        schema = self.schema["[GET]/products/multiple/{products_ids}/"][0]["schema"]
        validate(resp.json()["results"], schema)

    def test_products_detail(self):
        resp = self.client.get(
            reverse(
                "api.products:products-detail",
                kwargs={"product_id": "1"},
            )
        )
        schema = self.schema["[GET]/products/single/{product_id}/"][0]["schema"]
        validate(resp.json(), schema)

    def test_multiple_products_detail(self):
        resp = self.client.get(
            reverse(
                "api.products:products-multiple",
                kwargs={"product_ids": f"1,2"},
            )
        )
        schema = self.schema["[GET]/products/multiple/{products_ids}/"][0]["schema"]
        validate(resp.json()["results"], schema)
