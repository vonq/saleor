from typing import Optional

import requests

from simple_salesforce import Salesforce


def get_session_id(
    instance_url: str, client_id: str, client_secret: str, username: str, password: str
) -> Optional[str]:
    resp = requests.post(
        f"{instance_url}/services/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "grant_type": "password",
        },
        headers={
            "User-Agent": "curl/7.58.0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    if resp.ok:
        return resp.json()["access_token"]


def get_client(session_id: str, instance_url: str) -> Salesforce:
    return Salesforce(session_id=session_id, instance_url=instance_url, version="50.0")


def get_products_id_from_channel(channel_obj: dict):
    if products := channel_obj.get("Products__r"):
        return [record["Uuid__c"] for record in products["records"]]
    return []
