import json

from django.urls import reverse

from api.products.models import Channel, Product
from api.tests import AuthenticatedTestCase
from django.test import override_settings
from api.tests.integration import force_user_login


@override_settings(
    IGB_API_KEY="xxx",
    IGB_API_ENVIRONMENT_ID="xxx",
    IGB_URL="https://api.ingoedebanen.nl/apipartner/hapi/v1/{environment_id}/jobboards",
    CREDENTIALS_STORAGE_KEY="GOsSyvGjCjMiUGKUJin5gNe54P+mdVyiL/i2uvfuzik=",
    CREDENTIALS_TRANSPORT_KEY="GOsSyvGjCjMiUGKUJin5gNe54P+mdVyiL/i2uvfuzik=",
)
class ContractsTestCase(AuthenticatedTestCase):
    CONTRACTS_ENDPOINT = reverse("api.igb:contracts-list")

    def setUp(self) -> None:
        self.channel = Channel.objects.create(
            name="Test Channel",
            type=Channel.Type.JOB_BOARD,
            moc_enabled=True,
            igb_moc_channel_class="Whatever",
            igb_moc_extended_information={
                "facets": [
                    {
                        "facet": {
                            "name": "JobPostingBold",
                            "label": "JobPostingBold",
                            "options": [
                                {
                                    "option": {
                                        "key": "true",
                                        "sort": "10",
                                        "label": "Ja",
                                        "default": "0",
                                    }
                                },
                                {
                                    "option": {
                                        "key": "false",
                                        "sort": "20",
                                        "label": "Nee",
                                        "default": "1",
                                    }
                                },
                            ],
                        }
                    },
                    {
                        "facet": {
                            "name": "PremiumJobAd",
                            "label": "PremiumJobAd",
                            "options": [
                                {
                                    "option": {
                                        "key": "true",
                                        "sort": "10",
                                        "label": "Ja",
                                        "default": "0",
                                    }
                                },
                                {
                                    "option": {
                                        "key": "false",
                                        "sort": "20",
                                        "label": "Nee",
                                        "default": "1",
                                    }
                                },
                            ],
                        }
                    },
                ],
                "credentials": [
                    {
                        "credential": {
                            "name": "Username_DU",
                            "sort": "10",
                            "label": "Username DU",
                            "description": None,
                        }
                    },
                    {
                        "credential": {
                            "name": "Password_DU",
                            "sort": "20",
                            "label": "Password DU",
                            "description": None,
                        }
                    },
                ],
            },
        )

        self.moc_product = Product.objects.create(
            title="This is a MC product",
            salesforce_product_type=Product.SalesforceProductType.JOB_BOARD,
            status=Product.Status.ACTIVE,
            channel_id=self.channel.id,
            moc_only=True,
        )

    def test_a_contract_can_be_registered(self):
        force_user_login(self.client, "mapi")

        resp = self.client.post(
            self.CONTRACTS_ENDPOINT,
            json.dumps(
                {
                    "customer_name": "My Customer",
                    "customer_id": "123",
                    "channel_id": self.channel.id,
                    "credentials": {
                        "Username_DU": "username",
                        "Password_DU": "secret!!!",
                    },
                    "facets": {"PremiumJobAd": True, "JobPostingBold": True},
                }
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(201, resp.status_code)
        self.assertTrue(resp.json().get("contract_id"))

        contract_id = resp.json().get("contract_id")

        resp = self.client.get(
            reverse("api.igb:contracts-detail", kwargs={"contract_id": contract_id}),
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(200, resp.status_code)
        self.assertEqual(contract_id, resp.json().get("contract_id"))

        # cannot retrieve contracts for another user
        resp = self.client.get(
            reverse("api.igb:contracts-detail", kwargs={"contract_id": contract_id}),
            HTTP_X_CUSTOMER_ID="12345",
        )

        self.assertEqual(404, resp.status_code)

    def test_cannot_register_contract_if_not_mapi(self):
        force_user_login(self.client, "hapi")
        resp = self.client.post(
            self.CONTRACTS_ENDPOINT,
            json.dumps(
                {
                    "customer_name": "My Customer",
                    "customer_id": "123",
                    "channel_id": self.channel.id,
                    "credentials": {
                        "Username_DU": "username",
                        "Password_DU": "secret!!!",
                    },
                    "facets": {"PremiumJobAd": True, "JobPostingBold": True},
                }
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(403, resp.status_code)

    def test_can_validate_wrong_credentials(self):
        force_user_login(self.client, "mapi")
        resp = self.client.post(
            self.CONTRACTS_ENDPOINT,
            json.dumps(
                {
                    "customer_name": "My Customer",
                    "customer_id": "123",
                    "channel_id": self.channel.id,
                    "credentials": {
                        "USERNAME": "username",
                        "PASSWORD": "secret!!!",
                    },
                    "facets": {"PremiumJobAd": True, "JobPostingBold": True},
                }
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(400, resp.status_code)
        self.assertEqual(
            ["Malformed Credentials: check expected credentials for channel"],
            resp.json(),
        )

    def test_can_validate_facets(self):
        force_user_login(self.client, "mapi")
        resp = self.client.post(
            self.CONTRACTS_ENDPOINT,
            json.dumps(
                {
                    "customer_name": "My Customer",
                    "customer_id": "123",
                    "channel_id": self.channel.id,
                    "credentials": {
                        "Username_DU": "username",
                        "Password_DU": "secret!!!",
                    },
                    "facets": {"Premium": True, "Bold": True},
                }
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(400, resp.status_code)
        self.assertEqual(
            ["Malformed Facets: check expected facets for channel"], resp.json()
        )

    def test_can_validate_contracts(self):
        force_user_login(self.client, "internal")

        resp = self.client.post(
            self.CONTRACTS_ENDPOINT,
            json.dumps(
                {
                    "customer_name": "My Customer",
                    "customer_id": "123",
                    "channel_id": self.channel.id,
                    "credentials": {
                        "Username_DU": "username",
                        "Password_DU": "secret!!!",
                    },
                    "facets": {"PremiumJobAd": True, "JobPostingBold": True},
                }
            ),
            content_type="application/json",
        )

        contract_id = resp.json().get("contract_id")

        # validate a valid contract for a MC product
        resp = self.client.post(
            reverse("api.igb:contracts-validate"),
            json.dumps(
                [
                    {
                        "contract_id": contract_id,
                        "product_id": str(self.moc_product.product_id),
                    }
                ]
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(200, resp.status_code)

        # cannot validate with a wrong customer id
        resp = self.client.post(
            reverse("api.igb:contracts-validate"),
            json.dumps(
                [
                    {
                        "contract_id": contract_id,
                        "product_id": str(self.moc_product.product_id),
                    }
                ]
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="1234",
        )

        self.assertEqual(400, resp.status_code)

        # cannot validate an invalid payload
        resp = self.client.post(
            reverse("api.igb:contracts-validate"),
            json.dumps(
                {
                    "contract_id": contract_id,
                    "product_id": str(self.moc_product.product_id),
                }
            ),
            content_type="application/json",
            HTTP_X_CUSTOMER_ID="123",
        )

        self.assertEqual(400, resp.status_code)
