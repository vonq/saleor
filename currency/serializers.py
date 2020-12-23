from rest_framework import serializers


class ExchangeRateSerializer(serializers.Serializer):
    rate = serializers.FloatField()
    code = serializers.CharField(source="target_currency.code")
    date = serializers.DateField()


class CurrencySerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
