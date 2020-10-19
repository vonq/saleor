from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from api.products.geocoder import Geocoder
from api.products.models import Location, Product
from api.products.serializers import ProductSerializer, LocationSerializer


class LocationSearchViewSet(viewsets.ModelViewSet):
    http_method_names = ("get",)
    models = Location

    def get_queryset(self):
        text = self.request.query_params['text']
        response = Geocoder.geocode(text)
        location = Location.from_mapbox_response(response)
        return location

    def get_serializer_class(self):
        return LocationSerializer


class ProductsListView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        locations = self.request.query_params.get('locationId')  # type: List

        if locations:
            locations = locations.split(',')
            queryset = Product.objects.get_by_location_ids(locations)

        serializer = ProductSerializer(queryset[:10], many=True)
        return Response(serializer.data)
