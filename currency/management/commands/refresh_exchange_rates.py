from xml.etree import ElementTree

import requests
from django.core.management import BaseCommand

from api.currency.models import Currency, ExchangeRate

FEED_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


class Command(BaseCommand):
    help = """
        Refresh our own storage of foreign currency exchange against EUR
        """

    def get_exchance_rate_for(self, code, feed):
        exchange_date = feed.find(".//*[@time]").get("time")

        currency = feed.find(f".//*[@currency='{code}']")
        rate = float(currency.get("rate"))
        if not rate:
            self.stdout.write(
                self.style.ERROR(f"Couldn't find currency for {code}, skipping.")
            )
            return None, None

        self.stdout.write(self.style.SUCCESS(f"Exchange rate for {code} is {rate}."))

        return rate, exchange_date

    def handle(self, *args, **options):
        resp = requests.get(FEED_URL)
        feed = ElementTree.fromstring(resp.content)

        for currency in Currency.objects.all():
            exchange_rate, exchange_date = self.get_exchance_rate_for(
                currency.code, feed
            )
            if not exchange_rate or not exchange_date:
                continue
            ExchangeRate.objects.update_or_create(
                defaults={"rate": exchange_rate},
                target_currency=currency,
                date=exchange_date,
            )
