from django.test import tag
from api.products.geocoder import Geocoder
from api.tests import AuthenticatedTestCase


@tag("unit")
class GeocoderTestCase(AuthenticatedTestCase):
    def test_returns_empty_continent_when_country_not_recognised(self):
        continent = Geocoder.get_continent_for_country("Ye Old Queen's Land")
        self.assertEqual(continent, "")
