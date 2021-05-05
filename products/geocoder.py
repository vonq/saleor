from functools import lru_cache
import re

from typing import List, Dict
import pycountry_convert as pc
from mapbox import Geocoder as MapboxGeocoder
from pycountry_convert.convert_continent_code_to_continent_name import (
    CONTINENT_CODE_TO_CONTINENT_NAME,
)

from django.apps import apps

CONTINENTS = list(CONTINENT_CODE_TO_CONTINENT_NAME.values())
MAPBOX_INTERNATIONAL_PLACE_TYPE = "world"


class Geocoder:
    @staticmethod
    @lru_cache
    def geocode(text: str) -> List[Dict]:
        response = MapboxGeocoder().forward(
            address=text, types=["country", "region", "place", "district"]
        )
        return response.geojson().get("features", [])

    @staticmethod
    @lru_cache
    def get_continent_for_country(country: str) -> str:
        try:
            country_code = pc.country_name_to_country_alpha2(
                country, cn_name_format="default"
            )
        except KeyError as e:
            return ""

        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name.lower()

    @staticmethod
    @lru_cache
    def get_continents(text):
        matching_continent_names = list(
            filter(lambda x: re.search(re.escape(text), x, re.IGNORECASE), CONTINENTS)
        )
        if matching_continent_names:
            Location = apps.get_model("products", "Location")
            return Location.objects.filter(
                mapbox_placename__in=matching_continent_names,
                mapbox_place_type=["continent"],
            )

        return []
