from rest_framework import serializers

from api.products.models import Product, Location, JobFunction, JobTitle, Industry


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='geocoder_id')
    fully_qualified_place_name = serializers.CharField()
    canonical_name = serializers.CharField(allow_null=True)
    within = serializers.CharField(allow_null=True)
    context = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = Location
        fields = ("id", "fully_qualified_place_name", "canonical_name", "place_type", "within", "context")


class JobFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFunction
        fields = ('id', 'name', 'parent')


class ProductSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)
    job_functions = JobFunctionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("title", "locations", "job_functions", "industries",)


class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTitle
        fields = ('id', 'name')


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ("id", "name",)
