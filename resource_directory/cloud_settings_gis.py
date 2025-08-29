"""
PostgreSQL settings with GIS enabled for cloud deployment.
This enables PostGIS functionality for spatial queries and location-based features.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Enable GIS features FIRST (before importing base settings)
GIS_ENABLED = True

# Now import base settings
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cloud-migration-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']  # Configure appropriately for production

# Database - PostgreSQL with PostGIS on Render
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

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# GIS-specific settings
SPATIAL_REFERENCE_SYSTEM = 4326
GEOMETRY_SIMPLIFICATION_TOLERANCE = 0.001
MAX_POLYGON_VERTICES = 10000
GEOCODING_CACHE_EXPIRY_DAYS = 30
GEOCODING_RATE_LIMIT_PER_MINUTE = 60
