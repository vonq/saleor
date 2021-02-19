from typing import Optional, Dict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_recursive.fields import RecursiveField

from api.currency.conversion import convert
from api.currency.models import ExchangeRate
from api.products.docs import CommonParameters
from api.products.models import Location, JobFunction, JobTitle, Industry, Channel
from api.products.area import bounding_box_area

from uuid import UUID


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    fully_qualified_place_name = serializers.CharField()
    place_type = serializers.ListField(
        child=serializers.ChoiceField(choices=Location.TYPE_CHOICES)
    )
    canonical_name = serializers.CharField(allow_null=True)
    within = RecursiveField(allow_null=True)

    area = serializers.SerializerMethodField()
    bounding_box = serializers.ListField(
        child=serializers.FloatField(), source="mapbox_bounding_box"
    )

    def get_area(self, location):
        if location.mapbox_bounding_box:
            return bounding_box_area(location)

    class Meta:
        model = Location
        fields = (
            "id",
            "fully_qualified_place_name",
            "canonical_name",
            "place_type",
            "within",
            "area",
            "bounding_box",
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
    job_function = serializers.SerializerMethodField(
        method_name="get_job_function_of_self_or_canonical"
    )

    def get_job_function_of_self_or_canonical(self, job_title):
        if job_title.job_function:
            return LimitedJobFunctionSerializer(
                job_title.job_function, read_only=True, many=False
            ).data
        elif job_title.alias_of and job_title.alias_of.job_function:
            return LimitedJobFunctionSerializer(
                job_title.alias_of.job_function, read_only=True, many=False
            ).data
        return None

    class Meta:
        model = JobTitle
        fields = ("id", "name", "job_function")


class LimitedChannelSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    type = serializers.CharField(read_only=True)
    id = serializers.IntegerField()


class ProductSerializer(serializers.Serializer):
    _selected_currency: Optional[str] = None
    _exchange_rates: Dict[str, float] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if not request:
            return

        exchange_rates = ExchangeRate.get_latest_rates().values(
            "target_currency__code", "rate"
        )

        for rate in exchange_rates:
            self._exchange_rates[rate["target_currency__code"]] = float(rate["rate"])

        self._selected_currency = request.query_params.get(
            CommonParameters.CURRENCY.name
        )

    @staticmethod
    def get_homepage(product):
        if product.url:
            return product.url
        if product.channel:
            return product.channel.url
        return None

    @staticmethod
    def get_type(product):
        return getattr(product.channel, "type", None)

    @staticmethod
    def get_cross_postings(product):
        return product.salesforce_cross_postings

    @staticmethod
    def get_logo_url(product):
        return [{"size": "300x200", "url": product.logo_url}]

    @staticmethod
    def get_logo_square_url(product):
        return [{"size": "68x68", "url": product.logo_square_url}]

    @staticmethod
    def get_logo_rectangle_url(product):
        return [{"size": "270x90", "url": product.logo_rectangle_url}]

    @staticmethod
    def get_duration(product):
        return {"range": "days", "period": product.duration_days}

    def get_prices(self, price):
        prices = [{"amount": price, "currency": "EUR"}] + [
            {
                "amount": convert(price, exchange_rate),
                "currency": currency_code,
            }
            for currency_code, exchange_rate in self._exchange_rates.items()
        ]
        if self._selected_currency:
            return filter(lambda x: x["currency"] == self._selected_currency, prices)
        return prices

    def get_vonq_price(self, product):
        prices = self.get_prices(product.unit_price)
        if self._selected_currency:
            return filter(lambda x: x["currency"] == self._selected_currency, prices)
        return prices

    def get_ratecard_price(self, product):
        prices = self.get_prices(product.rate_card_price)
        if self._selected_currency:
            return filter(lambda x: x["currency"] == self._selected_currency, prices)
        return prices

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
    logo_square_url = serializers.SerializerMethodField()
    logo_rectangle_url = serializers.SerializerMethodField()
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
    currency = serializers.CharField(required=False, max_length=3)
    name = serializers.CharField(required=False)
    recommended = serializers.BooleanField(required=False, default=False)
    channelType = serializers.CharField(required=False)
    customerId = serializers.CharField(required=False)

    @property
    def is_recommendation(self) -> bool:
        return bool(self.validated_data.get("recommended"))

    @property
    def is_my_own_product_request(self) -> bool:
        return bool(self.validated_data.get("customerId"))

    @property
    def is_search_request(self) -> bool:
        return any(
            (
                self.validated_data.get("includeLocationId"),
                self.validated_data.get("exactLocationId"),
                self.validated_data.get("industryId"),
                self.validated_data.get("jobTitleId"),
                self.validated_data.get("jobFunctionId"),
                self.validated_data.get("durationFrom"),
                self.validated_data.get("durationTo"),
                self.validated_data.get("name"),
                self.validated_data.get("channelType"),
                self.validated_data.get("customerId"),
            )
        )

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

    def validate_channelType(self, value):
        if value in Channel.Type.values:
            return value
        raise ValidationError(detail="Invalid channel type!")

    def validate_customerId(self, value):
        try:
            UUID(value)
            return value
        except ValueError:
            raise ValidationError(detail="Invalid customer id!")

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
