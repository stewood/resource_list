#!/usr/bin/env python3
"""
Script to debug the comparison logic
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
from directory.utils.version_utils import compare_versions

def debug_comparison():
    """Debug the comparison logic"""
    try:
        # Get the resource
        resource = Resource.objects.get(pk=80)
        
        # Get the last published version (version 8)
        version_8 = ResourceVersion.objects.filter(resource=resource, version_number=8).first()
        
        if not version_8:
            print("Version 8 not found!")
            return
            
        print(f"=== DEBUGGING COMPARISON LOGIC ===")
        print(f"Resource: {resource.name}")
        print(f"Published Version: {version_8.version_number}")
        print()
        
        # Create the same snapshots as the view does
        published_snapshot = version_8.snapshot
        
        # Filter out system/metadata fields (same as view)
        system_fields_to_exclude = {
            'id', 'created_by_id', 'updated_by_id', 'last_verified_by_id',
            'created_at', 'updated_at', 'is_deleted', 'last_verified_at', 'source', 'notes'
        }
        
        # Create filtered published snapshot
        filtered_published_snapshot = {}
        for key, value in published_snapshot.items():
            if key not in system_fields_to_exclude:
                if key == 'category_id' and value:
                    try:
                        from directory.models import TaxonomyCategory
                        category = TaxonomyCategory.objects.get(id=value)
                        filtered_published_snapshot['category'] = category.name
                    except TaxonomyCategory.DoesNotExist:
                        filtered_published_snapshot['category'] = ""
                else:
                    filtered_published_snapshot[key] = value
        
        # Create current snapshot (same as view)
        current_snapshot = {
            "name": resource.name,
            "category": resource.category.name if resource.category else "",
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
            "hours_of_operation": resource.hours_of_operation,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            "is_emergency_service": resource.is_emergency_service,
            "is_24_hour_service": resource.is_24_hour_service,
            "insurance_accepted": resource.insurance_accepted,
            "capacity": resource.capacity,
            "service_types": ", ".join([st.name for st in resource.service_types.all()]) if resource.service_types.exists() else "",
            "coverage_areas": ", ".join([ca.name for ca in resource.coverage_areas.all()]) if resource.coverage_areas.exists() else "",
            "status": resource.status,
            "source": resource.source,
            "last_verified_by": (
                resource.last_verified_by.get_full_name()
                if resource.last_verified_by
                else ""
            ),
        }
        
        print("=== PUBLISHED SNAPSHOT (FILTERED) ===")
        for key, value in filtered_published_snapshot.items():
            print(f"{key}: '{value}'")
        print()
        
        print("=== CURRENT SNAPSHOT ===")
        for key, value in current_snapshot.items():
            print(f"{key}: '{value}'")
        print()
        
        # Test the comparison
        print("=== TESTING COMPARISON ===")
        all_differences = compare_versions(filtered_published_snapshot, current_snapshot)
        
        print(f"Total differences found: {len(all_differences)}")
        for field, diff in all_differences.items():
            print(f"Field: {field}")
            print(f"  Type: {diff['diff_type']}")
            print(f"  Old: '{diff['old_value']}'")
            print(f"  New: '{diff['new_value']}'")
            print()
        
        # Test specific field comparison
        print("=== TESTING SPECIFIC FIELDS ===")
        name_old = filtered_published_snapshot.get('name')
        name_new = current_snapshot.get('name')
        print(f"Name comparison:")
        print(f"  Published: '{name_old}' (type: {type(name_old)})")
        print(f"  Current: '{name_new}' (type: {type(name_new)})")
        print(f"  Equal?: {name_old == name_new}")
        print(f"  Is None?: {name_old is None or name_new is None}")
        
        phone_old = filtered_published_snapshot.get('phone')
        phone_new = current_snapshot.get('phone')
        print(f"Phone comparison:")
        print(f"  Published: '{phone_old}' (type: {type(phone_old)})")
        print(f"  Current: '{phone_new}' (type: {type(phone_new)})")
        print(f"  Equal?: {phone_old == phone_new}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_comparison()
