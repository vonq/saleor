from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.geocoder import Geocoder
from api.products.models import MapboxLocation, Product, Location


@tag("integration")
class TrafficLocationsDataTestCase(TestCase):
    def setUp(self) -> None:

        self.rome_location = Location(
            canonical_name="Rome, Italy",
            mapbox_id="place.9045806458813870",
            mapbox_context=[
                "region.10762497081813870",
                "country.18258463351519910",
                "continent.europe",
                "world",
            ],
        )
        self.rome_location.save()

        self.amsterdam_location = Location(
            canonical_name="Amsterdam, The Netherlands",
            mapbox_id="place.9718548927723970",
            mapbox_context=[
                "region.9930807704279220",
                "country.13545879598622050",
                "continent.europe",
                "world",
            ],
        )
        self.amsterdam_location.save()

        self.london_location = Location(
            canonical_name="London, United Kingdom",
            mapbox_id="place.8780954591631530",
            mapbox_context=[
                "district.14664713661976620",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
                "world",
            ],
        )
        self.london_location.save()

        self.europe_location = Location(
            canonical_name="Europe",
            mapbox_id="continent.europe",
            mapbox_context=["world"],
        )
        self.europe_location.save()

        self.rome_board = Product(
            title="Product for Rome", similarweb_top_country_shares={"it": 90, "gb": 10}
        )
        self.rome_board.save()
        self.rome_board.locations.set([self.rome_location])
        self.rome_board.save()

        self.london_board = Product(
            title="Board with London jobs",
            similarweb_top_country_shares={"gb": 80, "us": 20},
        )
        self.london_board.save()
        self.london_board.locations.set([self.london_location])
        self.london_board.save()

        self.germany_location = Location(
            mapbox_id="country.11437281100480410",
            mapbox_context=["continent.europe", "world"],
        )
        self.germany_location.save()

        self.german_board = Product(
            title="Board with German jobs (but popular for Polish)",
            similarweb_top_country_shares={"de": 10, "pl": 90},
        )
        self.german_board.save()
        self.german_board.locations.set([self.europe_location, self.germany_location])
        self.german_board.save()

        self.european_board = Product(
            title="European Jobs Board",
            similarweb_top_country_shares={"gb": 5, "it": 5, "de": 90},
        )
        self.european_board.save()
        self.european_board.locations.set(
            [self.london_location, self.germany_location, self.europe_location,]
        )
        self.european_board.save()

        self.amsterdam_board = Product(
            title="Jobs in Amsterdam",
            similarweb_top_country_shares={"nl": 80, "de": 20},
        )
        self.amsterdam_board.save()
        self.amsterdam_board.locations.set([self.amsterdam_location])
        self.amsterdam_board.save()

    def test_get_country_shortcode_works(self):
        geocoder_response = Geocoder.geocode("reading uk")
        country_code = MapboxLocation.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "gb")

        geocoder_response = Geocoder.geocode("rome italy")
        country_code = MapboxLocation.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "it")

        geocoder_response = Geocoder.geocode("ulaanbaatar")
        country_code = MapboxLocation.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "mn")

    def test_search_flow(self):
        resp = self.client.get(reverse("locations") + "?text=london%20uk")
        london_location_id = resp.json()[0]["id"]
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={london_location_id}"
        )

        # we get three results: one for london, two for europe
        self.assertEqual(len(resp.json()["results"]), 2)

        # the first result is the one for London (since it gets more traffic from gb)
        self.assertEqual(resp.json()["results"][0]["title"], "Board with London jobs")

        resp = self.client.get(reverse("locations") + "?text=berlin")
        berlin_id = resp.json()[0]["id"]

        resp = self.client.get(
            reverse("api.products:products-list") + f"?includeLocationId={berlin_id}"
        )
        self.assertEqual(len(resp.json()["results"]), 2)

        # the first result is the global board (since the local Germany board
        # actually gets most of its traffic from Poland)
        self.assertEqual(resp.json()["results"][0]["title"], "European Jobs Board")
