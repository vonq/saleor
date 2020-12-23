from unittest.mock import patch

from django.test import tag
from rest_framework.reverse import reverse

from api.currency.conversion import convert
from api.currency.models import Currency, ExchangeRate
from api.products.models import Product
from api.tests import AuthenticatedTestCase


@tag("unit")
class StartingCurrenciesTestCase(AuthenticatedTestCase):
    def test_has_default_currencies(self):
        self.assertEqual(Currency.objects.count(), 2)

    def test_has_default_exchange_rates(self):
        self.assertEqual(ExchangeRate.objects.count(), 2)


@tag("unit")
@patch("algoliasearch_django.registration.AlgoliaEngine.save_record")
class ProductPriceConversionTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.gbp_conversion_rate = float(
            ExchangeRate.get_latest_rates().get(target_currency__code="GBP").rate
        )
        self.usd_conversion_rate = float(
            ExchangeRate.get_latest_rates().get(target_currency__code="USD").rate
        )

        Product.objects.bulk_create(
            [
                Product(
                    title="Product 1",
                    unit_price=1,
                    rate_card_price=1,
                    is_active=True,
                    status=Product.Status.NEGOTIATED,
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                ),
                Product(
                    title="Product 2",
                    unit_price=None,
                    rate_card_price=None,
                    is_active=True,
                    status=Product.Status.NEGOTIATED,
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                ),
            ],
        )

    def test_shows_converted_rate_prices(self, mock_save):
        resp = self.client.get(reverse("api.products:products-list"))
        records = resp.json()["results"]
        self.assertEqual(len(records), 2)

        self.assertCountEqual(
            records[0]["ratecard_price"],
            [
                {"amount": 1.0, "currency": "EUR"},
                {"amount": convert(1, self.gbp_conversion_rate), "currency": "GBP"},
                {"amount": convert(1, self.usd_conversion_rate), "currency": "USD"},
            ],
        )

        self.assertCountEqual(
            records[1]["ratecard_price"],
            [
                {"amount": None, "currency": "EUR"},
                {"amount": None, "currency": "GBP"},
                {"amount": None, "currency": "USD"},
            ],
        )

    def test_shows_only_selected_currency(self, mock_save):
        resp = self.client.get(reverse("api.products:products-list") + "?currency=GBP")
        records = resp.json()["results"]
        self.assertEqual(len(records), 2)

        self.assertCountEqual(
            records[0]["ratecard_price"],
            [
                {"amount": convert(1, self.gbp_conversion_rate), "currency": "GBP"},
            ],
        )

        self.assertCountEqual(
            records[1]["ratecard_price"],
            [
                {"amount": None, "currency": "GBP"},
            ],
        )
