from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.geocoder import Geocoder
from api.products.models import Location
from api.products.serializers import LocationSerializer


@tag("integration")
class LocationsTestCase(TestCase):
    def setUp(self) -> None:
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
                "Reading, Pennsylvania, United States",
                "Reading, England, United Kingdom",
                "Reading, Massachusetts, United States",
                "Readington, New Jersey, United States",
            ],
        )

        self.assertEqual(
            list(Location.objects.all().values_list("canonical_name", flat=True)),
            ["Reading", "Reading", "Reading", "Reading", "Readington"],
        )

    def test_autocomplete_returns_mapbox_order(self):
        self.client.get(reverse("locations") + "?text=london")

        self.assertListEqual(
            list(Location.objects.all().values_list("mapbox_placename", flat=True))[:5],
            [
                "London, Greater London, England, United Kingdom",
                "London, Ontario, Canada",
                "Enfield, Greater London, England, United Kingdom",
                "Londonderry, Derry, Northern Ireland, United Kingdom",
                "Barnet, Greater London, England, United Kingdom",
            ],
        )


@tag("integration")
class ExtendedLocationResultsTestCase(TestCase):
    def setUp(self) -> None:
        # we now rely on continent objects to be part
        # of the database
        Location.objects.create(
            mapbox_placename="Europe",
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

    def test_get_continents_search(self):
        cont = Geocoder.get_continents("eur")
        self.assertEqual(len(cont), 1)
        self.assertEqual(cont[0].fully_qualified_place_name, "Europe")
