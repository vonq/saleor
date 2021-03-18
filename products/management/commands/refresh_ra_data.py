from django.core.management.base import BaseCommand
from api.products.models import Product
import json


class Command(BaseCommand):
    help = """
    Updates Products click frequency data given a file
    
    The data was generated using this query
    ```
    with clicks_per_product_per_campaign as (
        select campaign_id, traffic_source as product_id, sum(unique_visitors) as v from company_campaign_step_source_view
        where date >= '2020-01-01'
        and traffic_source_type = 'vonq-contribution'
        and step = 'cta-click'
        and traffic_source <> ''
        and traffic_source is not null
        and traffic_source <> '0'
        group by traffic_source, campaign_id
    ),
    avg_clicks_per_product_per_campaign as (
        select product_id, cast(avg(v) as integer) as avg_clicks
        from clicks_per_product_per_campaign
        group by product_id
        order by avg(v) desc
    )
    SELECT
        product_id,
        avg_clicks,
           CUME_DIST() OVER (
                ORDER BY avg_clicks
            ) cume_dist_val,
        percent_rank() over (order by avg_clicks) percent_rank_val
    FROM
        avg_clicks_per_product_per_campaign
    order by avg_clicks desc;
    """

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="The path to the json file")

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]
        try:
            with open(json_file, mode="r") as fp:
                j = json.load(fp)
                for row in j:
                    self._update(row)
            self.stdout.write(self.style.SUCCESS("Success"))
        except OSError as e:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % json_file))

    def _update(self, row):
        product = Product.objects.all().filter(product_id=row["product_id"]).first()
        frequency = row["cume_dist_val"]
        if product and frequency != product.ra_click_frequency:
            self.stdout.write(
                f"Updating product {product.product_id} with click frequency {frequency}"
            )
            product.ra_click_frequency = frequency
            product.save()
