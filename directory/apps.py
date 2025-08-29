"""
Django app configuration for the directory app.

This module contains the Django app configuration for the directory app,
which provides the core resource management functionality.
"""

from django.apps import AppConfig


class DirectoryConfig(AppConfig):
    """
    Django app configuration for the directory app.

    This app provides comprehensive resource management for homeless services,
    including search, versioning, and workflow management.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "directory"
