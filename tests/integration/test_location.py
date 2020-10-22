from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import MapboxLocation
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


@tag("integration")
class MapboxLocationsTestCase(TestCase):
    def test_autocomplete_saves_mapbox_locations(self):
        self.client.get(reverse("api.products:locations-list") + "?text=reading")
        self.assertEqual(MapboxLocation.objects.count(), 5)

        self.assertListEqual(
            list(MapboxLocation.objects.all().values_list("mapbox_placename", flat=True)),
            [
                "Reading, Reading, England, United Kingdom",
                "Reading, Pennsylvania, United States",
                "Reading, England, United Kingdom",
                "Reading, Massachusetts, United States",
                "Readington, New Jersey, United States",
            ],
        )
