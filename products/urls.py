from django.urls import path
from rest_framework.routers import DefaultRouter

from api.products.views import LocationSearchViewSet, ProductsViewSet

app_name = "api.products"

router = DefaultRouter()
router.register(r"locations", LocationSearchViewSet, basename="locations")
urlpatterns = [
    path(r"", ProductsViewSet.as_view({'get': 'list'}), name='products'),
    path(r"locations", LocationSearchViewSet, name='locations')
]
