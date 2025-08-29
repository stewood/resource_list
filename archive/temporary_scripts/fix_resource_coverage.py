#!/usr/bin/env python3
"""
Fix Resource Coverage Areas

This script fixes resource-coverage relationships by linking resources to the correct
coverage areas that have geometry data.
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, ResourceCoverage, CoverageArea
from django.contrib.auth.models import User


def fix_resource_coverage():
    """Fix resource-coverage relationships to use coverage areas with geometry."""
    print("🔧 Fixing resource-coverage relationships...")
    
    # Get a user for audit trail
    user = User.objects.first()
    if not user:
        print("❌ No user found for audit trail")
        return
    
    # Get all Kentucky counties with geometry (new ones)
    ky_counties_with_geom = CoverageArea.objects.filter(
        kind='COUNTY',
        ext_ids__state_fips='21'
    ).exclude(geom__isnull=True)
    
    print(f"✅ Found {ky_counties_with_geom.count()} Kentucky counties with geometry")
    
    # Create a mapping of county names to the correct coverage area IDs
    county_mapping = {}
    for county in ky_counties_with_geom:
        county_mapping[county.name] = county.id
        print(f"  - {county.name}: ID {county.id}")
    
    # Find all resource-coverage relationships that need fixing
    fixed_count = 0
    skipped_count = 0
    
    for rc in ResourceCoverage.objects.all():
        ca = rc.coverage_area
        
        # Only fix Kentucky counties without geometry
        if (ca.kind == 'COUNTY' and 
            ca.ext_ids == {} and  # Old records have empty ext_ids
            ca.geom is None and   # Old records have no geometry
            ca.name in county_mapping):  # We have a new record for this county
            
            old_id = ca.id
            new_id = county_mapping[ca.name]
            
            print(f"🔄 Fixing: {ca.name}")
            print(f"  Old coverage area ID: {old_id} (no geometry)")
            print(f"  New coverage area ID: {new_id} (with geometry)")
            
            # Get the new coverage area
            new_coverage_area = CoverageArea.objects.get(id=new_id)
            
            # Update the resource-coverage relationship
            rc.coverage_area = new_coverage_area
            rc.updated_by = user
            rc.save()
            
            print(f"  ✅ Updated resource {rc.resource.name} to use new coverage area")
            fixed_count += 1
        else:
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  Fixed relationships: {fixed_count}")
    print(f"  Skipped relationships: {skipped_count}")
    
    # Verify the fix for Bald Rock Fire Department
    print(f"\n🔍 Verifying Bald Rock Fire Department fix...")
    try:
        bald_rock = Resource.objects.get(id=193)
        coverage_areas = ResourceCoverage.objects.filter(resource=bald_rock)
        for rc in coverage_areas:
            ca = rc.coverage_area
            print(f"  - {ca.name} (ID: {ca.id})")
            print(f"    Has geometry: {ca.geom is not None}")
            print(f"    ext_ids: {ca.ext_ids}")
    except Resource.DoesNotExist:
        print("  ❌ Bald Rock Fire Department not found")


if __name__ == "__main__":
    fix_resource_coverage()
