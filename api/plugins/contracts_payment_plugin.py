import json
from typing import List, Optional, Any

from saleor.payment.interface import GatewayResponse, PaymentData, CustomerSource, \
    PaymentGateway
from saleor.plugins.base_plugin import BasePlugin, PluginConfigurationType


class ContractsRepository:
    def get_contract_by_id(self):
        pass

    def charge_contract(self):
        pass


class ContractsPaymentPlugin(BasePlugin):
    PLUGIN_NAME = "Pay with your Contract Balance"
    PLUGIN_ID = "vonq.payments.sf_contracts"
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None
    DEFAULT_CONFIGURATION = [
        {"name": "Public API key", "value": None},
        {"name": "Secret API key", "value": None},
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": "EUR,USD,GBP"},
    ]
    DEFAULT_ACTIVE = False

    def get_client_token(self, token_config, previous_value):
        return previous_value

    def get_payment_config(self, previous_value):
        # this one returns a list of configuration after
        # you call the createCheckout mutation
        return [
            {"field": "contract_1", "value": json.dumps({"balance": 10})},
            {"field": "contract_2", "value": json.dumps({"balance": 20})},
        ]

    def token_is_required_as_payment_input(self, previous_value):
        return False

    def process_payment(
            self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        # all the logic goes here
        # get the contract by id
        # check the balance
        # adjust the balance
        # return status?
        return previous_value

    def get_supported_currencies(self, previous_value):
        return ["EUR", "GBP", "USD"]
