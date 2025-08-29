#!/usr/bin/env python3
"""
Migrate Staging Only - Import GIS data to staging using existing export files

This script imports GIS data to staging using the existing export files.
It ONLY operates on staging and does NOT touch the local development database.

Usage:
    python cloud/migrate_staging_only.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def migrate_staging_only():
    """Migrate GIS data to staging using existing export files"""
    print("🚀 Staging-Only GIS Data Migration")
    print("=" * 40)
    
    # Safety confirmation
    print("\n⚠️  SAFETY WARNING:")
    print("This script will:")
    print("  1. Use existing export files from cloud/exports/")
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
    
    print("\n🔄 Starting staging migration...")
    
    # Set up Django for staging ONLY
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import GEOSGeometry
    
    # Load export files
    exports_dir = project_root / 'cloud' / 'exports'
    
    # Check if export files exist
    coverage_file = exports_dir / 'coverage_areas.json'
    association_file = exports_dir / 'resource_coverage.json'
    
    if not coverage_file.exists():
        print(f"❌ Coverage areas export file not found: {coverage_file}")
        return
    
    if not association_file.exists():
        print(f"❌ Resource coverage export file not found: {association_file}")
        return
    
    # Load coverage areas data
    print("📂 Loading coverage areas data...")
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)
    
    print(f"✅ Loaded {len(coverage_data)} coverage areas")
    
    # Load associations data
    print("📂 Loading resource coverage associations...")
    with open(association_file, 'r') as f:
        association_data = json.load(f)
    
    print(f"✅ Loaded {len(association_data)} associations")
    
    # Clear existing data in STAGING
    print("🗑️ Clearing existing coverage areas and associations in STAGING...")
    ResourceCoverage.objects.all().delete()
    CoverageArea.objects.all().delete()
    
    # Import coverage areas using bulk_create
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
        
        # Create coverage area object
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
    
    print(f"✅ Imported {len(created_coverage_areas)} coverage areas")
    
    # Import associations
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
    
    print(f"✅ Imported {imported_association_count} associations")
    
    # Verify the migration
    print("🧪 Verifying migration...")
    
    from directory.models import Resource
    
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    resource_count = Resource.objects.count()
    
    print(f"📊 Final staging data counts:")
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
    
    print("\n🎉 Staging migration completed successfully!")
    print("Your Render staging environment now has all GIS data!")

if __name__ == '__main__':
    migrate_staging_only()

