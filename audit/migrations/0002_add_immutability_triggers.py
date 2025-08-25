# Generated manually for MVP requirements

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
        ("directory", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            # Prevent UPDATE on audit_log table
            sql="""
            CREATE OR REPLACE FUNCTION audit_no_update()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_log is append-only';
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER audit_no_update BEFORE UPDATE ON directory_auditlog
            FOR EACH ROW EXECUTE FUNCTION audit_no_update();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS audit_no_update; DROP FUNCTION IF EXISTS audit_no_update();",
        ),
        migrations.RunSQL(
            # Prevent DELETE on audit_log table
            sql="""
            CREATE OR REPLACE FUNCTION audit_no_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_log cannot be deleted';
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER audit_no_delete BEFORE DELETE ON directory_auditlog
            FOR EACH ROW EXECUTE FUNCTION audit_no_delete();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS audit_no_delete; DROP FUNCTION IF EXISTS audit_no_delete();",
        ),
        migrations.RunSQL(
            # Prevent UPDATE on resource_version table
            sql="""
            CREATE OR REPLACE FUNCTION version_no_update()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'resource_version is append-only';
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER version_no_update BEFORE UPDATE ON directory_resourceversion
            FOR EACH ROW EXECUTE FUNCTION version_no_update();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS version_no_update; DROP FUNCTION IF EXISTS version_no_update();",
        ),
        migrations.RunSQL(
            # Prevent DELETE on resource_version table
            sql="""
            CREATE OR REPLACE FUNCTION version_no_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'resource_version cannot be deleted';
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER version_no_delete BEFORE DELETE ON directory_resourceversion
            FOR EACH ROW EXECUTE FUNCTION version_no_delete();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS version_no_delete; DROP FUNCTION IF EXISTS version_no_delete();",
        ),
    ]
