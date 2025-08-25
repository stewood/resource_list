#!/usr/bin/env python3
"""
Export SQLite data to JSON format for migration to PostgreSQL.
This script exports all data from the current SQLite database.
"""

import os
import sys
import json
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from django.core.management import call_command
from django.core.serializers import serialize
from directory.models import Resource, CoverageArea, TaxonomyCategory
from audit.models import AuditLog
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


def export_data():
    """Export all data from SQLite to JSON files."""
    
    # Create exports directory
    exports_dir = project_root / 'cloud' / 'exports'
    exports_dir.mkdir(exist_ok=True)
    
    print("🔄 Starting data export from SQLite...")
    
    # List of models to export (in dependency order)
    models_to_export = [
        # Django built-in models
        (User, 'users.json'),
        (Group, 'groups.json'),
        (Permission, 'permissions.json'),
        (ContentType, 'content_types.json'),
        
        # Your app models
        (TaxonomyCategory, 'taxonomy.json'),
        (CoverageArea, 'coverage_areas.json'),
        (Resource, 'resources.json'),
        (AuditLog, 'audit_logs.json'),
    ]
    
    exported_files = []
    
    for model, filename in models_to_export:
        try:
            # Get all objects from the model
            objects = model.objects.all()
            count = objects.count()
            
            if count == 0:
                print(f"⚠️  No data found for {model.__name__}")
                continue
            
            # Serialize to JSON
            serialized_data = serialize('json', objects, indent=2)
            
            # Save to file
            filepath = exports_dir / filename
            with open(filepath, 'w') as f:
                f.write(serialized_data)
            
            exported_files.append((filename, count))
            print(f"✅ Exported {count} {model.__name__} records to {filename}")
            
        except Exception as e:
            print(f"❌ Error exporting {model.__name__}: {e}")
    
    # Create a summary file
    summary = {
        'export_date': django.utils.timezone.now().isoformat(),
        'source_database': 'SQLite',
        'exported_files': exported_files,
        'total_records': sum(count for _, count in exported_files)
    }
    
    summary_file = exports_dir / 'export_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 Export completed!")
    print(f"📁 Files saved to: {exports_dir}")
    print(f"📊 Total records exported: {summary['total_records']}")
    print(f"📋 Summary saved to: {summary_file}")
    
    return exports_dir


if __name__ == '__main__':
    export_data()
