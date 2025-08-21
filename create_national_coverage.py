#!/usr/bin/env python3
"""
Script to create a National coverage area for the lower 48 states.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import CoverageArea
from django.contrib.auth.models import User

def main():
    print("=== CREATING NATIONAL COVERAGE AREA (LOWER 48) ===\n")
    
    # Check if National coverage area already exists
    existing = CoverageArea.objects.filter(name='National (Lower 48 States)').first()
    if existing:
        print(f"National coverage area already exists: {existing.name} (ID: {existing.id})")
        return
    
    # Get a user for the audit trail
    user = User.objects.first()
    if not user:
        print("Error: No users found in the system!")
        return
    
    print(f"Using user: {user.username}")
    
    # Create the National coverage area
    try:
        national_area = CoverageArea.objects.create(
            kind='POLYGON',
            name='National (Lower 48 States)',
            ext_ids={
                'type': 'national',
                'description': 'Lower 48 United States',
                'states_included': 'All 48 contiguous states',
                'excludes': ['Alaska', 'Hawaii', 'American Samoa', 'Guam', 'Northern Mariana Islands', 'Puerto Rico', 'U.S. Virgin Islands']
            },
            created_by=user,
            updated_by=user
        )
        
        print(f"✅ Successfully created National coverage area:")
        print(f"   ID: {national_area.id}")
        print(f"   Name: {national_area.name}")
        print(f"   Type: {national_area.kind}")
        print(f"   External IDs: {national_area.ext_ids}")
        print(f"   Created: {national_area.created_at}")
        
        # Also create a more generic "United States" option
        us_area = CoverageArea.objects.filter(name='United States').first()
        if not us_area:
            us_area = CoverageArea.objects.create(
                kind='POLYGON',
                name='United States (All States and Territories)',
                ext_ids={
                    'type': 'national',
                    'description': 'All United States and Territories',
                    'states_included': 'All 50 states plus territories',
                    'includes': ['All 50 states', 'DC', 'Puerto Rico', 'Guam', 'U.S. Virgin Islands', 'American Samoa', 'Northern Mariana Islands']
                },
                created_by=user,
                updated_by=user
            )
            print(f"\n✅ Also created United States coverage area:")
            print(f"   ID: {us_area.id}")
            print(f"   Name: {us_area.name}")
            print(f"   Type: {us_area.kind}")
            print(f"   External IDs: {us_area.ext_ids}")
        
        print(f"\n🎯 Coverage areas created successfully!")
        print(f"   - National (Lower 48 States): ID {national_area.id}")
        print(f"   - United States (All States and Territories): ID {us_area.id}")
        
    except Exception as e:
        print(f"❌ Error creating coverage area: {e}")

if __name__ == "__main__":
    main()
