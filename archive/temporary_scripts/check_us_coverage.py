#!/usr/bin/env python3
"""
Check United States Coverage Area

This script checks if we have a United States coverage area in the database.
"""
import os
import sys
import django

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import CoverageArea

def check_us_coverage():
    print("🔍 Checking for United States Coverage Area...")
    
    # Look for United States coverage
    us_coverage = CoverageArea.objects.filter(
        name__icontains='United States', 
        kind='STATE'
    ).first()
    
    if us_coverage:
        print(f"✅ Found United States Coverage Area:")
        print(f"  ID: {us_coverage.id}")
        print(f"  Name: {us_coverage.name}")
        print(f"  Kind: {us_coverage.kind}")
        print(f"  Has geometry: {us_coverage.geom is not None}")
        print(f"  FIPS codes: {us_coverage.ext_ids}")
    else:
        print("❌ No United States Coverage Area found")

if __name__ == "__main__":
    check_us_coverage()
