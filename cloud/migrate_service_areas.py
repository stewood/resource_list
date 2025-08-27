#!/usr/bin/env python3
"""
Service Areas Migration: Add Missing Coverage Areas and Resource Associations

This script adds missing coverage areas and resource-coverage associations to staging
without touching existing users or resources.

Usage:
    python cloud/migrate_service_areas.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_service_areas_from_dev():
    """Export coverage areas and resource associations from local development"""
    print("📤 Exporting service areas from local development...")
    
    # Set up Django for local development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    
    # Create exports directory
    exports_dir = project_root / 'cloud' / 'exports'
    exports_dir.mkdir(exist_ok=True)
    
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
    
    with open(exports_dir / 'coverage_areas_only.json', 'w') as f:
        json.dump(coverage_data, f, indent=2)
    print(f"✅ Exported {len(coverage_data)} coverage areas with spatial data")
    
    # Export resource-coverage associations
    associations = ResourceCoverage.objects.all()
    association_data = []
    for assoc in associations:
        association_data.append({
            'model': 'directory.resourcecoverage',
            'pk': assoc.id,
            'fields': {
                'resource_id': assoc.resource.id,
                'coverage_area_id': assoc.coverage_area.id,
                'created_at': assoc.created_at.isoformat(),
                'created_by_id': assoc.created_by.id,
                'notes': assoc.notes,
            }
        })
    
    with open(exports_dir / 'resource_coverage_only.json', 'w') as f:
        json.dump(association_data, f, indent=2)
    print(f"✅ Exported {len(association_data)} resource-coverage associations")
    
    print("🎉 Service areas export completed successfully!")

def import_service_areas_to_staging():
    """Import coverage areas and associations to staging (preserve existing data)"""
    print("📥 Importing service areas to staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import GEOSGeometry
    
    exports_dir = project_root / 'cloud' / 'exports'
    
    # Import coverage areas (skip if already exists)
    with open(exports_dir / 'coverage_areas_only.json', 'r') as f:
        coverage_data = json.load(f)
    
    existing_coverage_ids = set(CoverageArea.objects.values_list('id', flat=True))
    imported_coverage_count = 0
    
    for ca_item in coverage_data:
        if ca_item['pk'] not in existing_coverage_ids:
            fields = ca_item['fields']
            
            # Handle spatial fields
            geom = None
            center = None
            
            if fields['geom']:
                geom = GEOSGeometry(fields['geom'])
            
            if fields['center']:
                center = GEOSGeometry(fields['center'])
            
            CoverageArea.objects.create(
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
            imported_coverage_count += 1
    
    print(f"✅ Imported {imported_coverage_count} new coverage areas")
    
    # Import resource-coverage associations (clear existing first)
    print("🗑️ Clearing existing resource-coverage associations...")
    ResourceCoverage.objects.all().delete()
    
    with open(exports_dir / 'resource_coverage_only.json', 'r') as f:
        association_data = json.load(f)
    
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
    
    print(f"✅ Imported {len(association_data)} resource-coverage associations")
    
    print("🎉 Service areas import completed successfully!")

def test_service_areas():
    """Test service areas functionality on staging"""
    print("🧪 Testing service areas functionality...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    
    # Test basic counts
    resource_count = Resource.objects.count()
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    
    print(f"📊 Service areas data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
    # Test resource coverage
    if association_count > 0:
        print(f"\n📍 Sample resource service areas:")
        sample_associations = ResourceCoverage.objects.select_related('resource', 'coverage_area')[:5]
        for assoc in sample_associations:
            print(f"  - {assoc.resource.name} serves {assoc.coverage_area.name}")
    
    # Test spatial query
    if coverage_count > 0:
        areas_with_center = CoverageArea.objects.filter(center__isnull=False)
        if areas_with_center.exists():
            test_point = Point(-84.0849, 37.1289, srid=4326)  # London, KY
            nearby_areas = areas_with_center.filter(
                center__distance_lte=(test_point, 10000)
            ).annotate(
                distance=Distance('center', test_point)
            ).order_by('distance')[:3]
            
            print(f"\n📍 Spatial query test:")
            for area in nearby_areas:
                print(f"  - {area.name}: {area.distance.m:.0f}m away")
    
    print("✅ Service areas test completed!")

def main():
    """Main migration function"""
    print("🚀 Starting Service Areas Migration: Local Dev → Render Staging")
    print("=" * 60)
    
    # Step 1: Export from development
    export_service_areas_from_dev()
    print()
    
    # Step 2: Import to staging
    import_service_areas_to_staging()
    print()
    
    # Step 3: Test functionality
    test_service_areas()
    print()
    
    print("🎉 Service Areas Migration completed successfully!")
    print("Your Render staging environment now has complete service area functionality!")

if __name__ == '__main__':
    main()
