#!/usr/bin/env python3
"""
Script to check for duplicates in the CoverageArea database table.
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


def check_duplicates():
    """Check for duplicates in the CoverageArea table using various criteria."""
    
    print("🔍 Checking for duplicates in CoverageArea table...")
    print("=" * 60)
    
    # Get all coverage areas
    coverage_areas = CoverageArea.objects.all()
    total_count = coverage_areas.count()
    print(f"📊 Total records: {total_count:,}")
    print()
    
    # Check 1: Duplicates by name
    print("1️⃣ Checking for duplicate names...")
    name_counts = defaultdict(list)
    for ca in coverage_areas:
        name_counts[ca.name].append(ca)
    
    name_duplicates = {name: records for name, records in name_counts.items() if len(records) > 1}
    if name_duplicates:
        print(f"⚠️  Found {len(name_duplicates)} names with duplicates:")
        for name, records in list(name_duplicates.items())[:10]:  # Show first 10
            print(f"   '{name}': {len(records)} records (IDs: {[r.id for r in records[:5]]})")
        if len(name_duplicates) > 10:
            print(f"   ... and {len(name_duplicates) - 10} more")
    else:
        print("✅ No duplicate names found")
    print()
    
    # Check 2: Duplicates by name + kind
    print("2️⃣ Checking for duplicate names within same kind...")
    kind_name_counts = defaultdict(list)
    for ca in coverage_areas:
        key = (ca.name, ca.kind)
        kind_name_counts[key].append(ca)
    
    kind_name_duplicates = {key: records for key, records in kind_name_counts.items() if len(records) > 1}
    if kind_name_duplicates:
        print(f"⚠️  Found {len(kind_name_duplicates)} name+kind combinations with duplicates:")
        for (name, kind_val), records in list(kind_name_duplicates.items())[:10]:  # Show first 10
            print(f"   '{name}' ({kind_val}): {len(records)} records (IDs: {[r.id for r in records[:5]]})")
        if len(kind_name_duplicates) > 10:
            print(f"   ... and {len(kind_name_duplicates) - 10} more")
    else:
        print("✅ No duplicate name+kind combinations found")
    print()
    
    # Check 3: Duplicates by ext_ids (FIPS codes)
    print("3️⃣ Checking for duplicate FIPS codes...")
    fips_counts = defaultdict(list)
    for ca in coverage_areas:
        if ca.ext_ids and 'fips' in ca.ext_ids:
            fips_code = ca.ext_ids['fips']
            fips_counts[fips_code].append(ca)
    
    fips_duplicates = {fips: records for fips, records in fips_counts.items() if len(records) > 1}
    if fips_duplicates:
        print(f"⚠️  Found {len(fips_duplicates)} FIPS codes with duplicates:")
        for fips, records in list(fips_duplicates.items())[:10]:  # Show first 10
            print(f"   FIPS {fips}: {len(records)} records (IDs: {[r.id for r in records[:5]]})")
            for record in records[:3]:
                print(f"      - ID {record.id}: '{record.name}' ({record.type})")
        if len(fips_duplicates) > 10:
            print(f"   ... and {len(fips_duplicates) - 10} more")
    else:
        print("✅ No duplicate FIPS codes found")
    print()
    
    # Check 4: Duplicates by exact same ext_ids
    print("4️⃣ Checking for duplicate ext_ids combinations...")
    ext_ids_counts = defaultdict(list)
    for ca in coverage_areas:
        if ca.ext_ids:
            # Convert to tuple for hashing
            ext_ids_tuple = tuple(sorted(ca.ext_ids.items()))
            ext_ids_counts[ext_ids_tuple].append(ca)
    
    ext_ids_duplicates = {ext_ids: records for ext_ids, records in ext_ids_counts.items() if len(records) > 1}
    if ext_ids_duplicates:
        print(f"⚠️  Found {len(ext_ids_duplicates)} ext_ids combinations with duplicates:")
        for ext_ids, records in list(ext_ids_duplicates.items())[:5]:  # Show first 5
            print(f"   {dict(ext_ids)}: {len(records)} records (IDs: {[r.id for r in records[:5]]})")
            for record in records[:3]:
                print(f"      - ID {record.id}: '{record.name}' ({record.type})")
        if len(ext_ids_duplicates) > 5:
            print(f"   ... and {len(ext_ids_duplicates) - 5} more")
    else:
        print("✅ No duplicate ext_ids combinations found")
    print()
    
    # Check 5: Duplicates by type and state
    print("5️⃣ Checking for duplicate names within same state...")
    state_name_counts = defaultdict(list)
    for ca in coverage_areas:
        if ca.ext_ids and 'state_fips' in ca.ext_ids:
            state_fips = ca.ext_ids['state_fips']
            key = (ca.name, state_fips)
            state_name_counts[key].append(ca)
    
    state_name_duplicates = {key: records for key, records in state_name_counts.items() if len(records) > 1}
    if state_name_duplicates:
        print(f"⚠️  Found {len(state_name_duplicates)} name+state combinations with duplicates:")
        for (name, state_fips), records in list(state_name_duplicates.items())[:10]:  # Show first 10
            print(f"   '{name}' (State FIPS {state_fips}): {len(records)} records (IDs: {[r.id for r in records[:5]]})")
        if len(state_name_duplicates) > 10:
            print(f"   ... and {len(state_name_duplicates) - 10} more")
    else:
        print("✅ No duplicate name+state combinations found")
    print()
    
    # Summary
    print("📋 Summary:")
    print(f"   Total records: {total_count:,}")
    print(f"   Duplicate names: {len(name_duplicates)}")
    print(f"   Duplicate name+kind: {len(kind_name_duplicates)}")
    print(f"   Duplicate FIPS codes: {len(fips_duplicates)}")
    print(f"   Duplicate ext_ids: {len(ext_ids_duplicates)}")
    print(f"   Duplicate name+state: {len(state_name_duplicates)}")
    
    # Check if any duplicates exist
    total_duplicates = len(name_duplicates) + len(kind_name_duplicates) + len(fips_duplicates) + len(ext_ids_duplicates) + len(state_name_duplicates)
    
    if total_duplicates == 0:
        print("\n🎉 No duplicates found! Database is clean.")
    else:
        print(f"\n⚠️  Found {total_duplicates} types of potential duplicates.")
        print("   Note: Some duplicates might be legitimate (e.g., cities with same name in different states)")


if __name__ == "__main__":
    check_duplicates()
