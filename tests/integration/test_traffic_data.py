from unittest import skip

from django.test import tag
from rest_framework.reverse import reverse

from api.products.geocoder import Geocoder
from api.products.search.index import ProductIndex
from api.products.models import Product, Location
from api.tests.integration.search import SearchTestCase


@tag("integration")
@tag("algolia")
class TrafficLocationsDataTestCase(SearchTestCase):
    model_index_class_pairs = [(Product, ProductIndex)]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.rome_location = Location(
            canonical_name="Rome, Italy",
            mapbox_id="place.9045806458813870",
            mapbox_context=[
                "region.10762497081813870",
                "country.18258463351519910",
                "continent.europe",
                "world",
            ],
        )
        cls.rome_location.save()

        cls.amsterdam_location = Location(
            canonical_name="Amsterdam, The Netherlands",
            mapbox_id="place.9718548927723970",
            mapbox_context=[
                "region.9930807704279220",
                "country.13545879598622050",
                "continent.europe",
                "world",
            ],
        )
        cls.amsterdam_location.save()

        cls.london_location = Location(
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
        cls.london_location.save()

        cls.europe_location = Location(
            canonical_name="Europe",
            mapbox_id="continent.europe",
            mapbox_context=["world"],
        )
        cls.europe_location.save()

        cls.rome_board = Product(
            status=Product.Status.ACTIVE,
            title="Product for Rome",
            similarweb_top_country_shares={"it": 90, "gb": 10},
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.rome_board.save()
        cls.rome_board.locations.set([cls.rome_location])
        cls.rome_board.save()

        cls.london_board = Product(
            status=Product.Status.ACTIVE,
            title="Board with London jobs",
            similarweb_top_country_shares={"gb": 80, "us": 20},
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.london_board.save()
        cls.london_board.locations.set([cls.london_location])
        cls.london_board.save()

        cls.germany_location = Location(
            mapbox_id="country.11437281100480410",
            mapbox_context=["continent.europe", "world"],
        )
        cls.germany_location.save()

        cls.german_board = Product(
            status=Product.Status.ACTIVE,
            title="Board with German jobs (but popular for Polish)",
            similarweb_top_country_shares={"de": 10, "pl": 90},
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.german_board.save()
        cls.german_board.locations.set([cls.europe_location, cls.germany_location])
        cls.german_board.save()

        cls.european_board = Product(
            status=Product.Status.ACTIVE,
            title="European Jobs Board",
            similarweb_top_country_shares={"gb": 5, "it": 5, "de": 90},
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.european_board.save()
        cls.european_board.locations.set(
            [
                cls.london_location,
                cls.germany_location,
                cls.europe_location,
            ]
        )
        cls.european_board.save()

        cls.amsterdam_board = Product(
            status=Product.Status.ACTIVE,
            title="Jobs in Amsterdam",
            similarweb_top_country_shares={"nl": 80, "de": 20},
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
        )
        cls.amsterdam_board.save()
        cls.amsterdam_board.locations.set([cls.amsterdam_location])
        cls.amsterdam_board.save()

    def test_get_country_shortcode_works(self):
        geocoder_response = Geocoder.geocode("reading uk")
        country_code = Location.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "gb")

        geocoder_response = Geocoder.geocode("rome italy")
        country_code = Location.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "it")

        geocoder_response = Geocoder.geocode("ulaanbaatar")
        country_code = Location.get_country_short_code(geocoder_response[0])
        self.assertEqual(country_code, "mn")

    @skip
    @tag("Passes locally but fails in CI")
    def test_search_flow(self):
        resp = self.client.get(reverse("locations") + "?text=london%20uk")
        london_location_id = resp.json()[0]["id"]
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={london_location_id}"
        )

        # the first result is the European jobs board (because it matches the
        # secondary similarweb location and the most filters)
        self.assertEqual(resp.json()["results"][0]["title"], "European Jobs Board")

        resp = self.client.get(reverse("locations") + "?text=berlin")
        berlin_id = resp.json()[0]["id"]

        resp = self.client.get(
            reverse("api.products:products-list") + f"?includeLocationId={berlin_id}"
        )
        self.assertEqual(len(resp.json()["results"]), 2)

        # the first result is the European board – since DE is its primary SW location
        self.assertEqual(resp.json()["results"][0]["title"], "European Jobs Board")
