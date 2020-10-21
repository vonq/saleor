from django.test import TestCase
from rest_framework.reverse import reverse

from api.products.models import Location, Product


class LocationsTest(TestCase):
    def setUp(self) -> None:

        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            # "continent" here only serves to allow test assertions
            # on sorting to work deterministically here
            mapbox_context=["continent.europe"],
            # note that there is no "global" context for those...
        )
        united_kingdom.save()

        england = Location(
            mapbox_id="region.13483278848453920",
            mapbox_text="England",
            mapbox_context=["country.12405201072814600", "continent.europe"],
        )
        england.save()

        reading = Location(
            mapbox_id="place.12006143788019830",
            mapbox_text="Reading",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
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
                "continent.europe",
            ],
        )
        slough.save()

        global_location = Location(
            # global has a specific name to allow searching just for it
            mapbox_id="global", mapbox_text="global", mapbox_context=[],
        )
        global_location.save()

        product = Product(
            title="Something in the whole of the UK",
            url="https://vonq.com/somethinglkasjdfhg",
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

        global_product = Product(
            title="Something Global", url="https://vonq.com/somethingGlobal"
        )
        global_product.save()
        global_product.locations.add(global_location)
        global_product.save()

    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=place.12006143788019830"
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 1)
        self.assertEquals(resp.json()['results'][0]["title"], "Something in Reading")

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=region.13483278848453920"
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 2)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products") + "?locationId=country.12405201072814600"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 3)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products")
            + "?locationId=place.17224449158261700&locationId=place.12006143788019830"
        )
        self.assertEqual(len(resp.json()['results']), 2)

    def test_return_all_products_with_no_locations(self):
        resp = self.client.get(reverse("api.products:products"))
        self.assertEquals(len(resp.json()['results']), 4)

    def test_results_are_sorted_by_specificity(self):
        resp = self.client.get(reverse("api.products:products"))
        products = resp.json()['results']

        self.assertEquals(products[-1]["title"], "Something Global")
        self.assertEquals(products[-2]["title"], "Something in the whole of the UK")

    def test_products_with_global_locations(self):
        resp = self.client.get(reverse("api.products:products") + "?locationId=global")
        self.assertEquals(resp.status_code, 200)

        self.assertEquals(len(resp.json()['results']), 1)
        self.assertEquals(resp.json()['results'][0]["title"], "Something Global")

    def test_search_parameter_should_work_with_arrays_or_list(self):
        resp_one = self.client.get(reverse("api.products:products") + "?locationId=place.12006143788019830,place.17224449158261700")

        resp_two = self.client.get(
            reverse("api.products:products") + "?locationId=place.12006143788019830&locationId=place.17224449158261700")

        self.assertListEqual(resp_one.json()['results'], resp_two.json()['results'])

    def test_products_can_offset_and_limit(self):
        resp_one = self.client.get(reverse("api.products:products"))

        resp_two = self.client.get(reverse("api.products:products") + "?limit=1")

        resp_three = self.client.get(reverse("api.products:products") + "?limit=1&offset=2")

        self.assertNotEqual(len(resp_one.json()['results']), 1)
        self.assertEquals(len(resp_two.json()['results']), 1)
        self.assertEquals(len(resp_three.json()['results']), 1)
        self.assertNotEqual(resp_one.json()['results'][0]['title'], resp_two.json()['results'][0]['title'])

