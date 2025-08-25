"""
Django settings for PostgreSQL database on Render.
This file contains the database configuration for the cloud deployment.
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

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# PostgreSQL database configuration for Render
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
