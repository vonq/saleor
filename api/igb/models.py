import json
import base64
import uuid
from typing import Dict

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

    def encrypt_credentials(self, credentials: Dict[str, str]):
        cipher = AESCypher(settings.CREDENTIALS_STORAGE_KEY)

        self.credentials = json.dumps(
            {
                k: cipher.encrypt(base64.b64encode(v.encode()).decode())
                for k, v in credentials.items()
            }
        )

    @property
    def decrypted_credentials(self) -> Dict[str, str]:
        cipher = AESCypher(settings.CREDENTIALS_STORAGE_KEY)
        encrypted_credentials = json.loads(self.credentials)

        return {
            k: base64.b64decode(cipher.decrypt(v)).decode()
            for k, v in encrypted_credentials.items()
        }

    @property
    def transport_credentials(self) -> Dict[str, str]:
        cipher = AESCypher(settings.CREDENTIALS_TRANSPORT_KEY)
        credentials = self.decrypted_credentials

        return {k: cipher.encrypt(v) for k, v in credentials.items()}

    @classmethod
    def create_encrypted(cls, **kwargs) -> "Contract":
        contract = cls(**kwargs)
        contract.encrypt_credentials(contract.credentials)  # noqa
        contract.save()
        return contract
