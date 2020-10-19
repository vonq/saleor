from django.urls import path
from rest_framework.routers import DefaultRouter

from api.products.views import LocationSearchViewSet, ProductsListView

app_name = "api.products"

router = DefaultRouter()
router.register(r"locations", LocationSearchViewSet, basename="locations")
urlpatterns = [
    path(r"", ProductsListView.as_view(), name='products'),
    path(r"locations", LocationSearchViewSet, name='locations')
]
