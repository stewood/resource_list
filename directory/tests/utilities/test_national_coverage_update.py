#!/usr/bin/env python3
"""
Test script to verify national coverage area maintenance functionality.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resource_directory.settings")
django.setup()

from directory.models import CoverageArea


def main():
    print("=== TESTING NATIONAL COVERAGE AREA MAINTENANCE ===\n")

    # Check current national coverage areas
    national_lower_48 = CoverageArea.objects.filter(
        name="National (Lower 48 States)", kind="POLYGON"
    ).first()

    national_all = CoverageArea.objects.filter(
        name="United States (All States and Territories)", kind="POLYGON"
    ).first()

    print("Current National Coverage Areas:")
    if national_lower_48:
        print(f"✅ National (Lower 48 States): ID {national_lower_48.id}")
        print(f"   External IDs: {national_lower_48.ext_ids}")
    else:
        print("❌ National (Lower 48 States): Not found")

    if national_all:
        print(f"✅ United States (All States and Territories): ID {national_all.id}")
        print(f"   External IDs: {national_all.ext_ids}")
    else:
        print("❌ United States (All States and Territories): Not found")

    # Count available states
    state_count = CoverageArea.objects.filter(kind="STATE").count()
    print(f"\nAvailable states in database: {state_count}")

    # Test the maintenance function
    print("\n=== TESTING MAINTENANCE FUNCTION ===")

    # Import the maintenance function
    import sys

    sys.path.append("scripts")
    from update_geographic_data import GeographicDataUpdater

    updater = GeographicDataUpdater()
    updater._maintain_national_coverage_areas()

    print("\n=== AFTER MAINTENANCE ===")

    # Refresh the objects
    national_lower_48.refresh_from_db()
    national_all.refresh_from_db()

    print("Updated National Coverage Areas:")
    if national_lower_48:
        print(f"✅ National (Lower 48 States): ID {national_lower_48.id}")
        print(f"   External IDs: {national_lower_48.ext_ids}")
    else:
        print("❌ National (Lower 48 States): Not found")

    if national_all:
        print(f"✅ United States (All States and Territories): ID {national_all.id}")
        print(f"   External IDs: {national_all.ext_ids}")
    else:
        print("❌ United States (All States and Territories): Not found")


if __name__ == "__main__":
    main()
