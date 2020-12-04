"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
import sys

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from django.contrib import staticfiles

ENV = os.getenv("ENV", "dev")


def is_development() -> bool:
    """ Returns true if environment is development """
    return ENV == "dev"


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if is_development() else False

ALLOWED_HOSTS = (
    [
        ".pkb.web-acceptance.vonq-aws.com",
        ".pkb.web-acceptance.vonq.int",
        ".pkb.web-production.vonq-aws.com",
        ".vonq.int",  # This will cover nginx host renaming for health check
    ]
    + ["localhost"]
    if is_development
    else []
)

# Application definition

INSTALLED_APPS = [
    "algoliasearch_django",
    "corsheaders",
    "modeltranslation",
    "massadmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "health_check",  # required
    "health_check.db",  # stock Django health checkers
    "rest_framework",
    "drf_yasg2",
    "django_q",
    "ajax_select",
    "api",
    "api.products",
    "api.annotations",
    "api.currency",
]

ALGOLIA = {
    "APPLICATION_ID": os.getenv("ALGOLIA_APPLICATION_ID"),
    "API_KEY": os.getenv("ALGOLIA_API_KEY"),
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api.urls"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
}

SWAGGER_SETTINGS = {"USE_SESSION_AUTH": True}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = "staticfiles"
STATIC_URL = "/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://master.djaiqvf4qskm2.amplifyapp.com",
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

LANGUAGES = (
    ("en", "English"),
    ("de", "German"),
    ("nl", "Dutch"),
)

# noinspection PyUnusedName
MODELTRANSLATION_LANGUAGES = ("en", "de", "nl")
# noinspection PyUnusedName
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en", "de", "nl")

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

SIMILARWEB_API_KEY = os.getenv("SIMILARWEB_API_KEY")

MAPBOX_KEY = os.getenv("MAPBOX_ACCESS_TOKEN")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = "eu-central-1"

if is_development():
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

SALESFORCE_SYNC_ENABLED = bool(int(os.getenv("SALESFORCE_SYNC_ENABLED", 0)))

SALESFORCE_DOMAIN = os.getenv("SALESFORCE_DOMAIN")
SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
SALESFORCE_API_USERNAME = os.getenv("SALESFORCE_API_USERNAME")
SALESFORCE_API_PASSWORD = os.getenv("SALESFORCE_API_PASSWORD")

if not is_development():
    sentry_sdk.init(
        dsn="https://a0ea7b5b249d4181b092b5f627fc2067@o218462.ingest.sentry.io/5514267",
        integrations=[DjangoIntegration()],
        environment=ENV,
        send_default_pii=True,
    )


Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 4,
    "timeout": 120,
    "retry": 120,
    "queue_limit": 50,
    "max_attempts": 3,
    "bulk": 10,
    "orm": "default",
    "poll": 1,
}
