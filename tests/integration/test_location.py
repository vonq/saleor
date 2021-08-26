from django.test import TestCase

from django.test import tag
from rest_framework.reverse import reverse

from api.products.geocoder import Geocoder
from api.products.models import Location
from api.products.serializers import LocationSerializer


@tag("integration")
class LocationsTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.response = self.client.get(reverse("locations") + "?text=georgia")

    def test_locations_api_returns_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_locations_have_right_structure(self):
        serializer = LocationSerializer(data=self.response.data[0])
        self.assertTrue(serializer.is_valid())

    def test_location_have_only_desired_types(self):
        types = ["country", "region", "place", "district"]
        for result in self.response.data:
            for place_type in result["place_type"]:
                self.assertTrue(place_type in types)


@tag("integration")
class MapboxLocationsTestCase(TestCase):
    def test_autocomplete_saves_mapbox_locations(self):
        self.client.get(reverse("locations") + "?text=reading")
        self.assertEqual(Location.objects.count(), 5)

        self.assertListEqual(
            list(Location.objects.all().values_list("mapbox_placename", flat=True)),
            [
                "Reading, Reading, England, United Kingdom",
                "Reading, England, United Kingdom",
                "Reading, Pennsylvania, United States",
                "Reading, Massachusetts, United States",
                "Readington Township, New Jersey, United States",
            ],
        )

        self.assertEqual(
            list(Location.objects.all().values_list("canonical_name", flat=True)),
            ["Reading", "Reading", "Reading", "Reading", "Readington Township"],
        )

    def test_autocomplete_returns_mapbox_order(self):
        self.client.get(reverse("locations") + "?text=london")

        self.assertListEqual(
            list(Location.objects.all().values_list("mapbox_placename", flat=True)),
            [
                "London, Greater London, England, United Kingdom",
                "Londonderry, Londonderry, Northern Ireland, United Kingdom",
                "London, Ontario, Canada",
                "London Borough of Enfield, Greater London, England, United Kingdom",
                "Londonderry, Northern Ireland, United Kingdom",
            ],
        )

    def test_can_resolve_weird_antarctica_islands(self):
        resp = self.client.get(reverse("locations") + "?text=oceania")
        self.assertEqual(resp.status_code, 200)


@tag("integration")
class ExtendedLocationResultsTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        # we now rely on continent objects to be part
        # of the database
        Location.objects.create(
            mapbox_placename="Europe",
            mapbox_placename_en="Europe",
            mapbox_placename_nl="Europe",
            mapbox_placename_de="Europe",
            mapbox_place_type=["continent"],
            mapbox_context=["world"],
        )

    def test_endpoint_can_produce_extended_results(self):
        response = self.client.get(reverse("locations") + "?text=london%20uk")
        self.assertEqual(
            response.json()[0]["place_type"],
            ["place"],
        )
        self.assertEqual(
            response.json()[1]["place_type"],
            ["district"],
        )

    def test_endpint_can_match_on_continent_names(self):
        response = self.client.get(reverse("locations") + "?text=eur")

        self.assertEqual(
            response.json()[0]["place_type"],
            [
                "continent",
            ],
        )

    def test_endpoint_can_match_on_brackets(self):
        response = self.client.get(reverse("locations") + "?text=Belgium / Namen (BE")

        self.assertNotEqual(
            response.json()[0]["place_type"],
            [
                "continent",
            ],
        )

    def test_get_continents_search(self):
        cont = Geocoder.get_continents("eur")
        self.assertEqual(len(cont), 1)
        self.assertEqual(cont[0].fully_qualified_place_name, "Europe")

    def test_can_fetch_locations_in_multiple_languages(self):
        english_response = self.client.get(reverse("locations") + "?text=rome")
        german_response = self.client.get(
            reverse("locations") + "?text=rom", HTTP_ACCEPT_LANGUAGE="de-CH"
        )

        # The first two results are supposed to be Rome (the city), Rome (the region), Rome (a city in Georgia, US)
        self.assertEqual(
            [loc["id"] for loc in english_response.json()[0:2]],
            [loc["id"] for loc in german_response.json()[0:2]],
        )

    def test_can_resolve_basic_locations(self):
        english_response = self.client.get(
            reverse("locations") + "?text=germany", HTTP_ACCEPT_LANGUAGE="en"
        )
        german_response = self.client.get(
            reverse("locations") + "?text=deutschland", HTTP_ACCEPT_LANGUAGE="de-CH"
        )

        self.assertEqual(
            english_response.json()[0]["id"], german_response.json()[0]["id"]
        )

        germany_id = english_response.json()[0]["id"]
        germany = Location.objects.get(pk=germany_id)

        self.assertEqual(germany.canonical_name_en, "Germany")
        self.assertEqual(germany.canonical_name_de, "Deutschland")
        self.assertEqual(germany.canonical_name_nl, "Duitsland")


@tag("integration")
class ExistingLocationsTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.germany = Location.objects.create(
            mapbox_placename="Germany",
            mapbox_placename_en=None,
            mapbox_placename_nl=None,
            mapbox_placename_de=None,
            mapbox_id="country.11437281100480410",
            mapbox_place_type=["country"],
        )

    def test_search_for_deutschland_yields_germany(self):
        german_response = self.client.get(
            reverse("locations") + "?text=deutschland", HTTP_ACCEPT_LANGUAGE="de-CH"
        )
        germany_id = german_response.json()[0]["id"]

        self.assertEqual(self.germany.id, germany_id)
