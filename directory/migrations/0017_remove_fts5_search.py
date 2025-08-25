# Generated manually to remove FTS5 search components

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("directory", "0016_merge_20250825_0107"),
    ]

    operations = [
        # No operations needed - FTS5 components don't exist in PostgreSQL
        # This migration is a no-op to clean up the migration history
    ]
