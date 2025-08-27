#!/usr/bin/env python3
"""
Test GIS Migration Script

This script tests the GIS migration functionality without actually running the full migration.
Useful for testing connectivity and basic functionality.

Usage:
    python cloud/test_gis_migration.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_local_gis():
    """Test GIS functionality in local development"""
    print("🧪 Testing local GIS functionality...")
    
    # Set up Django for local development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    
    # Test basic counts
    resource_count = Resource.objects.count()
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    
    print(f"📊 Local data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
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
            
            print(f"📍 Local spatial query test:")
            for area in nearby_areas:
                print(f"  - {area.name}: {area.distance.m:.0f}m away")
    
    print("✅ Local GIS test completed!")

def test_staging_gis():
    """Test GIS functionality on staging"""
    print("🧪 Testing staging GIS functionality...")
    
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
    
    print(f"📊 Staging data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
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
            
            print(f"📍 Staging spatial query test:")
            for area in nearby_areas:
                print(f"  - {area.name}: {area.distance.m:.0f}m away")
    
    print("✅ Staging GIS test completed!")

def main():
    """Main test function"""
    print("🚀 Testing GIS Migration Setup")
    print("=" * 40)
    
    # Test local environment
    test_local_gis()
    print()
    
    # Test staging environment
    test_staging_gis()
    print()
    
    print("🎉 GIS migration test completed!")
    print("If both tests pass, you're ready to run the full migration.")

if __name__ == '__main__':
    main()
