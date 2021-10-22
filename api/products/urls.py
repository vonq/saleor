from rest_framework.routers import DefaultRouter
from api.products.views import (
    ProductsViewSet,
    IndustriesViewSet,
    AddonsViewSet,
    CategoriesViewSet,
    DeliveryTimeViewSet,
    MocViewset,
)

app_name = "api.products"

router = DefaultRouter()
router.register(r"industries", IndustriesViewSet, basename="industries")
router.register(r"categories", CategoriesViewSet, basename="categories")
router.register(r"addons", AddonsViewSet, basename="addons")
router.register(r"delivery-time", DeliveryTimeViewSet, basename="deliverytime")
router.register(r"mocs", MocViewset, basename="mocs")
router.register(r"", ProductsViewSet, basename="products")

urlpatterns = router.urls
