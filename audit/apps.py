"""
Django app configuration for the audit app.

This module contains the Django app configuration for the audit app,
which provides audit logging and version control functionality.
"""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """
    Django app configuration for the audit app.
    
    This app provides comprehensive audit logging and version control
    for tracking all changes to resources in the system.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"

    def ready(self):
        """Import signals when the app is ready."""
        import audit.models  # noqa
