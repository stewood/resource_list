#!/usr/bin/env python3
"""
Script to investigate same-state duplicates in the CoverageArea database table.
"""

import os
import sys
import django
from collections import defaultdict

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import CoverageArea


def investigate_same_state_duplicates():
    """Investigate duplicates within the same state to determine if they're legitimate."""
    
    print("🔍 Investigating same-state duplicates...")
    print("=" * 60)
    
    # Get all coverage areas
    coverage_areas = CoverageArea.objects.all()
    
    # Find same-state duplicates
    state_name_counts = defaultdict(list)
    for ca in coverage_areas:
        if ca.ext_ids and 'state_fips' in ca.ext_ids:
            state_fips = ca.ext_ids['state_fips']
            key = (ca.name, state_fips)
            state_name_counts[key].append(ca)
    
    same_state_duplicates = {key: records for key, records in state_name_counts.items() if len(records) > 1}
    
    print(f"Found {len(same_state_duplicates)} same-state duplicates to investigate:")
    print()
    
    # State name mapping for better display
    state_names = {
        '21': 'Kentucky', '18': 'Indiana', '17': 'Illinois', '29': 'Missouri',
        '47': 'Tennessee', '39': 'Ohio', '51': 'Virginia', '54': 'West Virginia'
    }
    
    for (name, state_fips), records in same_state_duplicates.items():
        state_name = state_names.get(state_fips, f"State {state_fips}")
        print(f"📍 {name} in {state_name} (FIPS {state_fips}): {len(records)} records")
        
        for i, record in enumerate(records, 1):
            print(f"   {i}. ID {record.id}: {record.kind}")
            print(f"      ext_ids: {record.ext_ids}")
            print(f"      created: {record.created_at}")
            print(f"      created_by: {record.created_by}")
            print()
        
        # Check if these are actually duplicates or different entities
        kinds = set(r.kind for r in records)
        ext_ids_sets = [set(r.ext_ids.items()) for r in records]
        
        if len(kinds) > 1:
            print(f"   ✅ LEGITIMATE: Different kinds ({', '.join(kinds)})")
        elif len(set(tuple(sorted(r.ext_ids.items())) for r in records)) > 1:
            print(f"   ✅ LEGITIMATE: Different ext_ids")
        else:
            print(f"   ⚠️  POTENTIAL DUPLICATE: Same kind and ext_ids")
        
        print("-" * 60)
        print()


def check_for_actual_duplicates():
    """Check for actual duplicates (same kind, name, and ext_ids)."""
    
    print("🔍 Checking for actual duplicates...")
    print("=" * 60)
    
    # Get all coverage areas
    coverage_areas = CoverageArea.objects.all()
    
    # Group by key characteristics
    duplicate_groups = defaultdict(list)
    for ca in coverage_areas:
        # Create a key that includes all identifying characteristics
        key = (
            ca.name,
            ca.kind,
            tuple(sorted(ca.ext_ids.items())) if ca.ext_ids else ()
        )
        duplicate_groups[key].append(ca)
    
    # Find actual duplicates
    actual_duplicates = {key: records for key, records in duplicate_groups.items() if len(records) > 1}
    
    if actual_duplicates:
        print(f"⚠️  Found {len(actual_duplicates)} actual duplicates:")
        print()
        
        for (name, kind, ext_ids), records in actual_duplicates.items():
            print(f"📍 {name} ({kind})")
            print(f"   ext_ids: {dict(ext_ids)}")
            print(f"   Count: {len(records)}")
            
            for i, record in enumerate(records, 1):
                print(f"   {i}. ID {record.id}")
                print(f"      created: {record.created_at}")
                print(f"      created_by: {record.created_by}")
            
            print("-" * 40)
            print()
    else:
        print("✅ No actual duplicates found!")
        print("   All records with the same name, kind, and ext_ids are unique.")


if __name__ == "__main__":
    investigate_same_state_duplicates()
    print("\n" + "=" * 60 + "\n")
    check_for_actual_duplicates()
