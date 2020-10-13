from rest_framework import viewsets

from api.products.geocoder import Geocoder
from api.products.models import Location
from api.products.serializers import ProductSerializer, LocationSerializer


class LocationSearchViewSet(viewsets.ModelViewSet):
    http_method_names = ("get",)
    models = Location

    def get_queryset(self):
        text = self.request.query_params['text']
        response = Geocoder.geocode(text)
        return response

    def get_serializer_class(self):
        return LocationSerializer


class ProductsViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return None

    def get_serializer_class(self):
        return ProductSerializer
