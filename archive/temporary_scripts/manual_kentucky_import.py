#!/usr/bin/env python3
"""
Manual Kentucky State Import

This script manually imports Kentucky state with geometry to test the import process.

Author: Resource Directory Team
Created: 2025-01-15
"""

import json
import os
import sys
import tempfile
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import django

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from directory.models import CoverageArea


def import_kentucky_manually():
    """Manually import Kentucky state with geometry."""
    print("🔧 Manually importing Kentucky state...")
    
    # Download and convert state data
    url = "https://www2.census.gov/geo/tiger/TIGER2023/STATE/tl_2023_us_state.zip"
    filename = "tl_2023_us_state.zip"
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, filename)
    extract_path = os.path.join(temp_dir, "tl_2023_us_state")
    
    try:
        print(f"📥 Downloading {url}...")
        urllib.request.urlretrieve(url, zip_path)
        print(f"✅ Download completed: {os.path.getsize(zip_path):,} bytes")
        
        # Extract the zip file
        print("📦 Extracting files...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Find the .shp file
        shp_files = [f for f in os.listdir(extract_path) if f.endswith('.shp')]
        if not shp_files:
            print("❌ No shapefile found")
            return
        
        shapefile_path = os.path.join(extract_path, shp_files[0])
        print(f"✅ Found shapefile: {shp_files[0]}")
        
        # Convert to GeoJSON
        print("🔄 Converting to GeoJSON...")
        geojson_path = os.path.join(temp_dir, "states.geojson")
        
        cmd = [
            'ogr2ogr',
            '-f', 'GeoJSON',
            '-t_srs', 'EPSG:4326',
            geojson_path,
            shapefile_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ ogr2ogr failed: {result.stderr}")
            return
        
        print("✅ GeoJSON conversion successful")
        
        # Parse GeoJSON and find Kentucky
        print("📊 Finding Kentucky in data...")
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        kentucky_feature = None
        for feature in geojson_data['features']:
            properties = feature['properties']
            state_name = properties.get('NAME', 'Unknown')
            state_fips = properties.get('STATEFP', 'Unknown')
            
            if state_name == 'Kentucky' or state_fips == '21':
                kentucky_feature = feature
                print(f"🎯 Found Kentucky: {state_name} (FIPS: {state_fips})")
                break
        
        if not kentucky_feature:
            print("❌ Kentucky not found in data")
            return
        
        # Get user for audit trail
        user = User.objects.first()
        if not user:
            print("❌ No user found for audit trail")
            return
        
        # Create Kentucky state coverage area
        print("🏗️ Creating Kentucky state coverage area...")
        
        properties = kentucky_feature['properties']
        geometry = kentucky_feature['geometry']
        
        # Create geometry object
        geom_obj = GEOSGeometry(json.dumps(geometry))
        
        # Convert single polygon to multipolygon if needed
        if geom_obj.geom_type == 'Polygon':
            geom_obj = MultiPolygon([geom_obj])
        
        # Create the coverage area
        kentucky_state = CoverageArea.objects.create(
            kind='STATE',
            name='Kentucky',
            geom=geom_obj,
            ext_ids={
                'state_fips': '21',
                'state_code': 'KY',
                'state_name': 'Kentucky'
            },
            created_by=user,
            updated_by=user
        )
        
        print(f"✅ Successfully created Kentucky state coverage area:")
        print(f"   ID: {kentucky_state.id}")
        print(f"   Name: {kentucky_state.name}")
        print(f"   Kind: {kentucky_state.kind}")
        print(f"   ext_ids: {kentucky_state.ext_ids}")
        print(f"   Has geometry: {kentucky_state.geom is not None}")
        
        if kentucky_state.geom:
            print(f"   Geometry type: {kentucky_state.geom.geom_type}")
            print(f"   Geometry bounds: {kentucky_state.geom.extent}")
        
        # Verify it was created
        print("\n🔍 Verifying creation...")
        created_state = CoverageArea.objects.filter(
            kind='STATE',
            ext_ids__state_fips='21'
        ).first()
        
        if created_state:
            print(f"✅ Kentucky state verified in database: {created_state.name}")
        else:
            print("❌ Kentucky state not found in database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import_kentucky_manually()
