import datetime
from unittest.mock import patch

import pytz
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
class DatedExchangeRatesTestCase(AuthenticatedTestCase):
    def setUp(self) -> None:
        gbp = Currency.objects.create(code="GBP", name="Pound Sterling")
        usd = Currency.objects.create(code="USD", name="US Dollars")

        ExchangeRate.objects.create(
            target_currency=gbp,
            rate=0.1,
            date="2020-09-30",
            created=datetime.datetime(2020, 10, 1, 14, 30, tzinfo=pytz.utc),
        )

        ExchangeRate.objects.create(
            target_currency=gbp,
            rate=0.2,
            date="2020-10-01",
            created=datetime.datetime(2020, 10, 2, 14, 30, tzinfo=pytz.utc),
        )

        ExchangeRate.objects.create(
            target_currency=gbp,
            rate=0.2,
            date="2020-10-02",
            created=datetime.datetime(2020, 10, 3, 14, 30, tzinfo=pytz.utc),
        )

    def test_can_retrieve_dated_exchange_rate(self):
        resp = self.client.get(
            reverse(
                "api.currency:dated-exchange-rate",
                kwargs={"currency": "GBP", "datetime": "2020-10-02T17:30"},
            )
        )

        self.assertEqual(resp.json()["rate"], 0.2)
        self.assertEqual(resp.json()["code"], "GBP")
        self.assertEqual(resp.json()["date"], "2020-10-01")


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
                    status=Product.Status.ACTIVE,
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                ),
                Product(
                    title="Product 2",
                    unit_price=None,
                    rate_card_price=None,
                    status=Product.Status.ACTIVE,
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
