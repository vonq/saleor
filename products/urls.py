from rest_framework.routers import DefaultRouter
from api.products.views import ProductsViewSet, IndustriesViewSet

app_name = "api.products"

router = DefaultRouter()
router.register(r"industries", IndustriesViewSet, basename="industries")
router.register(r"", ProductsViewSet, basename="products")

urlpatterns = router.urls
