"""
Test settings for PostgreSQL testing in the Homeless Resource Directory.

This module provides test-specific settings for PostgreSQL to ensure
all tests run against the same database engine as production.
"""

from .development_settings import *

# Override database settings for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_resource_directory",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5433",
        "TEST": {
            "NAME": "test_resource_directory_test",
        },
    }
}

# Disable GIS for tests (match production)
GIS_ENABLED = False

# Disable static files collection during tests
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Use faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# Test-specific settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Disable debug toolbar during tests
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False,
}

# Use in-memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable email sending during tests
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Test-specific middleware (remove debug toolbar)
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE 
    if "debug_toolbar" not in middleware
]

# Test-specific installed apps (remove debug toolbar)
INSTALLED_APPS = [
    app for app in INSTALLED_APPS 
    if "debug_toolbar" not in app
]
