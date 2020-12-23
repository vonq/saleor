from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.currency.apps import CurrencyConfig
from api.currency.models import ExchangeRate, Currency
from api.currency.serializers import ExchangeRateSerializer, CurrencySerializer


class ExchangeRateViewSet(ModelViewSet):
    model = ExchangeRate
    permission_classes = [IsAuthenticated]
    serializer_class = ExchangeRateSerializer
    http_method_names = ("get",)
    lookup_field = "target_currency__code"
    # only return the latest exchange rate for each currency
    queryset = ExchangeRate.get_latest_rates()

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of current currency conversion rates for EUR
        """,
        operation_id="List of currency exchange rates",
        tags=[CurrencyConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="List of currencies",
                examples={
                    "application/json": [
                        {"rate": 0.9161, "code": "GBP", "date": "2020-12-21"},
                        {"rate": 1.2173, "code": "USD", "date": "2020-12-21"},
                    ]
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes the current currency conversion rates for EUR for a specific currency
        """,
        operation_id="A currency exchange rate",
        tags=[CurrencyConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=False),
                description="A currency exchange rate",
                examples={
                    "application/json": {
                        "rate": 0.9161,
                        "code": "GBP",
                        "date": "2020-12-21",
                    }
                },
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CurrencyViewSet(GenericViewSet, ListModelMixin):
    model = Currency
    permission_classes = [IsAuthenticated]
    serializer_class = CurrencySerializer
    http_method_names = ("get",)
    queryset = Currency.objects.all()

    @swagger_auto_schema(
        operation_description="""
        This endpoint exposes a list of supported currencies
        """,
        operation_id="Currency list",
        tags=[CurrencyConfig.verbose_name],
        responses={
            200: openapi.Response(
                schema=serializer_class(many=True),
                description="List of currencies",
                examples={
                    "application/json": [
                        {"name": "British Pound", "code": "GBP"},
                        {"name": "US Dollar", "code": "USD"},
                        {"name": "Japanese Yen", "code": "JPY"},
                    ]
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
