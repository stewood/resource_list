#!/usr/bin/env python3
"""
Check Resources Without Coverage Areas

This script identifies resources that don't have any coverage areas assigned.
"""
import os
import sys
import django

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, ResourceCoverage

def check_resources_without_coverage():
    print("🔍 Checking Resources Without Coverage Areas...")
    
    # Get all resources
    total_resources = Resource.objects.count()
    
    # Get resources with coverage areas
    resources_with_coverage = Resource.objects.filter(
        resource_coverage_associations__isnull=False
    ).distinct().count()
    
    # Calculate resources without coverage
    resources_without_coverage = total_resources - resources_with_coverage
    
    print(f"📊 Summary:")
    print(f"  Total Resources: {total_resources}")
    print(f"  Resources with Coverage Areas: {resources_with_coverage}")
    print(f"  Resources WITHOUT Coverage Areas: {resources_without_coverage}")
    
    if resources_without_coverage > 0:
        print(f"\n📋 Resources WITHOUT Coverage Areas:")
        
        # Get the actual resources without coverage
        resources_without = Resource.objects.filter(
            resource_coverage_associations__isnull=True
        ).order_by('id')
        
        for i, resource in enumerate(resources_without, 1):
            print(f"  {i:3d}. ID {resource.id:3d} - {resource.name}")
            print(f"       Location: {resource.city}, {resource.state}")
            print(f"       Category: {resource.category.name if resource.category else 'None'}")
            print()
            
            # Show first 20 to avoid overwhelming output
            if i >= 20:
                remaining = resources_without_coverage - 20
                print(f"  ... and {remaining} more resources")
                break
    else:
        print("✅ All resources have coverage areas assigned!")

if __name__ == "__main__":
    check_resources_without_coverage()
