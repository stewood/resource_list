"""
Django settings for resource_directory project.

This module contains all Django settings for the Homeless Resource Directory application.
The application provides a comprehensive system for managing and tracking resources
for people experiencing homelessness, including shelters, food banks, medical services,
and other support organizations.

Key Features:
- Resource management with version control and audit logging
- Role-based permissions (Editor, Reviewer, Admin)
- FTS5 full-text search capabilities
- CSV import/export functionality
- Verification workflow for resource accuracy
- Spatial service areas with GIS support (when enabled)

Environment Variables:
- DJANGO_SECRET_KEY: Secret key for Django (defaults to insecure dev key)
- DEBUG: Enable debug mode (defaults to 0/False)
- ALLOWED_HOSTS: Comma-separated list of allowed hosts
- DATABASE_PATH: Path to SQLite database file
- GIS_ENABLED: Enable GIS features (defaults to 0/False)
- SPATIALITE_LIBRARY_PATH: Path to SpatiaLite library (optional)
- GDAL_LIBRARY_PATH: Path to GDAL library (optional)

For more information on Django settings, see:
https://docs.djangoproject.com/en/5.0/topics/settings/
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-change-me-in-production"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "0") == "1"

# GIS Configuration
GIS_ENABLED = os.environ.get("GIS_ENABLED", "0") == "1"
SPATIALITE_LIBRARY_PATH = os.environ.get("SPATIALITE_LIBRARY_PATH", "")
GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH", "")

# Allow common dev/test hosts by default
_default_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "testserver", "192.168.6.205", "100.93.223.61"]
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", ",".join(_default_hosts)).split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_htmx",
    "directory",
    "audit",
    "importer",
]

# Add GIS apps when GIS is enabled
if GIS_ENABLED:
    INSTALLED_APPS.append("django.contrib.gis")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "resource_directory.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "resource_directory.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Database configuration
if GIS_ENABLED:
    # Use SpatiaLite when GIS is enabled
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": os.environ.get("DATABASE_PATH", BASE_DIR / "data" / "db.sqlite3"),
            "OPTIONS": {
                "timeout": 20,
            },
        }
    }
    
    # Note: SpatiaLite library path is auto-detected by Django GIS
else:
    # Use regular SQLite when GIS is disabled
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("DATABASE_PATH", BASE_DIR / "data" / "db.sqlite3"),
            "OPTIONS": {
                "timeout": 20,
            },
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# Use absolute URL prefix for static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# WhiteNoise configuration for serving static files in production
# and locally when DEBUG is False
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login URL configuration
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/admin/login/"

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Resource Directory specific settings
RESOURCE_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("needs_review", "Needs Review"),
    ("published", "Published"),
]

# Validation settings
MIN_DESCRIPTION_LENGTH = 20
VERIFICATION_EXPIRY_DAYS = 180

# GIS-specific settings
if GIS_ENABLED:
    # Coordinate system for spatial data (WGS84)
    SPATIAL_REFERENCE_SYSTEM = 4326
    
    # Geometry simplification tolerance for display (in degrees)
    GEOMETRY_SIMPLIFICATION_TOLERANCE = 0.001
    
    # Maximum vertices for uploaded polygons
    MAX_POLYGON_VERTICES = 10000
    
    # Geocoding settings
    GEOCODING_CACHE_EXPIRY_DAYS = 30
    GEOCODING_RATE_LIMIT_PER_MINUTE = 60
