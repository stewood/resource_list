"""
Django settings for PostgreSQL database on Render with PostGIS support.
This file contains the database configuration for the cloud deployment with GIS functionality.
"""

import os
from pathlib import Path
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cloud-migration-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']  # Configure appropriately for production

# GIS Configuration - Test PostGIS availability
GIS_ENABLED = True

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# PostgreSQL database configuration for Render with PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'isaiah58_resources',
        'USER': 'isaiah58_user',
        'PASSWORD': 'CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr',
        'HOST': 'dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Add GIS apps when GIS is enabled
if GIS_ENABLED and "django.contrib.gis" not in INSTALLED_APPS:
    INSTALLED_APPS.append("django.contrib.gis")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Skip SQLite-specific migrations for PostgreSQL
MIGRATION_MODULES = {
    'directory': 'directory.migrations_postgresql',
}

# Skip problematic migrations
MIGRATION_EXCLUDE = [
    ('directory', '0002_add_fts5_search'),
    ('audit', '0002_add_immutability_triggers'),
]

# GIS-specific settings
SPATIAL_REFERENCE_SYSTEM = 4326
GEOMETRY_SIMPLIFICATION_TOLERANCE = 0.001
MAX_POLYGON_VERTICES = 10000
GEOCODING_CACHE_EXPIRY_DAYS = 30
GEOCODING_RATE_LIMIT_PER_MINUTE = 60
