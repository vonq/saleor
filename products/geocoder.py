from typing import List, Dict
from mapbox import Geocoder as MapboxGeocoder

from api.products.models import MapboxLocation


class Geocoder:
    @staticmethod
    def geocode(text: str) -> List[Dict]:
        response = MapboxGeocoder().forward(address=text, types=["country", "region", "place", "district"])
        return response.geojson()['features']

    @staticmethod
    def list_context_locations_ids(location_ids: List[str]) -> List[str]:
        qs = MapboxLocation.objects.filter(mapbox_id__in=location_ids)
        if qs.count() == 0:
            return []

        context_locations_ids = []
        for row in qs:
            context_locations_ids += [location['id'] for location in row.mapbox_data['context']]
        return context_locations_ids
