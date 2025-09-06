#!/usr/bin/env python3
"""
Script to check the previous version (version 6) to compare field values
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/stewood/rl')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, ResourceVersion

def check_previous_version():
    """Check version 6 to see what the values were before changes"""
    try:
        # Get the resource
        resource = Resource.objects.get(pk=80)
        
        # Get version 6 specifically
        version_6 = ResourceVersion.objects.filter(resource=resource, version_number=6).first()
        
        if not version_6:
            print("Version 6 not found!")
            return
            
        print(f"=== VERSION 6 SNAPSHOT ===")
        print(f"Version: {version_6.version_number}")
        print(f"Date: {version_6.changed_at}")
        print(f"Changed by: {version_6.changed_by}")
        print()
        
        # Get the snapshot data
        try:
            snapshot = version_6.snapshot
            print("=== FIELD VALUES IN VERSION 6 ===")
            print(f"Phone: '{snapshot.get('phone', 'NOT FOUND')}'")
            print(f"is_24_hour_service: {snapshot.get('is_24_hour_service', 'NOT FOUND')}")
            print(f"Source: '{snapshot.get('source', 'NOT FOUND')}'")
            print(f"Website: '{snapshot.get('website', 'NOT FOUND')}'")
            print(f"Address: {snapshot.get('address1', 'NOT FOUND')}, {snapshot.get('city', 'NOT FOUND')}, {snapshot.get('state', 'NOT FOUND')}")
            print(f"Hours: '{snapshot.get('hours_of_operation', 'NOT FOUND')}'")
            print(f"Emergency Service: {snapshot.get('is_emergency_service', 'NOT FOUND')}")
            
            # Check if service types and coverage areas existed
            print(f"Service Types: {snapshot.get('service_types', 'NOT FOUND')}")
            print(f"Coverage Areas: {snapshot.get('coverage_areas', 'NOT FOUND')}")
            
        except Exception as e:
            print(f"Error reading snapshot: {e}")
            
        # Now compare with current values
        print()
        print("=== COMPARISON WITH CURRENT VALUES ===")
        print(f"Phone: '{version_6.snapshot.get('phone', 'NOT FOUND')}' → '{resource.phone}'")
        print(f"24h Service: {version_6.snapshot.get('is_24_hour_service', 'NOT FOUND')} → {resource.is_24_hour_service}")
        print(f"Source: '{version_6.snapshot.get('source', 'NOT FOUND')}' → '{resource.source}'")
        
        # Check if there were service types and coverage areas in version 6
        v6_service_types = version_6.snapshot.get('service_types', [])
        v6_coverage_areas = version_6.snapshot.get('coverage_areas', [])
        
        current_service_types = [st.name for st in resource.service_types.all()]
        current_coverage_areas = [ca.name for ca in resource.coverage_areas.all()]
        
        print(f"Service Types: {v6_service_types} → {current_service_types}")
        print(f"Coverage Areas: {v6_coverage_areas} → {current_coverage_areas}")
        
    except Resource.DoesNotExist:
        print("Resource with ID 80 not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_previous_version()
