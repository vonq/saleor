from django.test import TestCase, tag
from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient

from api.products.serializers import LocationSerializer


@tag('integration')
class LocationsTestCase(TestCase):
    def test_locations_api_returns_200(self):
        client = RequestsClient()
        response = client.get("http://testserver" + reverse("api.products:locations") + "?text=georgia")
        assert response.status_code == 200

    def test_locations_have_right_structure(self):
        client = RequestsClient()
        response = client.get("http://testserver" + reverse("api.products:locations") + "?text=georgia")
        serializer = LocationSerializer(data=response.json()[0])
        assert serializer.is_valid() is True
