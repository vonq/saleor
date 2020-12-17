from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.products.models import Location, JobFunction, JobTitle, Industry
from rest_framework_recursive.fields import RecursiveField


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    fully_qualified_place_name = serializers.CharField()
    place_type = serializers.ListField(
        child=serializers.ChoiceField(choices=Location.TYPE_CHOICES)
    )
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
        read_only_fields = fields


class JobFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFunction
        fields = ("id", "name", "parent")


class JobFunctionTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    children = serializers.ListField(child=RecursiveField())


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


class JobTitleSerializer(serializers.ModelSerializer):
    job_function = LimitedJobFunctionSerializer(read_only=True, many=False)

    class Meta:
        model = JobTitle
        fields = ("id", "name", "job_function")


class LimitedChannelSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    type = serializers.CharField(read_only=True)
    id = serializers.IntegerField()


class ProductSerializer(serializers.Serializer):
    @staticmethod
    def get_homepage(product):
        if product.url:
            return product.url
        if product.channel:
            return product.channel.url
        return None

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

    @staticmethod
    def get_title(product):
        return product.external_product_name

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
    title = serializers.SerializerMethodField()
    channel = LimitedChannelSerializer(read_only=True)
    product_id = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class ProductSearchSerializer(serializers.Serializer):
    includeLocationId = serializers.CharField(required=False)
    exactLocationId = serializers.CharField(required=False)
    industryId = serializers.CharField(required=False)
    jobTitleId = serializers.IntegerField(required=False)
    jobFunctionId = serializers.IntegerField(required=False)
    durationFrom = serializers.IntegerField(required=False)
    durationTo = serializers.IntegerField(required=False)

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


class ChannelSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    products = serializers.ListField(
        child=ProductSerializer(read_only=True), source="product_set.all"
    )
    type = serializers.CharField(read_only=True)
