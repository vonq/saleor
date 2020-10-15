from rest_framework import serializers

from api.products.models import Product, Location


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField('get_geocoder_id')

    def get_geocoder_id(self, obj):
        return obj.geocoder_id

    class Meta:
        model = Location
        fields = ("id", "name", "place_text", "place_type", "within")
