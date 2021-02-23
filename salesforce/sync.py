import json
import logging
from functools import lru_cache

from django.conf import settings
from simple_salesforce import SalesforceResourceNotFound, format_soql

from api.salesforce.salesforce_client import get_session_id, get_client

logger = logging.getLogger(__name__)


class RemoteProductNotFound(Exception):
    pass


class SyncProductError(Exception):
    pass


class CreatePricebookEntryError(Exception):
    pass


def login():
    # TODO: Switch to a security token
    #       to avoid the extra login step.
    session_id = get_session_id(
        instance_url=settings.SALESFORCE_DOMAIN,
        client_id=settings.SALESFORCE_CLIENT_ID,
        client_secret=settings.SALESFORCE_CLIENT_SECRET,
        username=settings.SALESFORCE_API_USERNAME,
        password=settings.SALESFORCE_API_PASSWORD,
    )
    client = get_client(session_id=session_id, instance_url=settings.SALESFORCE_DOMAIN)
    return client


def make_salesforce_product(product_instance):
    return {
        # a newly created product won't have a salesforce_id field, only a product_id
        "Uuid__c": str(product_instance.salesforce_id)
        if product_instance.salesforce_id
        else str(product_instance.product_id),
        "Name": product_instance.title_en,
        "Channel__c": getattr(product_instance.channel, "salesforce_id", None),
        "Description": product_instance.description,
        "Product_Logo__c": product_instance.logo_url,
        "IsActive": product_instance.is_active,
        "Available_in_ATS__c": product_instance.available_in_ats,
        "Available_in_JMP__c": product_instance.available_in_jmp,
        "Duration__c": product_instance.duration_days,
        "TimeToGoLive__c": product_instance.time_to_process,
        "Product_Status__c": product_instance.status,
        "Type__c": cast_none(product_instance.salesforce_product_type),
        "Product_Category__c": cast_none(product_instance.salesforce_product_category),
        "Cross_Posting__c": json.dumps(product_instance.salesforce_cross_postings),
        "Recommended_product__c": product_instance.is_recommended,
        "HTML_Required__c": product_instance.has_html_posting,
        "Tracking_Method__c": cast_none(product_instance.tracking_method),
        "Pricing_Method__c": cast_none(product_instance.pricing_method),
        "PurchasePriceMethod__c": cast_none(product_instance.purchase_price_method),
    }


def update_pricebook(client, product_id, product_instance):
    pricebook = client.query(
        format_soql(
            "SELECT Id, Pricebook2Id, Product2Id, CurrencyIsoCode, UnitPrice, Rate_Card_supplier__c FROM PriceBookEntry WHERE Product2Id = {product_id} AND CurrencyIsoCode = 'EUR'",
            product_id=product_id,
        )
    )
    pricebook = pricebook["records"]
    if not pricebook or len(pricebook) > 1:
        return
    pricebook_entry = pricebook[0]
    pricebook_entry_id = pricebook_entry.pop("Id")
    client.PriceBookEntry.update(
        pricebook_entry_id,
        {
            "UnitPrice": product_instance.unit_price,
            "Rate_Card_supplier__c": product_instance.rate_card_price,
            "Purchase_Price__c": product_instance.purchase_price,
        },
    )


@lru_cache
def get_accounts(query):
    client = login()

    accounts = client.query(
        format_soql(
            "SELECT Id, Name, Type FROM Account WHERE Type='Partner' AND Name LIKE '%{:like}%'",
            query,
        )
    )
    return accounts["records"]


@lru_cache
def get_accounts_by_ids(ids):
    client = login()
    accounts = client.query(
        format_soql(
            "SELECT Id, Name, Type FROM Account WHERE Type='Partner' AND Id IN {ids}",
            ids=ids,
        )
    )
    return accounts["records"]


def cast_none(value):
    if value in ["None", "none", "null"]:
        return None
    return value


def update_channel(channel_instance):
    client = login()
    try:
        current_products = client.bulk.Product2.query(
            "SELECT Id, Name, Uuid__c, Channel__c FROM Product2 WHERE Channel__c='%s'"
            % channel_instance.salesforce_id
        )

        current_products_ids = set(map(lambda x: x["Uuid__c"], current_products))

        new_products_ids = set(
            channel_instance.product_set.values_list("salesforce_id", flat=True)
        )
        products_to_unlink_ids, products_to_link_ids = (
            current_products_ids - new_products_ids,
            new_products_ids - current_products_ids,
        )

        products_to_remove = []
        for product in current_products:
            if product["Uuid__c"] in products_to_unlink_ids:
                product["Channel__c"] = None
                products_to_remove.append(product)

        products_to_link = []
        for product_id in products_to_link_ids:
            products_to_link.append(
                {"Uuid__c": product_id, "Channel__c": channel_instance.salesforce_id}
            )

        client.bulk.Product2.upsert(
            products_to_remove + products_to_link, external_id_field="Uuid__c"
        )

        client.Channel__c.update(
            channel_instance.salesforce_id,
            {
                "Name": channel_instance.name,
                "Website__c": channel_instance.url,
                "Account__c": channel_instance.salesforce_account_id,
                "IsDeleted": not channel_instance.is_active,
            },
        )

    except SalesforceResourceNotFound as e:
        logger.error(
            "Resource %s couldn't be found on %s"
            % (channel_instance.salesforce_id, client.domain)
        )
    else:
        channel_instance.mark_as_synced()


def push_channel(channel_instance):
    client = login()

    account_id = channel_instance.salesforce_account_id

    resp = client.Channel__c.create(
        {
            "Name": channel_instance.name,
            "Website__c": channel_instance.url,
            "Account__c": account_id,
            "IsDeleted": not channel_instance.is_active,
        },
    )
    if not resp["success"]:
        logger.error(resp)
        return

    channel_instance.salesforce_id = resp["id"]
    channel_instance.save()

    new_products = channel_instance.product_set.all()

    products_to_link = []
    for product in new_products:
        products_to_link.append(
            {
                "Uuid__c": product.salesforce_id,
                "Channel__c": channel_instance.salesforce_id,
                "Name": product.title_en,
            }
        )

    resp = client.bulk.Product2.upsert(products_to_link, external_id_field="Uuid__c")
    channel_instance.mark_as_synced()


def update_product(product_instance):
    client = login()
    try:
        salesforce_product = client.Product2.get_by_custom_id(
            "Uuid__c", product_instance.salesforce_id
        )
    except SalesforceResourceNotFound:
        raise RemoteProductNotFound(
            f"Couldn't find any product with external id {product_instance.salesforce_id}"
        )

    product = make_salesforce_product(product_instance)
    product.pop("Uuid__c")
    product_id = salesforce_product["Id"]

    resp = client.Product2.update(product_id, product)
    if resp >= 400:
        raise SyncProductError(
            f"Couldn't sync product {product_instance.title} with SF"
        )

    update_pricebook(client, product_id, product_instance)

    product_instance.mark_as_synced()


def create_pricebook_entry(client, product_instance, product_id):
    resp = client.PriceBookEntry.create(
        {
            "Product2Id": product_id,
            "Pricebook2Id": get_standard_pricebook_id(client),
            "IsActive": True,
            "UnitPrice": product_instance.unit_price,
            "Rate_Card_supplier__c": product_instance.rate_card_price,
            "Purchase_Price__c": product_instance.purchase_price,
        }
    )

    if not resp["success"]:
        logger.error(resp)
        raise CreatePricebookEntryError(
            f"Could not create pricebook entry for product {product_id}"
        )


def get_standard_pricebook_id(client):
    resp = client.query("select Id, IsActive from PriceBook2 where IsStandard=True")
    return resp["records"][0]["Id"]


def create_salesforce_product(client, product_instance):
    product = make_salesforce_product(product_instance)
    resp = client.Product2.create(product)
    if not resp["success"]:
        logger.error(resp)
        raise SyncProductError(f"Error creating product {product_instance.product_id}")
    product_instance.salesforce_id = product["Uuid__c"]
    return resp["id"]


def push_product(product_instance):
    client = login()

    product_id = create_salesforce_product(client, product_instance)

    create_pricebook_entry(client, product_instance, product_id)

    product_instance.mark_as_synced()
