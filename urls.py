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
from django.contrib import admin
from django.urls import path, include, re_path

from drf_yasg2 import openapi
from drf_yasg2.views import get_schema_view
from rest_framework import permissions

from api.products.views import LocationSearchViewSet, JobTitleSearchViewSet, JobFunctionsViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="VONQ Product Knowledge Base API",
        default_version='v1'
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('health/?$', include('health_check.urls')),
    path(r"locations/", LocationSearchViewSet.as_view({'get': 'list'}), name="locations"),
    path('products/', include('api.products.urls', namespace="products")),
    path(r"job-functions/", JobFunctionsViewSet.as_view({'get': 'list'}), name="job-functions"),
    path(r"job-titles/", JobTitleSearchViewSet.as_view({'get': 'list'}), name="job-titles"),
    path(
        r"docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
