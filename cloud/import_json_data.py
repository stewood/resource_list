#!/usr/bin/env python3
"""
Import JSON Data to PostgreSQL

This script imports the JSON files that were exported from SQLite into PostgreSQL.
Run this after the export is complete.

Usage:
    python cloud/import_json_data.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("📥 Importing JSON Data to PostgreSQL")
    print("====================================")
    
    # Set up Django for PostgreSQL only
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    from django.db import connection
    
    # Clear existing data using direct SQL
    print("🧹 Clearing existing data...")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM directory_resource_service_types")
    cursor.execute("DELETE FROM directory_resourcecoverage")
    cursor.execute("DELETE FROM directory_resource")
    cursor.execute("DELETE FROM directory_servicetype")
    cursor.execute("DELETE FROM directory_coveragearea")
    cursor.execute("DELETE FROM directory_taxonomycategory")
    print("✅ Cleared existing data")
    
    # Import JSON files
    exports_dir = project_root / 'cloud' / 'exports'
    files = ['categories.json', 'service_types.json', 'coverage_areas.json', 'resources.json']
    
    for filename in files:
        file_path = exports_dir / filename
        if file_path.exists():
            print(f"📂 Importing {filename}...")
            try:
                execute_from_command_line(['manage.py', 'loaddata', str(file_path)])
                print(f"✅ Imported {filename}")
            except Exception as e:
                print(f"⚠️  Error importing {filename}: {e}")
        else:
            print(f"⚠️  File not found: {filename}")
    
    # Verify data
    print("\n🔍 Verifying data...")
    from directory.models import Resource
    total_resources = Resource.objects.count()
    published_resources = Resource.objects.filter(status='published').count()
    
    print(f"✅ Total resources: {total_resources}")
    print(f"✅ Published resources: {published_resources}")
    
    print("\n🎉 Import completed!")
    print("🌐 Check your data at: http://localhost:8000")

if __name__ == '__main__':
    main()
