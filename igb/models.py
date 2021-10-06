import json
import base64
import uuid

import dicttoxml
from django.db import models

from django.conf import settings

from api.igb.encryption import AESCypher
from api.products.models import Channel


class Contract(models.Model):
    contract_id = models.CharField(max_length=48, default=uuid.uuid4)
    customer_name = models.CharField(max_length=80, blank=True, null=True)
    customer_id = models.CharField(max_length=80)
    channel = models.ForeignKey(
        "products.Channel", on_delete=models.SET_NULL, null=True
    )
    credentials = models.TextField()
    facets = models.JSONField()

    def __str__(self):
        return f"({self.id}) for {self.customer_name} on {self.channel.name}"

    def encrypt_credentials(self, credentials: dict):
        credentials = json.dumps(credentials)
        cipher = AESCypher(settings.CREDENTIALS_STORAGE_KEY)
        encoded_credentials = base64.b64encode(
            json.dumps(credentials).encode()
        ).decode()
        self.credentials = cipher.encrypt(encoded_credentials)

    @property
    def decrypted_credentials(self):
        cipher = AESCypher(settings.CREDENTIALS_STORAGE_KEY)
        decrypted = cipher.decrypt(self.credentials)
        decoded = base64.b64decode(decrypted)
        return json.loads(decoded)

    @property
    def transport_credentials(self):
        cipher = AESCypher(settings.CREDENTIALS_TRANSPORT_KEY)
        credentials = self.decrypted_credentials
        credentials = dicttoxml.dicttoxml(json.loads(credentials)).decode()
        encoded_credentials = base64.b64encode(
            json.dumps(credentials).encode()
        ).decode()
        return cipher.encrypt(encoded_credentials)

    @classmethod
    def create_encrypted(cls, **kwargs):
        contract = cls(**kwargs)
        contract.encrypt_credentials(contract.credentials)  # noqa
        contract.save()
        return contract
