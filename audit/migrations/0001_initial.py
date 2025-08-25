# Generated manually for audit app initialization

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("directory", "0001_initial"),
    ]

    operations = [
        # This is an empty migration to initialize the audit app
        # The actual audit functionality is handled by signals in audit/models.py
    ]
