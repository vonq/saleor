import itertools
from typing import Type

from django.db.models import Q, Func, F, Max, IntegerField, Value
from django.db.models.fields.json import KeyTransform
from django.db.models.functions import Cast, Coalesce
from drf_yasg2 import openapi
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from api.products.models import Location


class FilterParametersMixin:
    parameters = []


class FiltersContainer:
    def __init__(self, *filters: Type[FilterParametersMixin]):
        self._filters = filters

    def __iter__(self):
        return iter(self._filters)

    def get_schema_parameters(self):
        return list(
            itertools.chain.from_iterable([item.parameters for item in self._filters])
        )


class ExactLocationIdFilter(filters.BaseFilterBackend, FilterParametersMixin):
    parameters = [
        openapi.Parameter(
            "exactLocationId",
            in_=openapi.IN_QUERY,
            description="Match only for products assigned to a location id",
            type=openapi.TYPE_STRING,
            required=False,
            explode=False,
        ),
    ]

    def filter_queryset(self, request, queryset, view):
        filter_by_query = request.query_params.get("exactLocationId")
        if not filter_by_query:
            return queryset
        filter_by_ids = filter_by_query.split(",")

        return queryset.filter(locations__id__in=filter_by_ids)


class IncludeLocationIdFilter(filters.BaseFilterBackend, FilterParametersMixin):
    parameters = [
        openapi.Parameter(
            "includeLocationId",
            in_=openapi.IN_QUERY,
            description="Id for a location. Optionally, a (comma-separated) array of values can be passed.",
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            required=False,
            explode=False,
        )
    ]

    def filter_queryset(self, request, queryset, view):
        location_ids = request.query_params.get("includeLocationId")
        if not location_ids:
            return queryset

        location_ids = location_ids.split(",")

        locations_and_contexts = Location.list_context_locations_ids(location_ids)

        if not locations_and_contexts:
            return queryset

        return queryset.filter(
            Q(locations__mapbox_context__contains=locations_and_contexts)
            | Q(locations__mapbox_id__in=locations_and_contexts)
        ).distinct()  # a .distinct() call is required when using __contains, as it results in a join across locations


class JobFunctionsTitleFilter(filters.BaseFilterBackend, FilterParametersMixin):
    parameters = [
        openapi.Parameter(
            "jobTitleId",
            in_=openapi.IN_QUERY,
            description="Job title id",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "jobFunctionId",
            in_=openapi.IN_QUERY,
            description="Job function id",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ]

    def filter_queryset(self, request, queryset, view):
        job_function_id = request.query_params.get("jobFunctionId")
        job_title_id = request.query_params.get("jobTitleId")

        if job_function_id and job_title_id:
            raise ValidationError(
                detail="Cannot search by both job title and job function. Please use either field."
            )

        if job_function_id:
            return queryset.filter(job_functions__id=job_function_id)

        if job_title_id:
            return queryset.filter(job_functions__jobtitle__id=job_function_id)

        return queryset


class IndustryFilter(filters.BaseFilterBackend, FilterParametersMixin):
    parameters = [
        openapi.Parameter(
            "industryId",
            in_=openapi.IN_QUERY,
            description="Industry Id",
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            required=False,
            explode=False,
        ),
    ]

    def filter_queryset(self, request, queryset, view):
        industry_id_param = request.query_params.get("industryId")
        if not industry_id_param:
            return queryset

        industry_ids = industry_id_param.split(",")

        return queryset.filter(industries__id__in=industry_ids)


class OrderByCardinalityFilter(filters.BaseFilterBackend, FilterParametersMixin):
    def filter_queryset(self, request, queryset, view):
        # TODO: this shouldn't run if we're applying OrderByLocationTrafficShare
        # TODO: find an elegant way to express this logic
        return (
            queryset.annotate(
                # the more specific a location, the longer its context (['place', 'district', 'country'...)
                # so we'll sort by descending cardinality to put most location-specific products first
                locations_cardinality=Max(
                    Func(F("locations__mapbox_context"), function="CARDINALITY")
                )
            )
            .order_by("-locations_cardinality")
            .distinct()
        )


class OrderByLocationTrafficShare(filters.BaseFilterBackend, FilterParametersMixin):
    def filter_queryset(self, request, queryset, view):
        location_id = request.query_params.get("includeLocationId")
        location_ids = location_id.split(",") if location_id else []

        if len(location_ids) > 1:
            # FIXME: the sorting behaviour with multiple source of traffic is undefined
            return queryset

        if not location_id or not Location.objects.filter(id=location_id).exists():
            return queryset

        # get the location we saved as part of the autocomplete
        country_code = Location.objects.filter(id=location_id).first().country_code

        return queryset.annotate(
            popularity=Coalesce(
                Cast(
                    KeyTransform(country_code, "similarweb_top_country_shares"),
                    IntegerField(),
                ),
                Value(0),
            )
        ).order_by("-popularity")
