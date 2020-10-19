from rest_framework import serializers

from api.products.models import Product, Location


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='geocoder_id')
    place_name = serializers.CharField()
    place_text = serializers.CharField()
    place_type = serializers.CharField()
    within = serializers.CharField()

    class Meta:
        model = Location
        fields = ("id", "place_name", "place_text", "place_type", "within")


class ProductSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("title", "locations")

