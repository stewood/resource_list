"""
Development settings for Resource Directory application.

This module contains Django settings specifically for the development environment
using PostgreSQL in Docker. It inherits from the base settings and overrides
database configuration and other development-specific settings.

Environment Variables:
- DATABASE_URL: PostgreSQL connection string (defaults to Docker container)
- DEBUG: Enable debug mode (defaults to True for development)
- DJANGO_SECRET_KEY: Secret key for Django (defaults to insecure dev key)

Usage:
    python manage.py runserver --settings=resource_directory.development_settings
    python manage.py migrate --settings=resource_directory.development_settings
"""

import os
from pathlib import Path

# Import base settings
from .settings import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env.development file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env.development')
except ImportError:
    pass

# Development-specific settings
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-dev-key-change-in-production"
)

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Database configuration for PostgreSQL in Docker
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "resource_directory_dev"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Disable GIS features in development (match production)
GIS_ENABLED = False

# Development-specific middleware
# Enable debug toolbar for development
if DEBUG:
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ] + MIDDLEWARE

# Add debug toolbar to installed apps
if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

# Debug toolbar configuration
if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
        "::1",
    ]

# Development-specific logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "development.log",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Development-specific static files configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Development-specific email configuration
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development-specific cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Development-specific session configuration
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development-specific security settings
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
