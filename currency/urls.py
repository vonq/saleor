from rest_framework.routers import DefaultRouter
from api.currency.views import ExchangeRateViewSet, CurrencyViewSet

app_name = "api.currency"

router = DefaultRouter()
router.register(r"currencies", CurrencyViewSet, basename="currencies")
router.register(r"", ExchangeRateViewSet, basename="exchange-rate")

urlpatterns = router.urls
