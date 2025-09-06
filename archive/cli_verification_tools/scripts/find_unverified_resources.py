#!/usr/bin/env python3
"""
Script to find resources that need verification
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

def find_unverified_resources():
    """Find resources that need verification"""
    try:
        # Find resources without verification dates (highest priority)
        unverified = Resource.objects.filter(last_verified_at__isnull=True).order_by('?')[:10]
        
        print("=== RESOURCES NEEDING VERIFICATION (No verification date) ===")
        print(f"Found {unverified.count()} resources without verification dates")
        print()
        
        for resource in unverified:
            print(f"ID: {resource.id}")
            print(f"Name: {resource.name}")
            print(f"Status: {resource.status}")
            print(f"Category: {resource.category.name if resource.category else 'None'}")
            print(f"City: {resource.city}")
            print(f"Last Updated: {resource.updated_at}")
            print("-" * 50)
        
        # Also check for published resources without verification (highest priority)
        published_unverified = Resource.objects.filter(
            status='published',
            last_verified_at__isnull=True
        ).order_by('?')[:5]
        
        print("\n=== PUBLISHED RESOURCES WITHOUT VERIFICATION (HIGHEST PRIORITY) ===")
        print(f"Found {published_unverified.count()} published resources without verification")
        print()
        
        for resource in published_unverified:
            print(f"ID: {resource.id}")
            print(f"Name: {resource.name}")
            print(f"Status: {resource.status}")
            print(f"Category: {resource.category.name if resource.category else 'None'}")
            print(f"City: {resource.city}")
            print(f"Last Updated: {resource.updated_at}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_unverified_resources()