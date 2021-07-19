from django.test import TestCase

from django.test import tag
from api.products.geocoder import Geocoder


@tag("unit")
class GeocoderTestCase(TestCase):
    def test_returns_empty_continent_when_country_not_recognised(self):
        continent = Geocoder.get_continent_for_country("Ye Old Queen's Land")
        self.assertEqual(continent, "")
