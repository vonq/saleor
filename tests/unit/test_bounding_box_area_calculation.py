from django.test import TestCase

from api.products.area import bounding_box_area
from api.products.models import Location


class TestBoundingBox(TestCase):
    def setUp(self) -> None:
        self.netherlands = Location.from_mapbox_result(
            {
                "id": "country.13545879598622050",
                "type": "Feature",
                "place_type": ["country"],
                "relevance": 1,
                "properties": {"wikidata": "Q55", "short_code": "nl"},
                "text": "Netherlands",
                "text_en": "Netherlands",
                "text_de": "Netherlands",
                "text_nl": "Netherlands",
                "place_name": "Netherlands",
                "place_name_en": "Netherlands",
                "place_name_de": "Netherlands",
                "place_name_nl": "Netherlands",
                "bbox": [
                    3.33390071158434,
                    50.7503661060614,
                    7.22749998189678,
                    53.6436329908026,
                ],
                "center": [5.61349061168593, 51.9724664894952],
                "geometry": {
                    "type": "Point",
                    "coordinates": [5.61349061168593, 51.9724664894952],
                },
            }
        )

        self.moscow = Location.from_mapbox_result(
            {
                "id": "place.9707587740083070",
                "type": "Feature",
                "place_type": ["place"],
                "relevance": 1,
                "properties": {"wikidata": "Q649"},
                "text": "Москва",
                "text_en": "Москва",
                "text_de": "Москва",
                "text_nl": "Москва",
                "place_name": "Москва, Moscow, Russia",
                "place_name_en": "Москва, Moscow, Russia",
                "place_name_de": "Москва, Moscow, Russia",
                "place_name_nl": "Москва, Moscow, Russia",
                "matching_text": "Moscow",
                "matching_place_name": "Moscow, Moscow, Russia",
                "bbox": [
                    36.8030478778,
                    55.1424098289334,
                    37.9672888618296,
                    56.0200519998407,
                ],
                "center": [37.61778, 55.75583],
                "geometry": {"type": "Point", "coordinates": [37.61778, 55.75583]},
            }
        )

        self.rome = Location.from_mapbox_result(
            {
                "id": "place.9045806458813870",
                "type": "Feature",
                "place_type": ["place"],
                "relevance": 1,
                "properties": {"wikidata": "Q220"},
                "text": "Roma",
                "text_nl": "Roma",
                "text_en": "Roma",
                "text_de": "Roma",
                "place_name": "Roma, Rome, Italy",
                "place_name_en": "Roma, Rome, Italy",
                "place_name_nl": "Roma, Rome, Italy",
                "place_name_de": "Roma, Rome, Italy",
                "matching_text": "Rome",
                "matching_place_name": "Rome, Rome, Italy",
                "bbox": [12.234478, 41.65548, 12.855979, 42.140911],
                "center": [12.48278, 41.89306],
                "geometry": {"type": "Point", "coordinates": [12.48278, 41.89306]},
            }
        )

        self.italy_cross = Location.from_mapbox_result(
            {
                "id": "place.15771978158386940",
                "type": "Feature",
                "place_type": ["place"],
                "relevance": 1,
                "properties": {"wikidata": "Q6093602"},
                "text": "Italy Cross",
                "text_en": "Italy Cross",
                "text_nl": "Italy Cross",
                "text_de": "Italy Cross",
                "place_name": "Italy Cross, Nova Scotia, Canada",
                "place_name_en": "Italy Cross, Nova Scotia, Canada",
                "place_name_nl": "Italy Cross, Nova Scotia, Canada",
                "place_name_de": "Italy Cross, Nova Scotia, Canada",
                "bbox": [
                    -64.5924865592795,
                    44.1980015393295,
                    -64.4940823864923,
                    44.2823217184863,
                ],
                "center": [-64.5488, 44.2669],
                "geometry": {"type": "Point", "coordinates": [-64.5488, 44.2669]},
            }
        )

    def test_can_convert_bbox_to_area(self):
        self.assertEqual(85558.0, bounding_box_area(self.netherlands))
        self.assertEqual(7157.0, bounding_box_area(self.moscow))
        self.assertEqual(2783.0, bounding_box_area(self.rome))
        self.assertEqual(74.0, bounding_box_area(self.italy_cross))
