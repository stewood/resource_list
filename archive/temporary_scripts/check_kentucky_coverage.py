#!/usr/bin/env python3
"""
Check Kentucky State Coverage Area

This script checks if we have a Kentucky State coverage area in the database.
"""
import os
import sys
import django

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import CoverageArea

def check_kentucky_coverage():
    print("🔍 Checking for Kentucky State Coverage Area...")
    
    # Look for Kentucky state coverage
    kentucky_state = CoverageArea.objects.filter(
        name__icontains='Kentucky', 
        kind='STATE'
    ).first()
    
    if kentucky_state:
        print(f"✅ Found Kentucky State Coverage Area:")
        print(f"  ID: {kentucky_state.id}")
        print(f"  Name: {kentucky_state.name}")
        print(f"  Kind: {kentucky_state.kind}")
        print(f"  Has geometry: {kentucky_state.geom is not None}")
        print(f"  FIPS codes: {kentucky_state.ext_ids}")
    else:
        print("❌ No Kentucky State Coverage Area found")
        
        # Check what state coverage areas we do have
        state_areas = CoverageArea.objects.filter(kind='STATE')
        print(f"\n📋 Available State Coverage Areas ({state_areas.count()}):")
        for area in state_areas:
            print(f"  - {area.name} (ID: {area.id})")

if __name__ == "__main__":
    check_kentucky_coverage()
