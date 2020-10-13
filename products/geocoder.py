from typing import List, Dict
from mapbox import Geocoder as MapboxGeocoder


class Geocoder:
    @staticmethod
    def geocode(text: str) -> List[Dict]:
        response = MapboxGeocoder().forward(text)
        return response.geojson()['features']
