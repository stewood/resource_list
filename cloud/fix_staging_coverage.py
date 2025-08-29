#!/usr/bin/env python3
"""
Fix Staging Coverage Areas - Import All Missing Coverage Areas

This script fixes the staging environment by importing all missing coverage areas
and ensuring all resource-coverage associations are properly set up.

Usage:
    python cloud/fix_staging_coverage.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def fix_staging_coverage():
    """Fix staging coverage areas by importing all missing data"""
    print("🔧 Fixing staging coverage areas...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import GEOSGeometry
    
    # First, let's clear all existing coverage areas and associations
    print("🗑️ Clearing existing coverage areas and associations...")
    ResourceCoverage.objects.all().delete()
    CoverageArea.objects.all().delete()
    
    # Import all coverage areas from the export file
    exports_dir = project_root / 'cloud' / 'exports'
    with open(exports_dir / 'coverage_areas.json', 'r') as f:
        coverage_data = json.load(f)
    
    print(f"📥 Importing {len(coverage_data)} coverage areas...")
    
    for ca_item in coverage_data:
        fields = ca_item['fields']
        
        # Handle spatial fields
        geom = None
        center = None
        
        if fields['geom']:
            geom = GEOSGeometry(fields['geom'])
        
        if fields['center']:
            center = GEOSGeometry(fields['center'])
        
        # Create coverage area without validation to handle missing FIPS codes
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
        
        # Save without validation to bypass FIPS code requirements
        coverage_area.save(force_insert=True)
    
    print(f"✅ Imported {len(coverage_data)} coverage areas")
    
    # Import all resource-coverage associations
    with open(exports_dir / 'resource_coverage.json', 'r') as f:
        association_data = json.load(f)
    
    print(f"📥 Importing {len(association_data)} resource-coverage associations...")
    
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
    
    # Verify the fix
    print("🧪 Verifying fix...")
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    
    print(f"📊 Final counts:")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
    # Check specific resource
    from directory.models import Resource
    resource_355 = Resource.objects.get(id=355)
    associations_355 = ResourceCoverage.objects.filter(resource=resource_355).select_related('coverage_area')
    
    print(f"📍 Resource 355 ({resource_355.name}) coverage areas:")
    for assoc in associations_355:
        print(f"  - {assoc.coverage_area.name} ({assoc.coverage_area.kind})")
    
    print("🎉 Staging coverage areas fixed successfully!")

if __name__ == '__main__':
    fix_staging_coverage()
