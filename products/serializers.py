from rest_framework import serializers

from api.products.models import ChannelProduct, Location


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelProduct
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"