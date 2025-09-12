#!/usr/bin/env python3
"""
GIS Deployment Verification Script

This script verifies that GIS functionality is properly configured
and working in the deployed environment.
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def test_gis_configuration():
    """Test GIS configuration and dependencies."""
    print("🔍 Testing GIS Configuration...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.production_settings')
    
    try:
        django.setup()
        from django.conf import settings
        
        print(f"✅ Django settings loaded: {settings.SETTINGS_MODULE}")
        
        # Check GIS enabled
        gis_enabled = getattr(settings, 'GIS_ENABLED', False)
        print(f"✅ GIS Enabled: {gis_enabled}")
        
        if not gis_enabled:
            print("❌ GIS is not enabled in settings")
            return False
            
        # Check django.contrib.gis in INSTALLED_APPS
        if 'django.contrib.gis' not in settings.INSTALLED_APPS:
            print("❌ django.contrib.gis not in INSTALLED_APPS")
            return False
        print("✅ django.contrib.gis in INSTALLED_APPS")
        
        # Check database engine
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'postgis' not in db_engine:
            print(f"❌ Database engine is not PostGIS: {db_engine}")
            return False
        print(f"✅ PostGIS database engine: {db_engine}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading Django settings: {e}")
        return False

def test_gis_imports():
    """Test GIS library imports."""
    print("\n🔍 Testing GIS Library Imports...")
    
    try:
        import django.contrib.gis
        print("✅ django.contrib.gis imported successfully")
        
        from django.contrib.gis.geos import Point, MultiPolygon
        print("✅ GEOS geometry classes imported")
        
        from django.contrib.gis.db.models.functions import Distance
        print("✅ GIS database functions imported")
        
        # Test geometry creation
        point = Point(0, 0, srid=4326)
        print(f"✅ Point geometry created: {point}")
        
        return True
        
    except ImportError as e:
        print(f"❌ GIS import error: {e}")
        return False
    except Exception as e:
        print(f"❌ GIS test error: {e}")
        return False

def test_database_connection():
    """Test database connection and PostGIS extension."""
    print("\n🔍 Testing Database Connection...")
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Test basic connection
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Database connection successful")
            
            # Test PostGIS extension
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='postgis');")
            postgis_exists = cursor.fetchone()[0]
            
            if postgis_exists:
                print("✅ PostGIS extension is installed")
            else:
                print("❌ PostGIS extension is not installed")
                return False
                
            # Test spatial reference systems
            cursor.execute("SELECT COUNT(*) FROM spatial_ref_sys WHERE srid=4326;")
            srid_count = cursor.fetchone()[0]
            
            if srid_count > 0:
                print("✅ Spatial reference systems available")
            else:
                print("❌ No spatial reference systems found")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_gis_models():
    """Test GIS model functionality."""
    print("\n🔍 Testing GIS Models...")
    
    try:
        from directory.models.geographic.coverage_area import CoverageArea
        
        # Test model fields
        coverage_area = CoverageArea()
        print("✅ CoverageArea model loaded")
        
        # Check if geometry field exists
        if hasattr(coverage_area, 'geom'):
            print("✅ Geometry field exists on CoverageArea")
        else:
            print("❌ Geometry field missing on CoverageArea")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ GIS model test error: {e}")
        return False

def main():
    """Run all GIS deployment tests."""
    print("🚀 GIS Deployment Verification")
    print("=" * 50)
    
    tests = [
        test_gis_configuration,
        test_gis_imports,
        test_database_connection,
        test_gis_models,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All GIS tests passed! GIS is properly configured.")
        return 0
    else:
        print("❌ Some GIS tests failed. Check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
