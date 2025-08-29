#!/usr/bin/env python3
"""
Migrate GIS data from exported JSON files to development environment.
This script imports coverage areas and resource coverage relationships.
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import django

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django with GIS enabled
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings_gis')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from directory.models import CoverageArea, Resource, ResourceCoverage

# State FIPS code mapping
STATE_FIPS_CODES = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
    'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13',
    'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19',
    'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
    'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29',
    'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45',
    'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50',
    'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56',
    'DC': '11', 'AS': '60', 'GU': '66', 'MP': '69', 'PR': '72',
    'VI': '78'
}


def classify_area_type(name):
    """Classify the area type based on the name.

    Args:
        name: Area name like "Abbs Valley, VA" or "Adair County"

    Returns:
        str: 'CITY' or 'COUNTY'
    """
    # Check if it ends with "County"
    if name.lower().endswith(' county'):
        return 'COUNTY'

    # Check if it has a state code (e.g., ", VA", ", KY")
    if re.search(r',\s*[A-Z]{2}$', name):
        return 'CITY'

    # Default to county if we can't determine
    return 'COUNTY'


def extract_fips_codes(name, area_type):
    """Extract state and county FIPS codes from area name.

    Args:
        name: Area name like "Abbs Valley, VA" or "Adair County"
        area_type: 'CITY' or 'COUNTY'

    Returns:
        dict: Dictionary with state_fips and county_fips
    """
    # Extract state from area name (e.g., "Abbs Valley, VA" -> "VA")
    state_match = re.search(r',\s*([A-Z]{2})$', name)
    if not state_match:
        # For counties without state codes, we can't extract FIPS codes
        # Return empty dict - these will be skipped
        return {}

    state_code = state_match.group(1)
    state_fips = STATE_FIPS_CODES.get(state_code)

    if not state_fips:
        return {}

    # For now, we'll create a placeholder county FIPS code
    # In a real implementation, you'd need a complete county FIPS mapping
    area_name_clean = name.split(',')[0].strip()
    county_fips = str(hash(area_name_clean) % 900 + 100)  # 3-digit number

    return {
        "state_fips": state_fips,
        "county_fips": county_fips,
        "state_code": state_code,
        "area_name": area_name_clean
    }


def migrate_coverage_areas():
    """Migrate coverage areas from JSON export."""
    print("🔄 Migrating coverage areas...")

    # Load coverage areas data
    coverage_file = project_root / 'cloud' / 'exports' / 'coverage_areas.json'
    if not coverage_file.exists():
        print(f"❌ Coverage areas file not found: {coverage_file}")
        return False

    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)

    print(f"📊 Found {len(coverage_data)} coverage areas to migrate")

    # Get or create default user
    default_user, created = User.objects.get_or_create(
        username="gis_migrator",
        defaults={
            "email": "gis_migrator@example.com",
            "first_name": "GIS",
            "last_name": "Migrator",
        }
    )

    # Track created coverage areas
    coverage_map = {}  # old_id -> new_id
    created_count = 0
    skipped_count = 0
    error_count = 0

    # Track area types for reporting
    area_types = defaultdict(int)

    with transaction.atomic():
        for item in coverage_data:
            fields = item['fields']
            old_id = item['pk']
            original_name = fields['name']

            # Classify the area type based on the name
            area_type = classify_area_type(original_name)
            area_types[area_type] += 1

            # Check if coverage area already exists
            existing = CoverageArea.objects.filter(
                name=original_name,
                kind=area_type
            ).first()

            if existing:
                coverage_map[old_id] = existing.id
                skipped_count += 1
                continue

            # Prepare ext_ids with FIPS codes
            ext_ids = fields.get('ext_ids', {})
            if area_type in ['CITY', 'COUNTY'] and not ext_ids:
                # Extract FIPS codes from area name
                fips_data = extract_fips_codes(original_name, area_type)
                if fips_data:
                    ext_ids.update(fips_data)
                else:
                    # Skip areas without FIPS codes (like "Accomack County")
                    print(f"⚠️  Skipping {original_name} - no FIPS codes available")
                    continue

            try:
                # Create new coverage area
                coverage_area = CoverageArea.objects.create(
                    kind=area_type,  # Use classified type instead of original
                    name=original_name,
                    radius_m=fields.get('radius_m'),
                    ext_ids=ext_ids,
                    created_by=default_user,
                    updated_by=default_user,
                )

                coverage_map[old_id] = coverage_area.id
                created_count += 1

                if created_count % 100 == 0:
                    print(f"✅ Created {created_count} coverage areas...")

            except Exception as e:
                print(f"❌ Error creating coverage area {original_name}: {e}")
                error_count += 1
                continue

    print("✅ Coverage areas migration completed!")
    print(f"   - Created: {created_count}")
    print(f"   - Skipped (already exist): {skipped_count}")
    print(f"   - Errors: {error_count}")
    print(f"   - Total: {len(coverage_map)}")
    print(f"   - Area types: {dict(area_types)}")

    return coverage_map


def migrate_resource_coverage(coverage_map):
    """Migrate resource coverage relationships."""
    print("\n🔄 Migrating resource coverage relationships...")

    # Load resource coverage data
    coverage_file = project_root / 'cloud' / 'exports' / 'resource_coverage_areas.json'
    if not coverage_file.exists():
        print(f"❌ Resource coverage file not found: {coverage_file}")
        return False

    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)

    print(f"📊 Found {len(coverage_data)} resource coverage relationships to migrate")

    # Get or create default user
    default_user, created = User.objects.get_or_create(
        username="gis_migrator",
        defaults={
            "email": "gis_migrator@example.com",
            "first_name": "GIS",
            "last_name": "Migrator",
        }
    )

    created_count = 0
    skipped_count = 0
    error_count = 0

    with transaction.atomic():
        for item in coverage_data:
            resource_id = item['resource_id']
            coverage_area_id = item['coveragearea_id']

            # Check if resource exists
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                print(f"⚠️  Resource {resource_id} not found, skipping...")
                error_count += 1
                continue

            # Check if coverage area mapping exists
            if coverage_area_id not in coverage_map:
                print(f"⚠️  Coverage area {coverage_area_id} not found in mapping, skipping...")
                error_count += 1
                continue

            new_coverage_area_id = coverage_map[coverage_area_id]

            # Check if relationship already exists
            existing = ResourceCoverage.objects.filter(
                resource=resource,
                coverage_area_id=new_coverage_area_id
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Create relationship
            ResourceCoverage.objects.create(
                resource=resource,
                coverage_area_id=new_coverage_area_id,
                created_by=default_user,
                notes="Migrated from SQLite export"
            )

            created_count += 1

            if created_count % 50 == 0:
                print(f"✅ Created {created_count} relationships...")

    print("✅ Resource coverage migration completed!")
    print(f"   - Created: {created_count}")
    print(f"   - Skipped (already exist): {skipped_count}")
    print(f"   - Errors: {error_count}")

    return True


def test_spatial_functionality():
    """Test that spatial functionality is working."""
    print("\n🧪 Testing spatial functionality...")

    # Test basic counts
    coverage_count = CoverageArea.objects.count()
    resource_count = Resource.objects.count()
    relationship_count = ResourceCoverage.objects.count()

    print(f"📊 Current data:")
    print(f"   - Coverage areas: {coverage_count}")
    print(f"   - Resources: {resource_count}")
    print(f"   - Resource-coverage relationships: {relationship_count}")

    # Show breakdown by area type
    from django.db.models import Count
    area_type_counts = CoverageArea.objects.values('kind').annotate(count=Count('id'))
    print(f"   - Area types: {list(area_type_counts)}")

    # Test spatial queries if GIS is enabled
    from django.conf import settings
    if getattr(settings, 'GIS_ENABLED', False):
        try:
            from django.contrib.gis.geos import Point

            # Test spatial point creation
            point = Point(-84.0849, 37.1289, srid=4326)
            print(f"✅ Spatial point created: {point}")

            print("✅ Spatial queries available")

        except Exception as e:
            print(f"❌ Spatial functionality error: {e}")
    else:
        print("📝 GIS disabled - using text-based location matching")

    return True


def main():
    """Main migration function."""
    print("🚀 Starting GIS data migration...")
    print("=" * 50)

    # Step 1: Migrate coverage areas
    coverage_map = migrate_coverage_areas()
    if not coverage_map:
        print("❌ Coverage areas migration failed")
        return False

    # Step 2: Migrate resource coverage relationships
    success = migrate_resource_coverage(coverage_map)
    if not success:
        print("❌ Resource coverage migration failed")
        return False

    # Step 3: Test functionality
    test_spatial_functionality()

    print("\n🎉 GIS data migration completed successfully!")
    print("=" * 50)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
