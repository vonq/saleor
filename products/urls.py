from rest_framework.routers import DefaultRouter

from api.products.views import LocationSearchViewSet, ProductsViewSet

app_name = "api.products"

router = DefaultRouter()
router.register(r"locations", LocationSearchViewSet, basename="locations")
router.register(r"", ProductsViewSet, basename="")
urlpatterns = router.urls
