from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Location, Product


@tag('unit')
class ProductLocationsTest(TestCase):
    def setUp(self) -> None:

        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            # "continent" here only serves to allow test assertions
            # on sorting to work deterministically here
            mapbox_context=["continent.europe", "global"],
            # note that there is no "global" context for those...
        )
        united_kingdom.save()
        self.united_kingdom_id = united_kingdom.id

        england = Location(
            mapbox_id="region.13483278848453920",
            mapbox_text="England",
            mapbox_context=["country.12405201072814600", "continent.europe", "global"],
        )
        england.save()
        self.england_id = england.id

        reading = Location(
            mapbox_id="place.12006143788019830",
            mapbox_text="Reading",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
                "global",
            ],
        )
        reading.save()
        self.reading_id = reading.id

        slough = Location(
            mapbox_id="place.17224449158261700",
            mapbox_text="Slough",
            mapbox_context=[
                "district.11228968263261700",
                "region.13483278848453920",
                "country.12405201072814600",
                "continent.europe",
                "global",
            ],
        )
        slough.save()
        self.slough_id = slough.id

        global_location = Location(
            # global has a specific name to allow searching just for it
            mapbox_id="global",
            mapbox_text="global",
            mapbox_context=[],
        )
        global_location.save()
        self.global_id = global_location.id

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

        product4 = Product(
            title="Something in Slough and Reading", url="https://vonq.com/something4"
        )

        product4.save()
        product4.locations.set([slough, reading])
        product4.save()

        global_product = Product(
            title="Something Global", url="https://vonq.com/somethingGlobal"
        )
        global_product.save()
        global_product.locations.add(global_location)
        global_product.save()

        # populate mapbox locations contexts
        self.client.get(reverse("locations") + "?text=reading")
        self.client.get(reverse("locations") + "?text=england")
        self.client.get(reverse("locations") + "?text=slough")
        self.client.get(reverse("locations") + "?text=united%20kingdom")

    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.reading_id}"
        )

        self.assertEquals(resp.status_code, 200)

        # must be 4, as we have product, product2, product4, global
        self.assertEqual(len(resp.json()["results"]), 4)

        # the most specific location is at the top
        self.assertEquals(resp.json()["results"][0]["title"], "Something in Reading")

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.england_id}"
        )

        self.assertEquals(resp.status_code, 200)
        # they're 5, because now there's a "slough only" product
        self.assertEqual(len(resp.json()["results"]), 5)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.united_kingdom_id}"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 5)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.slough_id},{self.reading_id}"
        )
        self.assertEqual(len(resp.json()["results"]), 5)

    def test_return_all_products_with_no_locations(self):
        resp = self.client.get(reverse("api.products:products-list"))
        self.assertEquals(len(resp.json()["results"]), 5)

    def test_results_are_sorted_by_specificity(self):
        resp = self.client.get(reverse("api.products:products-list"))
        products = resp.json()["results"]

        self.assertEquals(products[-1]["title"], "Something Global")
        self.assertEquals(products[-2]["title"], "Something in the whole of the UK")

    def test_products_with_global_locations(self):
        resp_global = self.client.get(
            reverse("api.products:products-list") + f"?includeLocationId={self.global_id}"
        )
        resp_list_all = self.client.get(reverse("api.products:products-list"))
        self.assertEquals(resp_global.status_code, 200)
        self.assertEquals(resp_list_all.status_code, 200)

        self.assertEquals(
            resp_global.json()["results"][-1]["title"], "Something Global"
        )
        self.assertEquals(
            len(resp_global.json()["results"]), len(resp_list_all.json()["results"])
        )

    def test_products_can_offset_and_limit(self):
        resp_one = self.client.get(reverse("api.products:products-list"))

        resp_two = self.client.get(reverse("api.products:products-list") + "?limit=1")

        resp_three = self.client.get(
            reverse("api.products:products-list") + "?limit=1&offset=2"
        )

        self.assertNotEqual(len(resp_one.json()["results"]), 1)
        self.assertEquals(len(resp_two.json()["results"]), 1)
        self.assertEquals(len(resp_three.json()["results"]), 1)
        self.assertNotEqual(
            resp_two.json()["results"][0]["title"],
            resp_three.json()["results"][0]["title"],
        )

    def test_can_narrow_the_list_by_filter_by(self):
        resp_one = self.client.get(reverse("api.products:products-list") + f'?includeLocationId={self.united_kingdom_id}')
        # five products, including global...
        self.assertEqual(resp_one.json()['count'], 5)

        filtered_response = self.client.get(reverse(
            "api.products:products-list") + f'?includeLocationId={self.united_kingdom_id}&exactLocationId={self.reading_id}')
        self.assertEqual(filtered_response.json()['count'], 2)

        only_filtered_response = self.client.get(reverse(
            "api.products:products-list") + f'?exactLocationId={self.reading_id}')
        self.assertEqual(only_filtered_response.json()['count'], 2)

        self.assertEqual(only_filtered_response.json()['count'], filtered_response.json()['count'])

        multiple_filtered_response = self.client.get(reverse(
            "api.products:products-list") + f'?includeLocationId={self.united_kingdom_id}'
                                            f'&exactLocationId={self.reading_id},{self.slough_id}')
        self.assertEqual(multiple_filtered_response.json()['count'], 3)


@tag('unit')
class GlobalLocationTest(TestCase):
    def setUp(self) -> None:
        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            mapbox_context=["global"],
        )
        united_kingdom.save()


        reading = Location(
            mapbox_id="place.12006143788019830",
            mapbox_text="Reading",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
                "global",
            ],
        )
        reading.save()
        self.reading_id = reading.id

        reading_mbl = Location(
            mapbox_id="place.12006143788019830",
            mapbox_placename="Reading, Reading, England, United Kingdom",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
            ],
        )
        reading_mbl.save()

        uk_product = Product(
            title="Something in the whole of the UK",
            url="https://vonq.com/somethinglkasjdfhg",
        )
        uk_product.save()
        uk_product.locations.add(united_kingdom)
        uk_product.save()

    def test_specific_query_yield_general_results(self):
        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?includeLocationId={self.reading_id}"
        )
        self.assertEqual(len(resp.json()["results"]), 1)


class LocationCardinalityFilterTestCase(TestCase):
    def setUp(self) -> None:
        united_kingdom = Location(
            mapbox_id="country.12405201072814600",
            mapbox_text="UK",
            # "continent" here only serves to allow test assertions
            # on sorting to work deterministically here
            mapbox_context=["continent.europe", "global"],
            # note that there is no "global" context for those...
        )
        united_kingdom.save()

        england = Location(
            mapbox_id="region.13483278848453920",
            mapbox_text="England",
            mapbox_context=["country.12405201072814600", "continent.europe", "global"],
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
                "global",
            ],
        )
        reading.save()

        board_one = Product(
            title="Multi-place board"
        )
        board_one.save()
        board_one.locations.set([united_kingdom, england, reading])
        board_one.save()

    def test_only_returns_one_board(self):
        resp = self.client.get(reverse('api.products:products-list'))
        self.assertEqual(resp.json()['count'], 1)
