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


class Geocoder:
    @staticmethod
    @lru_cache
    def geocode(text: str) -> List[Dict]:
        response = MapboxGeocoder().forward(
            address=text, types=["country", "region", "place", "district"]
        )
        return response.geojson()["features"]

    @staticmethod
    @lru_cache
    def get_continent_for_country(country: str) -> str:
        country_code = pc.country_name_to_country_alpha2(
            country, cn_name_format="default"
        )
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name.lower()

    @staticmethod
    @lru_cache
    def get_continents(text):
        matching_continent_names = list(
            filter(lambda x: re.search(text, x, re.IGNORECASE), CONTINENTS)
        )
        if matching_continent_names:
            Location = apps.get_model('products', 'Location')
            return [
                Location(
                    mapbox_placename=continent_name,
                    canonical_name=continent_name,
                    mapbox_id=f"continent.{continent_name.lower()}",
                    mapbox_context=["world"],
                    mapbox_place_type=["continent"],
                )
                for continent_name in matching_continent_names
            ]
        return []
