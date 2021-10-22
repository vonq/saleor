import logging
from typing import Optional
from xml.etree import ElementTree

import requests


logger = logging.getLogger(__name__)


def convert(original_value: Optional[float], conversion_rate: float):
    if original_value is None:
        return
    return round(original_value * conversion_rate, 2)


def get_exchance_rate_for(code, feed):
    exchange_date = feed.find(".//*[@time]").get("time")

    currency = feed.find(f".//*[@currency='{code}']")
    if currency is None:
        logger.warning(f"Couldn't find currency for {code}, skipping.")
        return None, None

    rate = float(currency.get("rate"))

    if not rate:
        logger.warning(f"Couldn't find rate for {code}, skipping.")
        return None, None

    logger.info(f"Exchange rate for {code} is {rate}.")

    return rate, exchange_date


def refresh_exchange_rates(apps):
    Currency = apps.get_model("currency", "Currency")
    ExchangeRate = apps.get_model("currency", "ExchangeRate")

    FEED_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    resp = requests.get(FEED_URL)
    feed = ElementTree.fromstring(resp.content)

    for currency in Currency.objects.all():
        exchange_rate, exchange_date = get_exchance_rate_for(currency.code, feed)
        if not exchange_rate or not exchange_date:
            continue
        ExchangeRate.objects.update_or_create(
            defaults={"rate": exchange_rate},
            target_currency=currency,
            date=exchange_date,
        )
