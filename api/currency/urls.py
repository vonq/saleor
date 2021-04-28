from django.urls import path
from rest_framework.routers import DefaultRouter

from api.currency.views import (
    ExchangeRateViewSet,
    CurrencyViewSet,
    DatedExchangeRateView,
)

app_name = "api.currency"

router = DefaultRouter()
router.register(r"currencies", CurrencyViewSet, basename="currencies")
router.register(r"", ExchangeRateViewSet, basename="exchange-rate")

urlpatterns = router.urls + [
    path(
        r"<str:currency>/<str:datetime>/",
        DatedExchangeRateView.as_view({"get": "retrieve"}),
        name="dated-exchange-rate",
    )
]
