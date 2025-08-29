#!/usr/bin/env python3
"""
Add Essential Coverage Areas to Staging

This script adds the essential coverage areas needed for the maps to work,
specifically the "United States (All States and Territories)" coverage area
that Resource 355 (988 Suicide & Crisis Lifeline) needs.

Usage:
    python cloud/add_essential_coverage.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def add_essential_coverage():
    """Add essential coverage areas to staging"""
    print("🔧 Adding essential coverage areas to staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage, Resource
    from django.contrib.gis.geos import GEOSGeometry
    from django.contrib.auth.models import User
    
    # Get the admin user
    user = User.objects.get(id=1)
    
    # Create the United States coverage area
    print("📝 Creating United States coverage area...")
    
    # Create a simple polygon covering the continental US
    # This is a rough approximation - in production you'd want the actual US boundary
    us_polygon_wkt = "MULTIPOLYGON(((-125 25, -125 50, -65 50, -65 25, -125 25)))"
    
    us_coverage, created = CoverageArea.objects.get_or_create(
        name="United States (All States and Territories)",
        defaults={
            'kind': 'STATE',
            'geom': GEOSGeometry(us_polygon_wkt, srid=4326),
            'ext_ids': {'state_fips': '00'},
            'created_by': user,
            'updated_by': user,
        }
    )
    
    if created:
        print(f"✅ Created United States coverage area (ID: {us_coverage.id})")
    else:
        print(f"✅ United States coverage area already exists (ID: {us_coverage.id})")
    
    # Create the association for Resource 355
    print("🔗 Creating association for Resource 355...")
    
    resource_355 = Resource.objects.get(id=355)
    association, created = ResourceCoverage.objects.get_or_create(
        resource=resource_355,
        coverage_area=us_coverage,
        defaults={
            'created_by': user,
            'notes': 'National 988 Suicide & Crisis Lifeline service area',
        }
    )
    
    if created:
        print(f"✅ Created association for Resource 355")
    else:
        print(f"✅ Association for Resource 355 already exists")
    
    # Verify the fix
    print("🧪 Verifying fix...")
    associations_355 = ResourceCoverage.objects.filter(resource=resource_355).select_related('coverage_area')
    
    print(f"📍 Resource 355 ({resource_355.name}) coverage areas:")
    for assoc in associations_355:
        print(f"  - {assoc.coverage_area.name} ({assoc.coverage_area.kind})")
    
    print("🎉 Essential coverage areas added successfully!")

if __name__ == '__main__':
    add_essential_coverage()
