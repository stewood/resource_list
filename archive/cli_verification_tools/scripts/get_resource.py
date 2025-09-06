#!/usr/bin/env python3
"""
Simple script to get a resource that needs verification
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

def get_resource_for_verification():
    """Get a resource that needs verification"""
    try:
        # Try to get a resource by ID first (let's try ID 1)
        try:
            resource = Resource.objects.get(id=1)
            print(f"Found resource ID 1: {resource.name}")
            return resource
        except Resource.DoesNotExist:
            pass
        
        # Try to get any resource
        resource = Resource.objects.first()
        if resource:
            print(f"Found resource ID {resource.id}: {resource.name}")
            return resource
        else:
            print("No resources found in database")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    resource = get_resource_for_verification()
    if resource:
        print(f"Resource ID: {resource.id}")
        print(f"Name: {resource.name}")
        print(f"Status: {resource.status}")
        print(f"Last Verified: {resource.last_verified_at}")
        print(f"Category: {resource.category.name if resource.category else 'None'}")
        print(f"City: {resource.city}")
        print(f"Phone: {resource.phone}")
        print(f"Website: {resource.website}")
        print(f"Description: {resource.description}")