from rest_framework.routers import DefaultRouter

from api.igb.views import ContractViewSet

app_name = "api.igb"

router = DefaultRouter()
router.register(r"contracts", ContractViewSet, basename="contracts")

urlpatterns = router.urls
