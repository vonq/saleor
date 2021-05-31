from typing import List, Optional

from saleor.payment.interface import GatewayResponse, PaymentData, CustomerSource, \
    PaymentGateway
from saleor.plugins.base_plugin import BasePlugin


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

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return previous_value

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return previous_value

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return previous_value

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return previous_value

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return previous_value

    def get_supported_currencies(self, previous_value):
        return ["EUR", "GBP", "USD"]

    def get_payment_gateway(
        self, currency: Optional[str], previous_value
    ) -> Optional["PaymentGateway"]:

        return PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=self.configuration,
            currencies=self.get_supported_currencies(previous_value=[]),
        )


    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        return [
            CustomerSource(id="1", gateway="boh"),
            CustomerSource(id="2", gateway="boh"),
        ]
