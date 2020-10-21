from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.serializers import LocationSerializer


@tag('integration')
class LocationsTestCase(TestCase):
    def test_locations_api_returns_200(self):
        response = self.client.get(reverse("api.products:locations") + "?text=georgia")
        self.assertEqual(response.status_code, 200)

    def test_locations_have_right_structure(self):
        response = self.client.get(reverse("api.products:locations") + "?text=georgia")
        serializer = LocationSerializer(data=response.data[0])
        self.assertTrue(serializer.is_valid())
