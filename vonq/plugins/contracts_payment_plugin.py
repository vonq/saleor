import json
from dataclasses import dataclass
from typing import List, Dict, Optional

from django.contrib.auth import get_user_model
from django.db.models import Model
from simple_salesforce import SalesforceResourceNotFound

from saleor.checkout.models import Checkout
from saleor.payment.interface import GatewayResponse, PaymentData, PaymentGateway
from saleor.plugins.base_plugin import BasePlugin

from api.salesforce.sync import login

User = get_user_model()  # type: Model


@dataclass
class Contract:
    customer_id: str
    contract_id: str
    balance: int

    def can_charge(self, amount):
        return self.balance >= amount


class InsufficientFunds(Exception):
    pass


class NonExistentContract(Exception):
    pass


class ContractsRepository:
    contracts_endpoint = "contracts/account/{customer_id}/"

    def get_contracts_by_customer_id(self, customer_id: str) -> Dict[str, Contract]:
        client = login()
        contracts = client.apexecute(
            self.contracts_endpoint.format(customer_id=customer_id), method="GET"
        )
        return {
            contract["id"]: Contract(
                customer_id=customer_id,
                balance=contract["remainingbudget__c"],
                contract_id=contract["id"],
            )
            for contract in contracts
        }

    def get_contract_by_id(self, contract_id: str) -> Optional[Contract]:
        client = login()
        try:
            resp = client.Contract.get(contract_id)
        except SalesforceResourceNotFound:
            return None
        return Contract(
            customer_id=resp["AccountId"],
            contract_id=resp["Id"],
            balance=resp["RemainingBudget__c"],
        )

    @staticmethod
    def get_customer_id_from_email(customer_email: str) -> Optional[str]:
        try:
            user = User.objects.get(email=customer_email)
        except User.DoesNotExist:
            return None
        return user.metadata.get("customer_id")

    def user_has_contract(self, email: str, contract_id: str) -> bool:
        if user := self.get_customer_id_from_email(email):
            if contract := self.get_contract_by_id(contract_id):
                return True
        return False

    def charge_contract(self, customer_id: str, contract_id: str, billed_amount: float):
        contracts = self.get_contracts_by_customer_id(customer_id)
        contract = contracts.get(contract_id)
        if contract:
            if contract.can_charge(billed_amount):
                contract.balance -= billed_amount
            else:
                raise InsufficientFunds(
                    "Cannot charge contract because of insufficient funds"
                )
        else:
            raise NonExistentContract


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
    DEFAULT_ACTIVE = True
    CONTRACTS_REPOSITORY = ContractsRepository()

    def get_client_token(self, token_config, previous_value):
        return previous_value

    def get_payment_gateways(
        self, currency: Optional[str], checkout: Optional["Checkout"], previous_value
    ) -> List["PaymentGateway"]:
        if checkout:
            previous_value = checkout.email
        # pass the customer email here to understand who is that
        return super().get_payment_gateways(currency, checkout, previous_value)

    def get_payment_config(self, customer_email):
        # this one returns a list of configuration after
        # you call the createCheckout mutation
        customer_id = self.CONTRACTS_REPOSITORY.get_customer_id_from_email(
            customer_email
        )
        if not customer_id:
            return []
        contracts = self.CONTRACTS_REPOSITORY.get_contracts_by_customer_id(customer_id)
        return [
            {
                "field": contract.contract_id,
                "value": json.dumps({"balance": float(contract.balance)}),
            }
            for contract in contracts.values()
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
        token = payment_information.token
        contract = self.CONTRACTS_REPOSITORY.get_contract_by_id(token)
        if not self.CONTRACTS_REPOSITORY.user_has_contract(
            payment_information.customer_email, token
        ):
            return GatewayResponse(
                is_success=False,
                action_required=False,
                kind="capture",
                error=f"User doesn't have conract",
                amount=payment_information.amount,
                currency=payment_information.currency,
                transaction_id="",
            )
        if not contract:
            return GatewayResponse(
                is_success=False,
                action_required=False,
                kind="capture",
                error=f"No contract available for {token}",
                amount=payment_information.amount,
                currency=payment_information.currency,
                transaction_id="1234",
            )
        if not contract.can_charge(payment_information.amount):
            return GatewayResponse(
                is_success=False,
                action_required=False,
                kind="capture",
                error="Insufficient funds!",
                amount=payment_information.amount,
                currency=payment_information.currency,
                transaction_id="1234",
            )
        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind="capture",
            error=None,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id="1234",  # TODO
            customer_id=payment_information.token,  # This is a workaround!
        )

    def get_supported_currencies(self, previous_value):
        return ["EUR", "GBP", "USD"]
