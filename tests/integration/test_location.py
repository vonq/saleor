from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.serializers import LocationSerializer


@tag('integration')
class LocationsTestCase(TestCase):
    def setUp(self) -> None:
        self.response = self.client.get(reverse("api.products:locations-list") + "?text=georgia")

    def test_locations_api_returns_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_locations_have_right_structure(self):
        serializer = LocationSerializer(data=self.response.data[0])
        self.assertTrue(serializer.is_valid())

    def test_location_have_only_desired_types(self):
        types = ["country", "region", "place", "district"]
        for result in self.response.data:
            for place_type in result['place_type']:
                self.assertTrue(place_type in types)
