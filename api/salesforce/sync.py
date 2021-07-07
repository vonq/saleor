import json
from functools import lru_cache
from typing import Optional

from django.conf import settings
from django_q.conf import logger
from simple_salesforce import SalesforceResourceNotFound, format_soql, SalesforceError

from api.products.models import Product
from api.salesforce.salesforce_client import get_session_id, get_client


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
        "JMP_Product_Name__c": product_instance.title_en,
        "Channel__c": getattr(product_instance.channel, "salesforce_id", None),
        "Customer__c": get_accounts_by_qprofile_id(product_instance.customer_id)[0][
            "Id"
        ]
        if product_instance.customer_id
        else None,
        "Description": product_instance.description,
        "Product_Logo__c": product_instance.logo_url,
        "IsActive": product_instance.is_active,
        "Available_in_ATS__c": product_instance.available_in_ats,
        "Available_in_JMP__c": product_instance.available_in_jmp,
        "Duration__c": product_instance.duration_days,
        "TimeToGoLive__c": product_instance.supplier_time_to_process,
        "Product_Status__c": None
        if product_instance.status == Product.Status.ACTIVE
        else product_instance.status,
        "Type__c": cast_none(product_instance.salesforce_product_type),
        "Target_Group__c": cast_none(product_instance.audience_group.capitalize()),
        "Product_Category__c": cast_none(product_instance.salesforce_product_category),
        "Cross_Posting__c": json.dumps(getattr(product_instance, "cross_postings", [])),
        "Recommended_product__c": product_instance.is_recommended,
        "HTML_Required__c": product_instance.posting_requirements.filter(
            posting_requirement_type="HTML Posting"
        ).count()
        > 0,
        "Tracking_Method__c": cast_none(product_instance.tracking_method),
        "Pricing_Method__c": cast_none(product_instance.pricing_method),
        "PurchasePriceMethod__c": cast_none(product_instance.purchase_price_method),
        "Product_Solution__c": cast_none(product_instance.salesforce_product_solution),
        "Remarks__c": str(product_instance.remarks),
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
        logger.warning(f"No pricebook entry for {product_instance.product_id}")
        return False
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
    return True


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
            "SELECT Id, Name, Type FROM Account WHERE Id IN {ids}",
            ids=ids,
        )
    )
    return accounts["records"]


@lru_cache
def get_qprofile_accounts(query):
    client = login()

    accounts = client.query(
        format_soql(
            "SELECT Id, Name, Type, Qprofile_ID__c FROM Account WHERE Type='Customer' AND Name LIKE '%{:like}%' AND Qprofile_ID__c != null",
            query,
        )
    )
    return accounts["records"]


@lru_cache
def get_accounts_by_qprofile_id(qprofile_id):
    client = login()
    accounts = client.query(
        format_soql(
            "SELECT Id, Name, Type, Qprofile_ID__c FROM Account WHERE Qprofile_ID__c = '%s'"
            % qprofile_id,
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

    client.bulk.Product2.upsert(products_to_link, external_id_field="Uuid__c")
    channel_instance.mark_as_synced()


def update_product(product_instance):
    logger.info(f"Updating product {product_instance.salesforce_id}...")
    client = login()
    try:
        salesforce_product = client.Product2.get_by_custom_id(
            "Uuid__c", product_instance.salesforce_id
        )
    except SalesforceResourceNotFound as e:
        logger.error(
            f"Couldn't find any product with external id {product_instance.salesforce_id} to update: {e}"
        )
        product_instance.mark_sync_failed()
        return

    product = make_salesforce_product(product_instance)
    product.pop("Uuid__c")
    product_id = salesforce_product["Id"]

    try:
        resp = client.Product2.update(product_id, product)
    except SalesforceError as e:
        logger.error(
            f"Error {e.__class__.__name__} when updating product {product_instance.salesforce_id} in Salesforce: {e}"
        )
        product_instance.mark_sync_failed()
        return

    if resp >= 400:
        logger.error(
            f"Couldn't sync product {product_instance.salesforce_id} with SF: update call response code was {resp}"
        )
        product_instance.mark_sync_failed()
        return

    if not update_pricebook(client, product_id, product_instance):
        logger.warning(
            f"Attempting to create a pricebook entry for {product_instance.salesforce_id}"
        )
        if not create_pricebook_entry(client, product_instance, product_id):
            logger.error(
                f"Failed Salesforce sync for product {product_instance.salesforce_id}, couldn't create a pricebook entry"
            )
            product_instance.mark_sync_failed()
            return

    logger.info(
        f"Successfully synced product {product_instance.salesforce_id} with Salesforce"
    )
    product_instance.mark_as_synced()


def create_pricebook_entry(client, product_instance, product_id):
    try:
        client.PriceBookEntry.create(
            {
                "Product2Id": product_id,
                "Pricebook2Id": get_standard_pricebook_id(client),
                "IsActive": True,
                "UnitPrice": product_instance.unit_price,
                "Rate_Card_supplier__c": product_instance.rate_card_price,
                "Purchase_Price__c": product_instance.purchase_price,
            }
        )

    except SalesforceError as e:
        logger.error(
            f"Error {e.__class__.__name__} when creating pricebook entry for product {product_instance.product_id}: {e}"
        )
        return False
    return True


def get_standard_pricebook_id(client):
    resp = client.query("select Id, IsActive from PriceBook2 where IsStandard=True")
    return resp["records"][0]["Id"]


def create_salesforce_product(client, product_instance) -> Optional[str]:
    product = make_salesforce_product(product_instance)
    product_instance.salesforce_id = product["Uuid__c"]
    try:
        resp = client.Product2.create(product)
    except SalesforceError as e:
        logger.error(
            f"Error {e.__class__.__name__} when creating product {product_instance.salesforce_id}: {e}"
        )
        return
    else:
        return resp["id"]


def push_product(product_instance):
    logger.info(
        f"Pushing new product {product_instance.salesforce_id} to SalesForce..."
    )
    client = login()

    product_id = create_salesforce_product(client, product_instance)
    if product_id:
        created = create_pricebook_entry(client, product_instance, product_id)
        if created:
            product_instance.mark_as_synced()
            logger.info(
                f"Successfully synced product {product_instance.salesforce_id} with Salesforce"
            )
            return

    logger.info(f"Failed Salesforce sync for product {product_instance.salesforce_id}")
    product_instance.mark_sync_failed()
