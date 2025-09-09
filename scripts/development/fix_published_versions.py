#!/usr/bin/env python3
"""
Fix published resources that are missing version records.

This script identifies published resources that have no version history
and creates initial version records for them so the published comparison
view works correctly.
"""

import os
import sys
import django
from django.db import transaction

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, ResourceVersion
import json


def create_initial_version_for_resource(resource):
    """
    Create an initial version record for a published resource.
    
    Args:
        resource: The Resource instance to create a version for
        
    Returns:
        ResourceVersion: The created version record
    """
    print(f"Creating initial version for resource {resource.id}: {resource.name}")
    
    # Create snapshot data
    snapshot_data = {
        "id": resource.id,
        "name": resource.name,
        "category_id": resource.category_id,
        "description": resource.description,
        "phone": resource.phone,
        "email": resource.email,
        "website": resource.website,
        "address1": resource.address1,
        "address2": resource.address2,
        "city": resource.city,
        "state": resource.state,
        "postal_code": resource.postal_code,
        "county": resource.county,
        "status": resource.status,
        "source": resource.source,
        "notes": resource.notes,
        "hours_of_operation": resource.hours_of_operation,
        "eligibility_requirements": resource.eligibility_requirements,
        "populations_served": resource.populations_served,
        "cost_information": resource.cost_information,
        "languages_available": resource.languages_available,
        "is_emergency_service": resource.is_emergency_service,
        "is_24_hour_service": resource.is_24_hour_service,
        "insurance_accepted": resource.insurance_accepted,
        "capacity": resource.capacity,
        "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
        "last_verified_by_id": resource.last_verified_by_id,
        "created_at": resource.created_at.isoformat(),
        "updated_at": resource.updated_at.isoformat(),
        "created_by_id": resource.created_by_id,
        "updated_by_id": resource.updated_by_id,
        "is_deleted": resource.is_deleted,
    }
    
    # Create the version record
    version = ResourceVersion.objects.create(
        resource=resource,
        version_number=1,
        snapshot_json=json.dumps(snapshot_data),
        changed_fields=json.dumps(list(snapshot_data.keys())),
        change_type="create",
        changed_by=resource.updated_by,
    )
    
    print(f"  ✅ Created version {version.version_number} for {resource.name}")
    return version


def fix_published_resources():
    """
    Find and fix published resources that are missing version records.
    """
    print("🔍 Finding published resources without version records...")
    
    # Find published resources
    published_resources = Resource.objects.filter(
        status='published',
        is_deleted=False
    )
    
    print(f"Found {published_resources.count()} published resources")
    
    # Check which ones are missing versions
    resources_to_fix = []
    for resource in published_resources:
        version_count = ResourceVersion.objects.filter(resource=resource).count()
        if version_count == 0:
            resources_to_fix.append(resource)
            print(f"  ❌ Resource {resource.id}: {resource.name} - No versions")
        else:
            print(f"  ✅ Resource {resource.id}: {resource.name} - {version_count} versions")
    
    if not resources_to_fix:
        print("🎉 All published resources already have version records!")
        return
    
    print(f"\n🔧 Found {len(resources_to_fix)} resources that need fixing")
    
    # Confirm before proceeding
    response = input(f"\nProceed to create version records for {len(resources_to_fix)} resources? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Create version records
    created_versions = []
    with transaction.atomic():
        for resource in resources_to_fix:
            try:
                version = create_initial_version_for_resource(resource)
                created_versions.append(version)
            except Exception as e:
                print(f"  ❌ Failed to create version for {resource.name}: {e}")
                raise
    
    print(f"\n🎉 Successfully created {len(created_versions)} version records!")
    print("Published comparison views should now work correctly for these resources.")


def verify_fix():
    """
    Verify that the fix worked by checking version counts.
    """
    print("\n🔍 Verifying fix...")
    
    published_resources = Resource.objects.filter(
        status='published',
        is_deleted=False
    )
    
    all_fixed = True
    for resource in published_resources:
        version_count = ResourceVersion.objects.filter(resource=resource).count()
        if version_count == 0:
            print(f"  ❌ Resource {resource.id}: {resource.name} - Still no versions")
            all_fixed = False
        else:
            print(f"  ✅ Resource {resource.id}: {resource.name} - {version_count} versions")
    
    if all_fixed:
        print("\n🎉 All published resources now have version records!")
    else:
        print("\n⚠️  Some resources still need fixing.")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Fix Published Resources Missing Version Records")
    print("=" * 60)
    
    try:
        fix_published_resources()
        verify_fix()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
