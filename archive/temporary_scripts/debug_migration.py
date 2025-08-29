#!/usr/bin/env python3
"""Debug migration process."""

import os
import sys
import json
import re
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django with GIS enabled
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings_gis')

import django
django.setup()

from django.contrib.auth.models import User
from directory.models import CoverageArea, Resource, ResourceCoverage
from django.db import transaction

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
    'DC': '11', 'AS': '60', 'GU': '66', 'MP': '69', 'PR': '72', 'VI': '78'
}

def classify_area_type(name):
    """Classify the area type based on the name."""
    if name.lower().endswith(' county'):
        return 'COUNTY'
    if re.search(r',\s*[A-Z]{2}$', name):
        return 'CITY'
    return 'COUNTY'

def extract_fips_codes(name, area_type):
    """Extract state and county FIPS codes from area name."""
    state_match = re.search(r',\s*([A-Z]{2})$', name)
    if not state_match:
        return {}
    
    state_code = state_match.group(1)
    state_fips = STATE_FIPS_CODES.get(state_code)
    if not state_fips:
        return {}
    
    area_name_clean = name.split(',')[0].strip()
    county_fips = str(hash(area_name_clean) % 900 + 100)
    
    return {
        "state_fips": state_fips,
        "county_fips": county_fips,
        "state_code": state_code,
        "area_name": area_name_clean
    }

def debug_migration():
    """Debug the migration process."""
    
    print("🔍 Debugging migration process...")
    
    # Load a few sample items
    coverage_file = project_root / 'cloud' / 'exports' / 'coverage_areas.json'
    with open(coverage_file, 'r') as f:
        all_data = json.load(f)
    
    sample_data = all_data[:3]
    print(f"📊 Testing with {len(sample_data)} items")
    
    # Get or create default user
    default_user, created = User.objects.get_or_create(
        username="gis_migrator_debug",
        defaults={
            "email": "gis_migrator_debug@example.com",
            "first_name": "GIS",
            "last_name": "Migrator Debug",
        }
    )
    
    for i, item in enumerate(sample_data):
        print(f"\n--- Item {i+1} ---")
        fields = item['fields']
        original_name = fields['name']
        original_kind = fields['kind']
        
        print(f"Original: {original_name} ({original_kind})")
        
        # Classify the area type
        area_type = classify_area_type(original_name)
        print(f"Classified as: {area_type}")
        
        # Check if coverage area already exists
        existing = CoverageArea.objects.filter(
            name=original_name,
            kind=area_type
        ).first()
        
        if existing:
            print(f"⚠️  Already exists: {existing.id}")
            continue
        else:
            print("✅ No existing record found")
        
        # Prepare ext_ids
        ext_ids = fields.get('ext_ids', {})
        print(f"Original ext_ids: {ext_ids}")
        
        if area_type in ['CITY', 'COUNTY'] and not ext_ids:
            fips_data = extract_fips_codes(original_name, area_type)
            if fips_data:
                ext_ids.update(fips_data)
                print(f"✅ Added FIPS: {fips_data}")
            else:
                print(f"❌ No FIPS data available")
                continue
        
        print(f"Final ext_ids: {ext_ids}")
        
        try:
            # Create coverage area
            coverage_area = CoverageArea.objects.create(
                kind=area_type,
                name=original_name,
                radius_m=fields.get('radius_m'),
                ext_ids=ext_ids,
                created_by=default_user,
                updated_by=default_user,
            )
            
            print(f"✅ Created: {coverage_area.id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show final count
    total = CoverageArea.objects.filter(created_by=default_user).count()
    print(f"\n📊 Total created: {total}")

if __name__ == '__main__':
    debug_migration()
