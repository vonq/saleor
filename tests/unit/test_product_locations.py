from django.test import TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Location, Product, MapboxLocation


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

        global_location = Location(
            # global has a specific name to allow searching just for it
            mapbox_id="global",
            mapbox_text="global",
            mapbox_context=[],
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

    def test_can_get_nested_locations(self):
        # Search for a product within Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + "?includeLocationId=place.12006143788019830"
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEquals(resp.json()["results"][0]["title"], "Something in Reading")

        # Search for a product in England
        resp = self.client.get(
            reverse("api.products:products-list")
            + "?includeLocationId=region.13483278848453920"
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 3)

        # Search for a product in UK
        resp = self.client.get(
            reverse("api.products:products-list")
            + "?includeLocationId=country.12405201072814600"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 4)

        # Search for a product in Slough OR Reading
        resp = self.client.get(
            reverse("api.products:products-list")
            + "?includeLocationId=place.17224449158261700,place.12006143788019830"
        )
        self.assertEqual(len(resp.json()["results"]), 3)

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
            reverse("api.products:products-list") + "?includeLocationId=global"
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
        resp_one = self.client.get(reverse("api.products:products-list") + '?includeLocationId=country.12405201072814600')
        self.assertEqual(resp_one.json()['count'], 4)

        filtered_response = self.client.get(reverse(
            "api.products:products-list") + '?includeLocationId=country.12405201072814600&exactLocationId=place.12006143788019830')
        self.assertEqual(filtered_response.json()['count'], 2)

        only_filtered_response = self.client.get(reverse(
            "api.products:products-list") + '?exactLocationId=place.12006143788019830')
        self.assertEqual(only_filtered_response.json()['count'], 2)

        self.assertEqual(only_filtered_response.json()['count'], filtered_response.json()['count'])

        multiple_filtered_response = self.client.get(reverse(
            "api.products:products-list") + '?includeLocationId=country.12405201072814600'
                                            '&exactLocationId=place.12006143788019830,place.17224449158261700')
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

        reading_mbl = MapboxLocation(
            mapbox_id="place.12006143788019830",
            mapbox_placename="Reading, Reading, England, United Kingdom",
            mapbox_context=[
                "district.17792293837019830",
                "region.13483278848453920",
                "country.12405201072814600",
            ],
            mapbox_data={
                "id": "place.12006143788019830",
                "bbox": [-1.248574, 51.328191, -0.771487, 51.5597],
                "text": "Reading",
                "type": "Feature",
                "center": [-0.97306, 51.45417],
                "context": [
                    {
                        "id": "district.17792293837019830",
                        "text": "Reading",
                        "wikidata": "Q161491",
                    },
                    {
                        "id": "region.13483278848453920",
                        "text": "England",
                        "wikidata": "Q21",
                        "short_code": "GB-ENG",
                    },
                    {
                        "id": "country.12405201072814600",
                        "text": "United Kingdom",
                        "wikidata": "Q145",
                        "short_code": "gb",
                    },
                ],
                "geometry": {"type": "Point", "coordinates": [-0.97306, 51.45417]},
                "relevance": 1,
                "place_name": "Reading, Reading, England, United Kingdom",
                "place_type": ["place"],
                "properties": {"wikidata": "Q161491"},
            },
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
            + "?includeLocationId=place.12006143788019830"
        )
        self.assertEqual(len(resp.json()["results"]), 1)



