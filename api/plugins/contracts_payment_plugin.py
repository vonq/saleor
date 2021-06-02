import json
from dataclasses import dataclass

from saleor.payment.interface import GatewayResponse, PaymentData
from saleor.plugins.base_plugin import BasePlugin



@dataclass
class Contract:
    customer_id: str
    balance: int

    def can_charge(self, amount):
        return self.balance >= amount


class InsufficientFunds(Exception):
    pass

class ContractsRepository:

    contracts = {
        'customer_1': Contract('customer_1', 100),
        'customer_2': Contract('customer_1', 100)
    }

    @classmethod
    def get_contract_by_customer_id(cls, customer_id):
        return cls.contracts.get(customer_id)


    @classmethod
    def charge_contract(cls, customer_id, billed_amount):
        contract = cls.get_contract_by_customer_id(customer_id)
        if contract:
            if contract.can_charge(billed_amount):
                contract.balance -= billed_amount
            else:
                raise InsufficientFunds("Cannot charge contract because of insufficient funds")


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
        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind="capture",
            error=None,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id='1234', # TODO
            customer_id=payment_information.token,  # This is a workaround!
        )

    def get_supported_currencies(self, previous_value):
        return ["EUR", "GBP", "USD"]
