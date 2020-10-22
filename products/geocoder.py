from typing import List, Dict
from mapbox import Geocoder as MapboxGeocoder


class Geocoder:
    @staticmethod
    def geocode(text: str) -> List[Dict]:
        response = MapboxGeocoder().forward(address=text, types=["country", "region", "place", "district"])
        return response.geojson()['features']
