from django.test import TestCase, tag
from rest_framework.test import RequestsClient


@tag("unit")
class HealthTestCase(TestCase):
    def test_random(self):
        client = RequestsClient()
        response = client.get("http://testserver/health")
        assert response.status_code == 200
