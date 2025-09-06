#!/usr/bin/env python3
"""
Script to check if the name field was actually changed
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

def check_name_change():
    """Check if the name field was actually changed"""
    try:
        # Get the resource
        resource = Resource.objects.get(pk=80)
        
        print(f"=== CURRENT RESOURCE STATE ===")
        print(f"Current Name: '{resource.name}'")
        print(f"Current Status: {resource.status}")
        print(f"Last Updated: {resource.updated_at}")
        print(f"Updated By: {resource.updated_by}")
        print()
        
        # Get the last published version (version 8)
        version_8 = ResourceVersion.objects.filter(resource=resource, version_number=8).first()
        
        if version_8:
            print(f"=== VERSION 8 (LAST PUBLISHED) ===")
            print(f"Version: {version_8.version_number}")
            print(f"Date: {version_8.changed_at}")
            print(f"Changed by: {version_8.changed_by}")
            print()
            
            # Get the snapshot data
            try:
                snapshot = version_8.snapshot
                print("=== FIELD VALUES IN VERSION 8 ===")
                print(f"Name: '{snapshot.get('name', 'NOT FOUND')}'")
                print(f"Phone: '{snapshot.get('phone', 'NOT FOUND')}'")
                print(f"is_24_hour_service: {snapshot.get('is_24_hour_service', 'NOT FOUND')}")
                print(f"Source: '{snapshot.get('source', 'NOT FOUND')}'")
                
            except Exception as e:
                print(f"Error reading snapshot: {e}")
                
        # Now compare with current values
        print()
        print("=== COMPARISON WITH CURRENT VALUES ===")
        if version_8:
            print(f"Name: '{version_8.snapshot.get('name', 'NOT FOUND')}' → '{resource.name}'")
            print(f"Phone: '{version_8.snapshot.get('phone', 'NOT FOUND')}' → '{resource.phone}'")
            print(f"24h Service: {version_8.snapshot.get('is_24_hour_service', 'NOT FOUND')} → {resource.is_24_hour_service}")
            print(f"Source: '{version_8.snapshot.get('source', 'NOT FOUND')}' → '{resource.source}'")
        
        # Check if there are any newer versions
        newer_versions = ResourceVersion.objects.filter(
            resource=resource, 
            version_number__gt=8
        ).order_by('-version_number')
        
        if newer_versions.exists():
            print()
            print("=== NEWER VERSIONS AFTER PUBLICATION ===")
            for version in newer_versions:
                print(f"Version {version.version_number}: {version.changed_at} by {version.changed_by}")
                try:
                    snapshot = version.snapshot
                    print(f"  Name in this version: '{snapshot.get('name', 'NOT FOUND')}'")
                except:
                    print(f"  Error reading snapshot")
                print()
        
    except Resource.DoesNotExist:
        print("Resource with ID 80 not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_name_change()
