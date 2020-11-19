from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.products.models import Product, Location, JobFunction, JobTitle, Industry
from rest_framework_recursive.fields import RecursiveField


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    fully_qualified_place_name = serializers.CharField()
    canonical_name = serializers.CharField(allow_null=True)
    within = RecursiveField(allow_null=True)

    class Meta:
        model = Location
        fields = (
            "id",
            "fully_qualified_place_name",
            "canonical_name",
            "place_type",
            "within",
        )


class JobFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFunction
        fields = ("id", "name", "parent")


class JobFunctionTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    children = serializers.ListField(child=RecursiveField())


class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTitle
        fields = ("id", "name")


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = (
            "id",
            "name",
        )


class LimitedLocationSerializer(serializers.Serializer):
    """
    A serializer for Location objects that doesn't
    follow nested relationships
    """

    id = serializers.IntegerField(read_only=True)
    canonical_name = serializers.CharField(read_only=True)


class LimitedJobFunctionSerializer(serializers.Serializer):
    """
    A serializer for JobFunction objects that doesn't
    follow nested relationships
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class ProductSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_homepage(product):
        return product.url

    @staticmethod
    def get_type(product):
        return product.salesforce_product_type

    @staticmethod
    def get_cross_postings(product):
        return product.salesforce_cross_postings

    @staticmethod
    def get_logo_url(product):
        return [{"size": "300x200", "url": product.logo_url}]

    @staticmethod
    def get_duration(product):
        return {"range": "days", "period": product.duration_days}

    @staticmethod
    def get_vonq_price(product):
        return [{"amount": product.unit_price, "currency": "EUR"}]

    @staticmethod
    def get_ratecard_price(product):
        return [{"amount": product.rate_card_price, "currency": "EUR"}]

    @staticmethod
    def get_time_to_process(product):
        return {"range": "hours", "period": product.time_to_process}

    locations = LimitedLocationSerializer(many=True, read_only=True)
    job_functions = LimitedJobFunctionSerializer(many=True, read_only=True)
    industries = IndustrySerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    time_to_process = serializers.SerializerMethodField()
    vonq_price = serializers.SerializerMethodField()
    ratecard_price = serializers.SerializerMethodField()
    cross_postings = serializers.SerializerMethodField()
    homepage = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        lookup_field = "product_id"
        fields = (
            "title",
            "locations",
            "job_functions",
            "industries",
            "description",
            "homepage",
            "logo_url",
            "duration",
            "time_to_process",
            "product_id",
            "vonq_price",
            "ratecard_price",
            "type",
            "cross_postings",
        )
        read_only_fields = fields


class ProductSearchSerializer(serializers.Serializer):
    includeLocationId = serializers.CharField(required=False)
    exactLocationId = serializers.CharField(required=False)
    industryId = serializers.CharField(required=False)
    jobTitleId = serializers.IntegerField(required=False)
    jobFunctionId = serializers.IntegerField(required=False)

    @staticmethod
    def is_a_valid_integer_array(value):
        """
        Make sure that we're getting a string of comma-separated integers
        """
        try:
            values = list(map(int, value.split(",")))
        except ValueError:
            raise ValidationError(detail="Invalid parameter values, must be integer")
        return values

    def validate_includeLocationId(self, value):
        return self.is_a_valid_integer_array(value)

    def validate_exactLocationId(self, value):
        return self.is_a_valid_integer_array(value)

    def validate_industryId(self, value):
        return self.is_a_valid_integer_array(value)

    def validate(self, attrs):
        if attrs.get("jobTitleId") and attrs.get("jobFunctionId"):
            raise ValidationError(
                detail="Cannot search by both job title and job function. Please use either field."
            )
        return attrs
