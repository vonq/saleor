from rest_framework import serializers


class ExchangeRateSerializer(serializers.Serializer):
    rate = serializers.SerializerMethodField()
    code = serializers.CharField(source="target_currency.code")
    date = serializers.DateField()

    def get_rate(self, exchange_rate):
        if exchange_rate.rate:
            return round(exchange_rate.rate, 2)


class CurrencySerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
