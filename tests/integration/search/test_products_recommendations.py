from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import Channel, JobFunction, Product
from api.products.search.index import ProductIndex
from api.tests import SearchTestCase
from api.tests.integration.search import is_generic_product
from api.vonqtaxonomy.models import (
    JobCategory as VonqJobCategory,
)


@tag("algolia")
@tag("integration")
class ProductRecommendationsTestCase(SearchTestCase):
    model_index_class_pairs = [
        (
            Product,
            ProductIndex,
        )
    ]

    @classmethod
    def setUpSearchClass(cls):
        pkb_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Whatever")

        jobboard_channel = Channel(type=Channel.Type.JOB_BOARD)
        jobboard_channel.save()
        community_channel = Channel(type=Channel.Type.COMMUNITY)
        community_channel.save()
        publication_channel = Channel(type=Channel.Type.PUBLICATION)
        publication_channel.save()
        social_channel = Channel(type=Channel.Type.SOCIAL_MEDIA)
        social_channel.save()

        job_function_for_recommendations = JobFunction(
            name="Job function for recommendations",
            vonq_taxonomy_value_id=pkb_job_category.id,
        )
        job_function_for_recommendations.save()
        cls.job_function_for_recommendations_id = job_function_for_recommendations.id

        for channel in [
            jobboard_channel,
            community_channel,
            publication_channel,
            social_channel,
        ]:
            for i in range(0, 6):
                recommended_product = Product(
                    title=f"recommendation {channel.type} {i}",
                    status=Product.Status.ACTIVE,
                    salesforce_id=f"recommendation {channel.type} {i}",
                    order_frequency=0.1 * i,
                    purchase_price=123,
                    unit_price=123,
                    salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
                    salesforce_product_category=Product.SalesforceProductCategory.GENERIC,
                )
                # one free product with max order frequency
                if i == 6:
                    recommended_product.purchase_price = 0
                    recommended_product.unit_price = 0
                    recommended_product.order_frequency = 1
                # one my own product with max order frequency
                if i == 5:
                    recommended_product.salesforce_product_category = (
                        Product.SalesforceProductCategory.CUSTOMER_SPECIFIC
                    )
                    recommended_product.order_frequency = 1

                recommended_product.save()
                recommended_product.channel = channel

                # keep 1 generic product for each channel type
                if not i == 0:
                    recommended_product.job_functions.add(
                        job_function_for_recommendations
                    )
                recommended_product.save()

    def test_can_recommend_products(self):
        def get_number_of_products_for_channel_type(products, channel_type):
            return len(
                [
                    r
                    for r in products
                    if r.get("channel") and r["channel"].get("type") == channel_type
                ]
            )

        def get_number_of_generic_products(products):
            return len([p for p in products if is_generic_product(p)])

        def get_number_of_niche_products(products):
            return len([p for p in products if not is_generic_product(p)])

        def is_a_free_product_present(products):
            return (
                len([p for p in products if not p["vonq_price"][0]["amount"] > 0]) > 0
            )

        resp = self.client.get(
            reverse("api.products:products-list")
            + f"?jobFunctionId={self.job_function_for_recommendations_id}&recommended=true"
        )

        self.assertEqual(resp.json()["count"], 6)

        response = resp.json()["results"]

        self.assertFalse(is_a_free_product_present(response))
        self.assertEqual(
            get_number_of_products_for_channel_type(
                response, Channel.Type.SOCIAL_MEDIA
            ),
            2,
        )
