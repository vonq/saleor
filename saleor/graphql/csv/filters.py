import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Q

from ...app.models import App
from ..core.filters import BaseJobFilter
from ..core.types import FilterInputObjectType


User = get_user_model()


def filter_user(qs, _, value):
    users = User.objects.filter(
        Q(first_name__ilike=value) | Q(last_name__ilike=value) | Q(email__ilike=value)
    ).values("pk")
    return qs.filter(Exists(users.filter(id=OuterRef("user_id"))))


def filter_app(qs, _, value):
    apps = App.objects.filter(name__ilike=value).values("pk")
    return qs.filter(Exists(apps.filter(id=OuterRef("app_id"))))


class ExportFileFilter(BaseJobFilter):
    user = django_filters.CharFilter(method=filter_user)
    app = django_filters.CharFilter(method=filter_app)


class ExportFileFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ExportFileFilter
