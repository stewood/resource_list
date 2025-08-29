#!/usr/bin/env python3
"""
Fix Coverage Area Centers Script

This script calculates and sets center points for coverage areas that are missing them.
This will help fix the map display issue where maps default to San Francisco coordinates.
"""

import os
import sys
import django
from django.contrib.gis.geos import Point
from django.db import transaction

def fix_coverage_area_centers():
    """Calculate and set center points for coverage areas missing them."""
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    django.setup()
    
    from directory.models import CoverageArea
    
    print("🔧 Fixing Coverage Area Centers...")
    
    # Find coverage areas with geometry but no center
    coverage_areas_without_center = CoverageArea.objects.filter(
        geom__isnull=False,
        center__isnull=True
    )
    
    print(f"📊 Found {coverage_areas_without_center.count()} coverage areas without center points")
    
    if coverage_areas_without_center.count() == 0:
        print("✅ All coverage areas already have center points!")
        return True
    
    fixed_count = 0
    
    with transaction.atomic():
        for ca in coverage_areas_without_center:
            try:
                # Calculate center from geometry extent
                extent = ca.geom.extent
                center_lon = (extent[0] + extent[2]) / 2  # (min_lon + max_lon) / 2
                center_lat = (extent[1] + extent[3]) / 2  # (min_lat + max_lat) / 2
                
                # Create center point
                center_point = Point(center_lon, center_lat, srid=4326)
                
                # Update the coverage area
                ca.center = center_point
                ca.save(update_fields=['center'])
                
                fixed_count += 1
                
                if fixed_count % 100 == 0:
                    print(f"  ✅ Fixed {fixed_count} coverage areas...")
                    
            except Exception as e:
                print(f"❌ Error fixing center for {ca.name} (ID: {ca.id}): {e}")
                continue
    
    print(f"🎉 Successfully fixed center points for {fixed_count} coverage areas!")
    
    # Verify the fix
    remaining_without_center = CoverageArea.objects.filter(
        geom__isnull=False,
        center__isnull=True
    ).count()
    
    print(f"📊 Remaining coverage areas without center: {remaining_without_center}")
    
    return True

def test_specific_coverage_area():
    """Test the fix for a specific coverage area."""
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    django.setup()
    
    from directory.models import CoverageArea
    
    # Test with Whitley County (ID: 25478)
    ca = CoverageArea.objects.get(id=25478)
    print(f"Testing {ca.name} (ID: {ca.id}):")
    print(f"  Has geometry: {ca.geom is not None}")
    print(f"  Has center: {ca.center is not None}")
    
    if ca.geom and not ca.center:
        extent = ca.geom.extent
        center_lon = (extent[0] + extent[2]) / 2
        center_lat = (extent[1] + extent[3]) / 2
        print(f"  Calculated center: ({center_lat}, {center_lon})")
        print(f"  Extent: {extent}")
    elif ca.center:
        print(f"  Center coordinates: {ca.center.coords}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_specific_coverage_area()
    else:
        success = fix_coverage_area_centers()
        sys.exit(0 if success else 1)

