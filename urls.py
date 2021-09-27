"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg2 import openapi
from drf_yasg2.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from ajax_select import urls as ajax_select_urls

from api.products.admin import get_admin_from_sf_uuid
from api.products.views import (
    LocationSearchViewSet,
    JobTitleSearchViewSet,
    JobFunctionsViewSet,
    ChannelsViewSet,
    FunctionFromTitleViewSet,
    IndexView,
)
from api.settings import is_development

schema_view = get_schema_view(
    openapi.Info(title="VONQ Product Knowledge Base API", default_version="v1"),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path(r"admin/", include("massadmin.urls")),
    path(r"admin/edit/<str:uuid>/", get_admin_from_sf_uuid, name="saleforce-edit"),
    path("admin/", admin.site.urls),
    re_path(r"health/?", include("health_check.urls")),
    path(
        r"locations/", LocationSearchViewSet.as_view({"get": "list"}), name="locations"
    ),
    path("products/", include("api.products.urls", namespace="products")),
    path("exchange/", include("api.currency.urls", namespace="exchange")),
    path("annotations/", include("api.annotations.urls", namespace="annotations")),
    path("vonqtaxonomy/", include("api.vonqtaxonomy.urls", namespace="vonqtaxonomy")),
    path(
        "parse-title-to-function/",
        FunctionFromTitleViewSet.as_view({"get": "list"}),
        name="parse-title-to-function",
    ),
    path(
        r"job-functions/",
        JobFunctionsViewSet.as_view({"get": "list"}),
        name="job-functions",
    ),
    path(
        r"job-titles/",
        JobTitleSearchViewSet.as_view({"get": "list"}),
        name="job-titles",
    ),
    path(r"ajax_select/", include(ajax_select_urls)),
    path(
        r"channels/",
        ChannelsViewSet.as_view({"get": "list"}),
        name="channels",
    ),
    path(
        r"channels/<int:pk>/",
        ChannelsViewSet.as_view({"get": "retrieve"}),
        name="channel-detail",
    ),
    path(
        r"docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(r"", IndexView.as_view(), name="index"),
]

if not is_development():
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
