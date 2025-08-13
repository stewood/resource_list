# Generated manually for MVP requirements

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
        ("directory", "0003_fix_fts5_search"),
    ]

    operations = [
        migrations.RunSQL(
            # Prevent UPDATE on audit_log table
            sql="""
            CREATE TRIGGER audit_no_update BEFORE UPDATE ON directory_auditlog
            BEGIN 
                SELECT RAISE(ABORT,'audit_log is append-only'); 
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS audit_no_update;",
        ),
        migrations.RunSQL(
            # Prevent DELETE on audit_log table
            sql="""
            CREATE TRIGGER audit_no_delete BEFORE DELETE ON directory_auditlog
            BEGIN 
                SELECT RAISE(ABORT,'audit_log cannot be deleted'); 
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS audit_no_delete;",
        ),
        migrations.RunSQL(
            # Prevent UPDATE on resource_version table
            sql="""
            CREATE TRIGGER version_no_update BEFORE UPDATE ON directory_resourceversion
            BEGIN 
                SELECT RAISE(ABORT,'resource_version is append-only'); 
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS version_no_update;",
        ),
        migrations.RunSQL(
            # Prevent DELETE on resource_version table
            sql="""
            CREATE TRIGGER version_no_delete BEFORE DELETE ON directory_resourceversion
            BEGIN 
                SELECT RAISE(ABORT,'resource_version cannot be deleted'); 
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS version_no_delete;",
        ),
    ]
