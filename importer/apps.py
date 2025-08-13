"""
Django app configuration for the importer app.

This module contains the Django app configuration for the importer app,
which provides CSV import and export functionality.
"""

from django.apps import AppConfig


class ImporterConfig(AppConfig):
    """
    Django app configuration for the importer app.
    
    This app provides CSV import and export functionality for bulk
    resource management and data migration.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "importer"
