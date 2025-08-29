#!/usr/bin/env python3
"""
Check Resource Coverage Areas

This script checks which coverage areas are linked to a specific resource.
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


def check_resource_coverage():
    """Check coverage areas for Bald Rock Fire Department."""
    print("🔍 Checking Bald Rock Fire Department coverage areas...")
    
    # Get the resource
    try:
        bald_rock = Resource.objects.get(id=193)
        print(f"✅ Found resource: {bald_rock.name} (ID: {bald_rock.id})")
    except Resource.DoesNotExist:
        print("❌ Resource not found")
        return
    
    # Get coverage areas
    coverage_areas = ResourceCoverage.objects.filter(resource=bald_rock)
    print(f"📊 Found {coverage_areas.count()} coverage areas:")
    
    for rc in coverage_areas:
        ca = rc.coverage_area
        print(f"  - {ca.name} (ID: {ca.id})")
        print(f"    Kind: {ca.kind}")
        print(f"    ext_ids: {ca.ext_ids}")
        print(f"    Has geometry: {ca.geom is not None}")
        if ca.geom:
            print(f"    Geometry type: {ca.geom.geom_type}")
        print()
    
    # Check if there are duplicate Laurel County records
    laurel_counties = CoverageArea.objects.filter(name='Laurel County', kind='COUNTY')
    print(f"🔍 Found {laurel_counties.count()} Laurel County records:")
    for ca in laurel_counties:
        print(f"  - ID: {ca.id}, ext_ids: {ca.ext_ids}, has_geom: {ca.geom is not None}")


if __name__ == "__main__":
    check_resource_coverage()
