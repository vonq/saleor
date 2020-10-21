from rest_framework import serializers

from api.products.models import Product, Location


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='geocoder_id')
    fully_qualified_place_name = serializers.CharField()
    canonical_name = serializers.CharField(allow_null=True)
    within = serializers.CharField(allow_null=True)

    class Meta:
        model = Location
        fields = ("id", "fully_qualified_place_name", "canonical_name", "place_type", "within")


class ProductSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("title", "locations")
