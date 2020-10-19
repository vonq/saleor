from django.test import TestCase
from rest_framework.reverse import reverse

from api.products.models import Location, Product


class LocationsTest(TestCase):
    def setUp(self) -> None:

        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            mapbox_context=[],
        )
        united_kingdom.save()

        england = Location(
            mapbox_id="region.13483278848453920",
            mapbox_text="England",
            mapbox_context=["country.12405201072814600"],
        )
        england.save()

        reading = Location(
            mapbox_id="place.12006143788019830",
            mapbox_text="Reading",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
            ],
        )
        reading.save()

        slough = Location(
            mapbox_id="place.17224449158261700",
            mapbox_text="Slough",
            mapbox_context=[
                "district.11228968263261700",
                "region.13483278848453920",
                "country.12405201072814600",
            ],
        )
        slough.save()

        product = Product(
                    title="Something in the whole of the UK", url="https://vonq.com/somethinglkasjdfhg"
                )
        product.save()
        product.locations.add(united_kingdom)
        product.save()

        product2 = Product(
            title="Something in Reading", url="https://vonq.com/something"
        )
        product2.save()
        product2.locations.add(reading)
        product2.save()

        product3 = Product(
            title="Something in Slough", url="https://vonq.com/something2"
        )
        product3.save()
        product3.locations.add(slough)
        product3.save()


    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(reverse("api.products:products") + "?locationId=place.12006143788019830")

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEquals(resp.json()[0]["title"], "Something in Reading")

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=region.13483278848453920"
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=country.12405201072814600"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=place.17224449158261700&locationId=place.12006143788019830"
        )
        self.assertEqual(len(resp.json()), 2)

        # TODO: boards marked as "global"
        # TODO: boards marked as "continent"
