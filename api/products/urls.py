from rest_framework.routers import DefaultRouter
from api.products.views import ProductsViewSet, IndustriesViewSet, AddonsViewSet

app_name = "api.products"

router = DefaultRouter()
router.register(r"industries", IndustriesViewSet, basename="industries")
router.register(r"addons", AddonsViewSet, basename="addons")
router.register(r"", ProductsViewSet, basename="products")

urlpatterns = router.urls
