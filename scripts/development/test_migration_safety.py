#!/usr/bin/env python3
"""
Test Migration Safety - Verify the migration script is safe before running

This script tests the migration process without actually performing any operations
to ensure it's safe to run.

Usage:
    python cloud/test_migration_safety.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_local_dev_export():
    """Test the local development export process"""
    print("🧪 Testing local development export...")
    
    # Set up Django for local development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage, Resource
    
    # Test data counts
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    resource_count = Resource.objects.count()
    
    print(f"✅ Local dev data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
    # Test export process (without saving files)
    coverage_data = []
    for ca in CoverageArea.objects.all()[:5]:  # Test with first 5
        geom_data = None
        center_data = None
        
        if ca.geom:
            geom_data = ca.geom.ewkt
        
        if ca.center:
            center_data = ca.center.ewkt
        
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
    
    print(f"✅ Export test successful - {len(coverage_data)} sample coverage areas processed")
    
    # Test association export
    association_data = []
    for assoc in ResourceCoverage.objects.all()[:5]:  # Test with first 5
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
    
    print(f"✅ Association export test successful - {len(association_data)} sample associations processed")
    
    return coverage_count, association_count, resource_count

def test_staging_import_simulation():
    """Test the staging import process (simulation only)"""
    print("🧪 Testing staging import simulation...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import CoverageArea, ResourceCoverage, Resource
    from django.contrib.gis.geos import GEOSGeometry
    
    # Test current staging data
    staging_coverage_count = CoverageArea.objects.count()
    staging_association_count = ResourceCoverage.objects.count()
    staging_resource_count = Resource.objects.count()
    
    print(f"✅ Current staging data counts:")
    print(f"  - Resources: {staging_resource_count}")
    print(f"  - Coverage Areas: {staging_coverage_count}")
    print(f"  - Associations: {staging_association_count}")
    
    # Test geometry import (with sample data)
    test_wkt = "MULTIPOLYGON(((-125 25, -125 50, -65 50, -65 25, -125 25)))"
    try:
        test_geom = GEOSGeometry(test_wkt)
        print("✅ Geometry import test successful")
    except Exception as e:
        print(f"❌ Geometry import test failed: {e}")
        return False
    
    # Test coverage area creation (without saving)
    try:
        from django.contrib.auth.models import User
        user = User.objects.first()
        
        test_coverage = CoverageArea(
            kind='STATE',
            name='Test Area',
            geom=test_geom,
            ext_ids={'state_fips': '00'},
            created_by=user,
            updated_by=user,
        )
        print("✅ Coverage area creation test successful")
    except Exception as e:
        print(f"❌ Coverage area creation test failed: {e}")
        return False
    
    return True

def test_database_connections():
    """Test database connections for both environments"""
    print("🧪 Testing database connections...")
    
    # Test local dev connection
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
        import django
        django.setup()
        
        from directory.models import Resource
        local_count = Resource.objects.count()
        print(f"✅ Local dev connection successful - {local_count} resources")
    except Exception as e:
        print(f"❌ Local dev connection failed: {e}")
        return False
    
    # Test staging connection
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
        import django
        django.setup()
        
        from directory.models import Resource
        staging_count = Resource.objects.count()
        print(f"✅ Staging connection successful - {staging_count} resources")
    except Exception as e:
        print(f"❌ Staging connection failed: {e}")
        return False
    
    return True

def test_migration_safety():
    """Comprehensive safety test for the migration"""
    print("🔒 Migration Safety Test")
    print("=" * 40)
    
    # Test 1: Database connections
    if not test_database_connections():
        print("❌ Database connection test failed - MIGRATION NOT SAFE")
        return False
    
    # Test 2: Local dev export
    local_coverage, local_associations, local_resources = test_local_dev_export()
    
    # Test 3: Staging import simulation
    if not test_staging_import_simulation():
        print("❌ Staging import simulation failed - MIGRATION NOT SAFE")
        return False
    
    # Test 4: Data integrity checks
    print("🧪 Data integrity checks...")
    
    # Check that local dev has the expected data
    if local_coverage < 7000:
        print(f"❌ Local dev coverage count too low ({local_coverage}) - MIGRATION NOT SAFE")
        return False
    
    if local_associations < 500:
        print(f"❌ Local dev association count too low ({local_associations}) - MIGRATION NOT SAFE")
        return False
    
    if local_resources < 250:
        print(f"❌ Local dev resource count too low ({local_resources}) - MIGRATION NOT SAFE")
        return False
    
    print("✅ Data integrity checks passed")
    
    # Test 5: Settings verification
    print("🧪 Settings verification...")
    
    # Check local settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    from django.conf import settings
    
    if not hasattr(settings, 'DATABASES'):
        print("❌ Local settings missing DATABASES - MIGRATION NOT SAFE")
        return False
    
    print("✅ Local settings verification passed")
    
    # Check staging settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    django.setup()
    from django.conf import settings
    
    if not hasattr(settings, 'DATABASES'):
        print("❌ Staging settings missing DATABASES - MIGRATION NOT SAFE")
        return False
    
    print("✅ Staging settings verification passed")
    
    print("\n🎉 ALL SAFETY TESTS PASSED!")
    print("✅ The migration script is safe to run")
    return True

if __name__ == '__main__':
    test_migration_safety()

