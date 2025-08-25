#!/usr/bin/env python3
"""
Simple Data Migration: SQLite → PostgreSQL

This script exports essential data from SQLite to JSON, then imports it to PostgreSQL.
Focuses only on resources and their metadata - no users, no audit logs.

Usage:
    python cloud/simple_data_migration.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_sqlite_data():
    """Export essential data from SQLite to JSON"""
    print("📤 Exporting data from SQLite...")
    
    # Set up Django for SQLite
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import Resource, TaxonomyCategory, ServiceType, CoverageArea
    
    # Create exports directory
    exports_dir = project_root / 'cloud' / 'exports'
    exports_dir.mkdir(exist_ok=True)
    
    # Export taxonomy categories
    categories = TaxonomyCategory.objects.all()
    category_data = []
    for cat in categories:
        category_data.append({
            'model': 'directory.taxonomycategory',
            'pk': cat.id,
            'fields': {
                'name': cat.name,
                'description': cat.description or '',
                'slug': cat.name.lower().replace(' ', '-').replace('&', 'and'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            }
        })
    
    with open(exports_dir / 'categories.json', 'w') as f:
        json.dump(category_data, f, indent=2)
    print(f"✅ Exported {len(category_data)} categories")
    
    # Export service types
    service_types = ServiceType.objects.all()
    service_type_data = []
    for st in service_types:
        service_type_data.append({
            'model': 'directory.servicetype',
            'pk': st.id,
            'fields': {
                'name': st.name,
                'description': st.description or '',
                'slug': st.name.lower().replace(' ', '-').replace('&', 'and'),
                'created_at': datetime.now().isoformat(),
            }
        })
    
    with open(exports_dir / 'service_types.json', 'w') as f:
        json.dump(service_type_data, f, indent=2)
    print(f"✅ Exported {len(service_type_data)} service types")
    
    # Export coverage areas (simplified)
    coverage_areas = CoverageArea.objects.all()
    coverage_data = []
    for ca in coverage_areas:
        coverage_data.append({
            'model': 'directory.coveragearea',
            'pk': ca.id,
            'fields': {
                'kind': 'county',
                'name': ca.name,
                'radius_m': None,
                'ext_ids': {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'created_by_id': 1,  # admin user
                'updated_by_id': 1,  # admin user
            }
        })
    
    with open(exports_dir / 'coverage_areas.json', 'w') as f:
        json.dump(coverage_data, f, indent=2)
    print(f"✅ Exported {len(coverage_data)} coverage areas")
    
    # Export resources (with admin user)
    resources = Resource.objects.all()
    resource_data = []
    for resource in resources:
        resource_data.append({
            'model': 'directory.resource',
            'pk': resource.id,
            'fields': {
                'name': resource.name,
                'category_id': resource.category.id,
                'description': resource.description or '',
                'phone': resource.phone or '',
                'email': resource.email or '',
                'website': resource.website or '',
                'address1': resource.address1 or '',
                'address2': resource.address2 or '',
                'city': resource.city or '',
                'state': resource.state or '',
                'county': resource.county or '',
                'postal_code': resource.postal_code or '',
                'status': resource.status,
                'source': resource.source or '',
                'notes': resource.notes or '',
                'hours_of_operation': resource.hours_of_operation or '',
                'is_emergency_service': resource.is_emergency_service,
                'is_24_hour_service': resource.is_24_hour_service,
                'eligibility_requirements': resource.eligibility_requirements or '',
                'populations_served': resource.populations_served or '',
                'insurance_accepted': resource.insurance_accepted or '',
                'cost_information': resource.cost_information or '',
                'languages_available': resource.languages_available or '',
                'capacity': resource.capacity or '',
                'verification_frequency_days': resource.verification_frequency_days or 180,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'created_by_id': 1,  # admin user
                'updated_by_id': 1,  # admin user
                'is_deleted': resource.is_deleted,
                'is_archived': resource.is_archived,
                'archive_reason': resource.archive_reason or '',
            }
        })
    
    with open(exports_dir / 'resources.json', 'w') as f:
        json.dump(resource_data, f, indent=2)
    print(f"✅ Exported {len(resource_data)} resources")
    
    # Export relationships
    relationships = []
    for resource in resources:
        for service_type in resource.service_types.all():
            relationships.append({
                'model': 'directory.resource_service_types',
                'fields': {
                    'resource_id': resource.id,
                    'servicetype_id': service_type.id,
                }
            })
    
    with open(exports_dir / 'relationships.json', 'w') as f:
        json.dump(relationships, f, indent=2)
    print(f"✅ Exported {len(relationships)} service type relationships")
    
    return exports_dir

def import_to_postgres(exports_dir):
    """Import data to PostgreSQL"""
    print("\n📥 Importing data to PostgreSQL...")
    
    # Set up Django for PostgreSQL
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    # Clear existing data using direct SQL
    print("🧹 Clearing existing data...")
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("DELETE FROM directory_resource_service_types")
    cursor.execute("DELETE FROM directory_resourcecoverage")
    cursor.execute("DELETE FROM directory_resource")
    cursor.execute("DELETE FROM directory_servicetype")
    cursor.execute("DELETE FROM directory_coveragearea")
    cursor.execute("DELETE FROM directory_taxonomycategory")
    print("✅ Cleared existing data")
    
    # Import in order
    files = ['categories.json', 'service_types.json', 'coverage_areas.json', 'resources.json']
    
    for filename in files:
        file_path = exports_dir / filename
        if file_path.exists():
            print(f"📂 Importing {filename}...")
            try:
                execute_from_command_line(['manage.py', 'loaddata', str(file_path), '--settings=resource_directory.development_settings'])
                print(f"✅ Imported {filename}")
            except Exception as e:
                print(f"⚠️  Error importing {filename}: {e}")
    
    # Verify data
    print("\n🔍 Verifying data...")
    total_resources = Resource.objects.count()
    published_resources = Resource.objects.filter(status='published').count()
    
    print(f"✅ Total resources: {total_resources}")
    print(f"✅ Published resources: {published_resources}")

def main():
    print("🚀 Simple SQLite to PostgreSQL Migration")
    print("========================================")
    
    # Export from SQLite
    exports_dir = export_sqlite_data()
    
    # Import to PostgreSQL
    import_to_postgres(exports_dir)
    
    print("\n🎉 Migration completed!")
    print("🌐 Check your data at: http://localhost:8000")

if __name__ == '__main__':
    main()
