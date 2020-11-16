from rest_framework import serializers

from api.products.models import Product, Location, JobFunction, JobTitle, Industry


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    fully_qualified_place_name = serializers.CharField()
    canonical_name = serializers.CharField(allow_null=True)
    within = serializers.CharField(allow_null=True)
    context = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = Location
        fields = (
            "id",
            "fully_qualified_place_name",
            "canonical_name",
            "place_type",
            "within",
            "context",
        )


class JobFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFunction
        fields = ("id", "name", "parent")


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


class ProductSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_homepage(product):
        return product.url

    @staticmethod
    def get_type(product):
        return product.salesforce_product_type

    @staticmethod
    def get_product_id(product):
        return (
            product.desq_product_id
            if product.desq_product_id
            else product.salesforce_id
        )

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

    locations = LocationSerializer(many=True, read_only=True)
    job_functions = JobFunctionSerializer(many=True, read_only=True)
    industries = IndustrySerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    time_to_process = serializers.SerializerMethodField()
    vonq_price = serializers.SerializerMethodField()
    ratecard_price = serializers.SerializerMethodField()
    cross_postings = serializers.SerializerMethodField()
    homepage = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    product_id = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
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
