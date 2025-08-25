#!/usr/bin/env python3
"""
Quick SQLite to PostgreSQL Migration Script

This script uses Django's ORM to copy data from SQLite to PostgreSQL,
handling schema differences automatically.

Usage:
    python cloud/quick_migration.py
"""

import os
import sys
import django
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_sqlite_data():
    """Get data from SQLite database"""
    # Set up Django for SQLite
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    django.setup()
    
    # Import models
    from directory.models import Resource, TaxonomyCategory, ServiceType, CoverageArea
    
    print("📋 Reading data from SQLite...")
    
    # Get taxonomy categories
    categories = list(TaxonomyCategory.objects.all())
    print(f"✅ Found {len(categories)} taxonomy categories")
    
    # Get service types
    service_types = list(ServiceType.objects.all())
    print(f"✅ Found {len(service_types)} service types")
    
    # Get coverage areas
    coverage_areas = list(CoverageArea.objects.all())
    print(f"✅ Found {len(coverage_areas)} coverage areas")
    
    # Get resources
    resources = list(Resource.objects.all())
    print(f"✅ Found {len(resources)} resources")
    
    return categories, service_types, coverage_areas, resources

def import_to_postgres(categories, service_types, coverage_areas, resources):
    """Import data to PostgreSQL database"""
    # Set up Django for PostgreSQL
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
    django.setup()
    
    # Import models
    from directory.models import Resource, TaxonomyCategory, ServiceType, CoverageArea
    from django.contrib.auth.models import User
    
    print("\n🔄 Switching to PostgreSQL...")
    
    # Clear existing data
    print("\n🧹 Clearing existing data...")
    Resource.objects.all().delete()
    ServiceType.objects.all().delete()
    CoverageArea.objects.all().delete()
    TaxonomyCategory.objects.all().delete()
    print("✅ Cleared existing data")
    
    # Get admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Found admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ No admin user found")
        return
    
    # Import taxonomy categories
    print("\n📂 Importing taxonomy categories...")
    for cat in categories:
        new_cat = TaxonomyCategory(
            name=cat.name,
            description=cat.description or '',
            slug=cat.name.lower().replace(' ', '-').replace('&', 'and'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        new_cat.save()
    print(f"✅ Imported {len(categories)} taxonomy categories")
    
    # Import service types
    print("📂 Importing service types...")
    for st in service_types:
        new_st = ServiceType(
            name=st.name,
            description=st.description or '',
            slug=st.name.lower().replace(' ', '-').replace('&', 'and'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        new_st.save()
    print(f"✅ Imported {len(service_types)} service types")
    
    # Import coverage areas
    print("📂 Importing coverage areas...")
    for ca in coverage_areas:
        new_ca = CoverageArea(
            name=ca.name,
            description=ca.description or '',
            slug=ca.name.lower().replace(' ', '-').replace('&', 'and'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        new_ca.save()
    print(f"✅ Imported {len(coverage_areas)} coverage areas")
    
    # Import resources
    print("📂 Importing resources...")
    imported_count = 0
    for resource in resources:
        try:
            # Get the category
            try:
                category = TaxonomyCategory.objects.get(name=resource.category.name)
            except TaxonomyCategory.DoesNotExist:
                print(f"⚠️  Category '{resource.category.name}' not found, skipping resource '{resource.name}'")
                continue
            
            # Create new resource
            new_resource = Resource(
                name=resource.name,
                category=category,
                description=resource.description or '',
                phone=resource.phone or '',
                email=resource.email or '',
                website=resource.website or '',
                address1=resource.address1 or '',
                address2=resource.address2 or '',
                city=resource.city or '',
                state=resource.state or '',
                county=resource.county or '',
                postal_code=resource.postal_code or '',
                status=resource.status,
                source=resource.source or '',
                notes=resource.notes or '',
                hours_of_operation=resource.hours_of_operation or '',
                is_emergency_service=resource.is_emergency_service,
                is_24_hour_service=resource.is_24_hour_service,
                eligibility_requirements=resource.eligibility_requirements or '',
                populations_served=resource.populations_served or '',
                insurance_accepted=resource.insurance_accepted or '',
                cost_information=resource.cost_information or '',
                languages_available=resource.languages_available or '',
                capacity=resource.capacity or '',
                verification_frequency_days=resource.verification_frequency_days or 180,
                created_by=admin_user,
                updated_by=admin_user,
                is_deleted=resource.is_deleted,
                is_archived=resource.is_archived,
                archive_reason=resource.archive_reason or ''
            )
            new_resource.save()
            
            # Add service types
            for service_type in resource.service_types.all():
                try:
                    new_service_type = ServiceType.objects.get(name=service_type.name)
                    new_resource.service_types.add(new_service_type)
                except ServiceType.DoesNotExist:
                    print(f"⚠️  Service type '{service_type.name}' not found for resource '{resource.name}'")
            
            # Add coverage areas
            for coverage_area in resource.coverage_areas.all():
                try:
                    new_coverage_area = CoverageArea.objects.get(name=coverage_area.name)
                    new_resource.coverage_areas.add(new_coverage_area)
                except CoverageArea.DoesNotExist:
                    print(f"⚠️  Coverage area '{coverage_area.name}' not found for resource '{resource.name}'")
            
            imported_count += 1
            
        except Exception as e:
            print(f"❌ Error importing resource '{resource.name}': {e}")
            continue
    
    print(f"✅ Imported {imported_count} resources")
    
    # Verify the data
    print("\n🔍 Verifying data...")
    total_resources = Resource.objects.count()
    published_resources = Resource.objects.filter(status='published').count()
    
    print(f"✅ Total resources in database: {total_resources}")
    print(f"✅ Published resources: {published_resources}")
    
    return total_resources, published_resources

def main():
    print("🚀 Quick SQLite to PostgreSQL Migration")
    print("=======================================")
    
    # Get data from SQLite
    categories, service_types, coverage_areas, resources = get_sqlite_data()
    
    # Import to PostgreSQL
    total_resources, published_resources = import_to_postgres(categories, service_types, coverage_areas, resources)
    
    print("\n🎉 Migration completed successfully!")
    print("🌐 You can now access your data at: http://localhost:8000")

if __name__ == '__main__':
    main()
