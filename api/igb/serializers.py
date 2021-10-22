from typing import Dict

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.fields import (
    SerializerMethodField,
    CharField,
    IntegerField,
    JSONField,
)

from api.igb.models import Contract
from api.products.models import Channel


class ContractSerializer(ModelSerializer):
    contract_id = CharField(read_only=True)
    channel_id = IntegerField(required=True)
    credentials = JSONField(required=True)

    class Meta:
        model = Contract
        fields = (
            "customer_name",
            "contract_id",
            "customer_id",
            "channel_id",
            "credentials",
            "facets",
        )

    def create(self, validated_data):
        try:
            channel = Channel.objects.get(
                pk=validated_data["channel_id"], moc_enabled=True
            )
        except Channel.DoesNotExist:
            raise ValidationError(detail="Invalid Channel ID")

        channel_credentials = channel.igb_moc_extended_information["credentials"]
        channel_facets = channel.igb_moc_extended_information["facets"]

        try:
            input_credentials = validated_data["credentials"]
            input_facets = validated_data["facets"]
        except ValueError as e:
            raise ValidationError(detail="Malformed payload: invalid json")

        for credential in channel_credentials:
            key = credential["credential"]["name"]
            if key not in input_credentials:
                raise ValidationError(
                    detail="Malformed Credentials: check expected credentials for channel"
                )

        for facet in channel_facets:
            key = facet["facet"]["name"]
            if key not in input_facets:
                raise ValidationError(
                    detail="Malformed Facets: check expected facets for channel"
                )

        return Contract.create_encrypted(**validated_data)


class DecryptedContractSerializer(ModelSerializer):
    class Meta:
        model = Contract
        fields = (
            "customer_name",
            "contract_id",
            "customer_id",
            "channel_id",
            "credentials",
            "class_name",
            "facets",
        )

    credentials = SerializerMethodField(read_only=True)
    class_name = SerializerMethodField(read_only=True)

    def get_credentials(self, contract: Contract) -> Dict[str, str]:
        return contract.transport_credentials

    def get_class_name(self, contract: Contract) -> str:
        return contract.channel.igb_moc_channel_class


class ValidateContractSerializer(Serializer):
    contract_id = CharField(required=True)
    product_id = CharField(required=True)
