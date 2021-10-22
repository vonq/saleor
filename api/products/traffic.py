import datetime
from functools import lru_cache
from typing import List

import pycountry
import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings


class ApiUnavailableException(Exception):
    pass


def get_country_code_from_iso_3166(iso_code):
    try:
        results = pycountry.countries.search_fuzzy(iso_code)
    except LookupError:
        return
    if results:
        return results[0].alpha_2.lower()


class SimilarWebApiClient:
    def __init__(self):
        self.api_key = settings.SIMILARWEB_API_KEY

        self.request_url = (
            "https://api.similarweb.com/v1/website/{domain}/geo/traffic-by-country?"
            "api_key={api_key}"
            "&start_date={start_date}"
            "&end_date={end_date}"
            "&main_domain_only=true"
            "&format=json"
        )

    def get_share_country_from_record(self, record: dict) -> dict:
        return {
            "share": int(record["share"] * 100),
            "country": get_country_code_from_iso_3166(str(record["country"])),
        }

    @lru_cache
    def get_country_share_for_domain(self, domain: str) -> List[dict]:
        last_month = datetime.date.today() - relativedelta(months=1)
        last_year = datetime.date.today() - relativedelta(years=1)

        resp = requests.get(
            self.request_url.format(
                domain=domain,
                api_key=self.api_key,
                start_date=last_year.strftime("%Y-%m"),
                end_date=last_month.strftime("%Y-%m"),
            )
        )

        if not resp.ok:
            raise ApiUnavailableException(resp.json()["meta"]["error_message"])

        results = []
        for record in resp.json()["records"][:6]:
            country = get_country_code_from_iso_3166(str(record["country"]))
            if country:
                results.append(self.get_share_country_from_record(record))

        return results
