#!/usr/bin/env python3
"""
Debug State Import Script

This script helps debug the state import process by examining the GeoJSON data
and checking what states are actually available.

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
from directory.models import CoverageArea


def download_and_convert_state_data():
    """Download and convert state data to see what's available."""
    print("🔍 Debugging state import process...")
    
    # Download the state shapefile
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
        
        # Parse GeoJSON and examine data
        print("📊 Examining GeoJSON data...")
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        print(f"📈 Total features: {len(geojson_data['features'])}")
        
        # Look for Kentucky specifically
        kentucky_found = False
        for feature in geojson_data['features']:
            properties = feature['properties']
            state_name = properties.get('NAME', 'Unknown')
            state_fips = properties.get('STATEFP', 'Unknown')
            
            if state_name == 'Kentucky' or state_fips == '21':
                print(f"🎯 Found Kentucky!")
                print(f"   Name: {state_name}")
                print(f"   FIPS: {state_fips}")
                print(f"   Properties: {properties}")
                kentucky_found = True
                break
        
        if not kentucky_found:
            print("❌ Kentucky not found in data")
            print("🔍 Available states (first 10):")
            for i, feature in enumerate(geojson_data['features'][:10]):
                properties = feature['properties']
                state_name = properties.get('NAME', 'Unknown')
                state_fips = properties.get('STATEFP', 'Unknown')
                print(f"   {i+1}. {state_name} (FIPS: {state_fips})")
        
        # Check existing coverage areas
        print("\n📋 Existing coverage areas:")
        existing_states = CoverageArea.objects.filter(kind='STATE')
        for state in existing_states:
            print(f"   {state.id}: {state.name} - ext_ids: {state.ext_ids}")
        
        # Check if Kentucky exists
        kentucky_exists = CoverageArea.objects.filter(
            kind='STATE',
            ext_ids__state_fips='21'
        ).first()
        
        if kentucky_exists:
            print(f"✅ Kentucky state already exists: {kentucky_exists.name}")
        else:
            print("❌ Kentucky state does not exist in database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    download_and_convert_state_data()
