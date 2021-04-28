import json
import os

import responses
from django.test import TestCase, tag

from api.products.traffic import SimilarWebApiClient


@tag("unit")
class SimilarWebTrafficTestCase(TestCase):
    def setUp(self) -> None:
        self.json_sw_response = open(
            os.path.join(os.path.dirname(__file__), "data", "similarweb_output.json")
        )

    @responses.activate
    def test_similarweb_client(self):
        # we have a hard limit of 1000 requests per month,
        # so mock the data to save requests
        responses.add(
            responses.GET,
            "https://api.similarweb.com/v1/website/bbc.com/geo/traffic-by-country",
            json=json.load(self.json_sw_response),
            status=200,
        )

        resp = SimilarWebApiClient().get_country_share_for_domain("bbc.com")
        self.assertEqual(len(resp), 5)
        self.assertEqual(resp[0]["country"], "us")

    def tearDown(self) -> None:
        self.json_sw_response.close()
