"""
Staging settings for Render deployment.
This configuration is optimized for staging environment on Render.
"""

import os
from pathlib import Path
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-staging-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', '0') == '1'

# Allow Render domain and common staging hosts
ALLOWED_HOSTS = [
    'isaiah58-resource-directory.onrender.com',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# Add any additional hosts from environment
if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS.extend(os.environ.get('ALLOWED_HOSTS').split(','))

# Disable GIS features to avoid PostGIS dependency
GIS_ENABLED = False

# Database - PostgreSQL on Render
# Use environment variables for database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'isaiah58_resources'),
        'USER': os.environ.get('DB_USER', 'isaiah58_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr'),
        'HOST': os.environ.get('DB_HOST', 'dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use simpler static files storage for staging (no manifest required)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings for staging
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging configuration for staging
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
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cache configuration (use memory cache for staging)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Session configuration
SESSION_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_SECURE = False     # Set to True in production

# Email configuration (use console backend for staging)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable debug toolbar in staging
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

# Remove debug toolbar middleware
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'debug_toolbar' not in mw]
