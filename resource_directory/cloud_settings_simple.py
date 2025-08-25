"""
Simple PostgreSQL settings for cloud migration.
This uses Django's migration system properly.
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

# Disable GIS features to avoid PostGIS dependency
GIS_ENABLED = False

# Database - PostgreSQL on Render
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
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
