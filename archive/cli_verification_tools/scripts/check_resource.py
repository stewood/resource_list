#!/usr/bin/env python3
"""
Script to check the current values of specific fields for resource ID 80
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/stewood/rl')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource

def check_resource_fields():
    """Check the current values of specific fields for resource ID 80"""
    try:
        # Get the resource
        resource = Resource.objects.get(pk=80)
        
        print(f"Resource: {resource.name}")
        print(f"ID: {resource.id}")
        print(f"Status: {resource.status}")
        print(f"Last Updated: {resource.updated_at}")
        print(f"Updated By: {resource.updated_by}")
        print()
        
        # Check the fields mentioned in the AI report
        print("=== FIELDS MENTIONED IN AI REPORT ===")
        print(f"Phone: '{resource.phone}'")
        print(f"is_24_hour_service: {resource.is_24_hour_service}")
        print(f"Source: '{resource.source}'")
        print()
        
        # Check other relevant fields
        print("=== OTHER RELEVANT FIELDS ===")
        print(f"Website: '{resource.website}'")
        print(f"Address: {resource.address1}, {resource.city}, {resource.state}")
        print(f"Hours: '{resource.hours_of_operation}'")
        print(f"Emergency Service: {resource.is_emergency_service}")
        print()
        
        # Check service types and coverage areas
        service_types = [st.name for st in resource.service_types.all()]
        coverage_areas = [ca.name for ca in resource.coverage_areas.all()]
        
        print("=== SERVICE TYPES ===")
        print(f"Count: {len(service_types)}")
        for st in service_types:
            print(f"  - {st}")
        print()
        
        print("=== COVERAGE AREAS ===")
        print(f"Count: {len(coverage_areas)}")
        for ca in coverage_areas:
            print(f"  - {ca}")
        print()
        
        # Check if there are any versions
        versions = resource.versions.all().order_by('-version_number')
        print(f"=== VERSION HISTORY ===")
        print(f"Total versions: {versions.count()}")
        
        if versions.exists():
            latest = versions.first()
            print(f"Latest version: {latest.version_number}")
            print(f"Latest version date: {latest.changed_at}")
            print(f"Latest version by: {latest.changed_by}")
            
            # Check the snapshot data
            try:
                snapshot = latest.snapshot
                print(f"Snapshot keys: {list(snapshot.keys())}")
                
                # Check specific fields in snapshot
                if 'phone' in snapshot:
                    print(f"Phone in snapshot: '{snapshot['phone']}'")
                if 'is_24_hour_service' in snapshot:
                    print(f"24h service in snapshot: {snapshot['is_24_hour_service']}")
                    
            except Exception as e:
                print(f"Error reading snapshot: {e}")
        
    except Resource.DoesNotExist:
        print("Resource with ID 80 not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_resource_fields()
