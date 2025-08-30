#!/usr/bin/env python3
"""
Test script to verify PostGIS connectivity and functionality.
This script tests if the PostGIS backend is working properly.
"""

import os
import sys
import django
from django.conf import settings

def test_postgis_connection():
    """Test PostGIS connection and basic functionality."""
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    django.setup()
    
    try:
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL version: {version}")
            
        # Test PostGIS extension
        with connection.cursor() as cursor:
            cursor.execute("SELECT PostGIS_Version();")
            postgis_version = cursor.fetchone()[0]
            print(f"✅ PostGIS version: {postgis_version}")
            
        # Test spatial functions
        with connection.cursor() as cursor:
            cursor.execute("SELECT ST_AsText(ST_GeomFromText('POINT(0 0)'));")
            result = cursor.fetchone()[0]
            print(f"✅ Spatial function test: {result}")
            
        # Test Django GIS imports
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models import PointField
        print("✅ Django GIS imports successful")
        
        # Test CoverageArea model import
        from directory.models import CoverageArea
        print("✅ CoverageArea model import successful")
        
        # Test basic query
        count = CoverageArea.objects.count()
        print(f"✅ CoverageArea count: {count}")
        
        print("\n🎉 All PostGIS tests passed! The configuration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ PostGIS test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_postgis_connection()
    sys.exit(0 if success else 1)

