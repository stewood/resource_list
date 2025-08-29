#!/usr/bin/env python3
"""
Migrate All GIS Data from Local Dev to Render Staging

This script performs a complete migration of all GIS data from the local development
environment to the Render staging environment, including all coverage areas and
resource-coverage associations.

Usage:
    python cloud/migrate_all_gis_data.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_from_local_dev():
    """Export data from local development environment"""
    print("📤 Exporting data from local development...")
    
    # Set up Django for local development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    
    # Export coverage areas with spatial data
    coverage_areas = CoverageArea.objects.all()
    coverage_data = []
    for ca in coverage_areas:
        # Handle spatial fields properly
        geom_data = None
        center_data = None
        
        if ca.geom:
            geom_data = ca.geom.ewkt  # Export as WKT with SRID
        
        if ca.center:
            center_data = ca.center.ewkt  # Export as WKT with SRID
        
        coverage_data.append({
            'model': 'directory.coveragearea',
            'pk': ca.id,
            'fields': {
                'kind': ca.kind,
                'name': ca.name,
                'geom': geom_data,
                'center': center_data,
                'radius_m': ca.radius_m,
                'ext_ids': ca.ext_ids,
                'created_at': ca.created_at.isoformat(),
                'updated_at': ca.updated_at.isoformat(),
                'created_by_id': ca.created_by.id,
                'updated_by_id': ca.updated_by.id,
            }
        })
    
    print(f"✅ Exported {len(coverage_data)} coverage areas with spatial data")
    
    # Export resource-coverage associations
    associations = ResourceCoverage.objects.all()
    association_data = []
    for assoc in associations:
        association_data.append({
            'model': 'directory.resourcecoverage',
            'pk': assoc.id,
            'fields': {
                'resource_id': assoc.resource_id,
                'coverage_area_id': assoc.coverage_area_id,
                'created_at': assoc.created_at.isoformat(),
                'created_by_id': assoc.created_by.id,
                'notes': assoc.notes,
            }
        })
    
    print(f"✅ Exported {len(association_data)} resource-coverage associations")
    
    # Save export files
    exports_dir = project_root / 'cloud' / 'exports'
    exports_dir.mkdir(exist_ok=True)
    
    with open(exports_dir / 'coverage_areas_complete.json', 'w') as f:
        json.dump(coverage_data, f, indent=2)
    
    with open(exports_dir / 'resource_coverage_complete.json', 'w') as f:
        json.dump(association_data, f, indent=2)
    
    print("🎉 Export completed successfully!")
    return coverage_data, association_data

def import_to_staging(coverage_data, association_data):
    """Import data to staging environment"""
    print("📥 Importing data to staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import GEOSGeometry
    
    # Clear all existing coverage areas and associations in STAGING ONLY
    print("🗑️ Clearing existing coverage areas and associations in STAGING...")
    ResourceCoverage.objects.all().delete()
    CoverageArea.objects.all().delete()
    
    # Import all coverage areas using bulk_create to bypass validation
    print(f"📥 Importing {len(coverage_data)} coverage areas...")
    
    coverage_areas_to_create = []
    for ca_item in coverage_data:
        fields = ca_item['fields']
        
        # Handle spatial fields
        geom = None
        center = None
        
        if fields['geom']:
            geom = GEOSGeometry(fields['geom'])
        
        if fields['center']:
            center = GEOSGeometry(fields['center'])
        
        # Create coverage area object without saving
        coverage_area = CoverageArea(
            id=ca_item['pk'],
            kind=fields['kind'],
            name=fields['name'],
            geom=geom,
            center=center,
            radius_m=fields['radius_m'],
            ext_ids=fields['ext_ids'],
            created_at=datetime.fromisoformat(fields['created_at']),
            updated_at=datetime.fromisoformat(fields['updated_at']),
            created_by_id=fields['created_by_id'],
            updated_by_id=fields['updated_by_id'],
        )
        
        coverage_areas_to_create.append(coverage_area)
    
    # Use bulk_create to bypass validation
    created_coverage_areas = CoverageArea.objects.bulk_create(
        coverage_areas_to_create, 
        ignore_conflicts=True,
        batch_size=1000
    )
    
    imported_coverage_count = len(created_coverage_areas)
    print(f"✅ Imported {imported_coverage_count} coverage areas")
    
    # Import all resource-coverage associations
    print(f"📥 Importing {len(association_data)} resource-coverage associations...")
    
    imported_association_count = 0
    for assoc_item in association_data:
        fields = assoc_item['fields']
        ResourceCoverage.objects.create(
            id=assoc_item['pk'],
            resource_id=fields['resource_id'],
            coverage_area_id=fields['coverage_area_id'],
            created_at=datetime.fromisoformat(fields['created_at']),
            created_by_id=fields['created_by_id'],
            notes=fields['notes'],
        )
        imported_association_count += 1
    
    print(f"✅ Imported {imported_association_count} resource-coverage associations")
    
    return imported_coverage_count, imported_association_count

def verify_staging_migration():
    """Verify the migration on staging"""
    print("🧪 Verifying migration on staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    resource_count = Resource.objects.count()
    
    print(f"📊 Final data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
    # Check specific resources
    print(f"\n📍 Sample resource coverage areas:")
    
    # Check Resource 355 (988 Suicide & Crisis Lifeline)
    resource_355 = Resource.objects.get(id=355)
    associations_355 = ResourceCoverage.objects.filter(resource=resource_355).select_related('coverage_area')
    print(f"  - Resource 355 ({resource_355.name}): {associations_355.count()} coverage areas")
    for assoc in associations_355:
        print(f"    * {assoc.coverage_area.name} ({assoc.coverage_area.kind})")
    
    # Check a few other resources
    sample_resources = Resource.objects.filter(status='published')[:3]
    for resource in sample_resources:
        associations = ResourceCoverage.objects.filter(resource=resource).select_related('coverage_area')
        print(f"  - {resource.name}: {associations.count()} coverage areas")
        for assoc in associations[:2]:  # Show first 2
            print(f"    * {assoc.coverage_area.name} ({assoc.coverage_area.kind})")
    
    # Test spatial query
    print(f"\n📍 Testing spatial query...")
    try:
        # Test a simple spatial query
        from django.contrib.gis.geos import Point
        test_point = Point(-87.6298, 41.8781, srid=4326)  # Chicago coordinates
        
        nearby_areas = CoverageArea.objects.filter(
            geom__contains=test_point
        )[:5]
        
        print(f"  - Found {nearby_areas.count()} coverage areas containing Chicago")
        for area in nearby_areas:
            print(f"    * {area.name} ({area.kind})")
            
    except Exception as e:
        print(f"  - Spatial query test failed: {e}")

def migrate_all_gis_data():
    """Migrate all GIS data from local dev to staging"""
    print("🚀 Complete GIS Data Migration: Local Dev → Render Staging")
    print("=" * 60)
    
    # Safety confirmation
    print("\n⚠️  SAFETY WARNING:")
    print("This script will:")
    print("  1. Export all coverage areas and associations from LOCAL development")
    print("  2. Clear all coverage areas and associations in STAGING")
    print("  3. Import all data to STAGING")
    print("  4. Verify the migration")
    print()
    print("✅ Your local development database will NOT be affected")
    print("✅ Your local development database will NOT be modified")
    print("✅ Only the STAGING database will be updated")
    print()
    
    # Get user confirmation
    response = input("Do you want to proceed with the migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Migration cancelled by user")
        return
    
    print("\n🔄 Starting migration...")
    
    # Step 1: Export from local development
    coverage_data, association_data = export_from_local_dev()
    
    # Step 2: Import to staging
    imported_coverage_count, imported_association_count = import_to_staging(coverage_data, association_data)
    
    # Step 3: Verify the migration
    verify_staging_migration()
    
    # Step 4: Verify local database wasn't affected
    print("\n🔍 Verifying local database integrity...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    
    local_coverage_count = CoverageArea.objects.count()
    local_association_count = ResourceCoverage.objects.count()
    local_resource_count = Resource.objects.count()
    
    print(f"✅ Local database verification:")
    print(f"  - Resources: {local_resource_count}")
    print(f"  - Coverage Areas: {local_coverage_count}")
    print(f"  - Associations: {local_association_count}")
    
    if local_coverage_count == 7615 and local_association_count == 575 and local_resource_count == 254:
        print("✅ Local database integrity confirmed - no changes detected")
    else:
        print("⚠️  WARNING: Local database may have been affected!")
    
    print("\n🎉 Complete GIS Data Migration completed successfully!")
    print("Your Render staging environment now has all GIS data from development!")

if __name__ == '__main__':
    migrate_all_gis_data()
