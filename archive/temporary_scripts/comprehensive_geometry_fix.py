#!/usr/bin/env python3
"""
Comprehensive Geometry Fix Script

This script analyzes all resource-coverage relationships and ensures they're linked
to coverage areas with valid geometry. It handles various types of coverage areas
including states, counties, cities, and other geographic entities.
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, ResourceCoverage, CoverageArea
from django.contrib.auth.models import User
from django.db import transaction


def analyze_coverage_areas():
    """Analyze all coverage areas and their geometry status."""
    print("🔍 Analyzing Coverage Areas...")
    
    # Get all coverage areas grouped by kind
    kinds = CoverageArea.objects.values_list('kind', flat=True).distinct()
    
    for kind in kinds:
        areas = CoverageArea.objects.filter(kind=kind)
        with_geom = areas.exclude(geom__isnull=True).count()
        without_geom = areas.filter(geom__isnull=True).count()
        
        print(f"  {kind}: {with_geom} with geometry, {without_geom} without geometry")
    
    print()


def analyze_resource_coverage():
    """Analyze resource-coverage relationships."""
    print("🔍 Analyzing Resource-Coverage Relationships...")
    
    # Get relationships without geometry
    relationships_without_geom = ResourceCoverage.objects.filter(
        coverage_area__geom__isnull=True
    ).select_related('resource', 'coverage_area')
    
    print(f"📊 Found {relationships_without_geom.count()} relationships without geometry")
    
    # Group by coverage area kind
    kind_stats = {}
    for rc in relationships_without_geom:
        kind = rc.coverage_area.kind
        if kind not in kind_stats:
            kind_stats[kind] = []
        kind_stats[kind].append(rc)
    
    for kind, relationships in kind_stats.items():
        print(f"  {kind}: {len(relationships)} relationships")
        for rc in relationships[:3]:  # Show first 3 examples
            print(f"    - {rc.resource.name} -> {rc.coverage_area.name} (ID: {rc.coverage_area.id})")
        if len(relationships) > 3:
            print(f"    ... and {len(relationships) - 3} more")
    
    print()
    return relationships_without_geom


def fix_coverage_relationships(relationships_without_geom):
    """Fix resource-coverage relationships to use coverage areas with geometry."""
    print("🔧 Fixing Resource-Coverage Relationships...")
    
    # Get a user for audit trail
    user = User.objects.first()
    if not user:
        print("❌ No user found for audit trail")
        return
    
    # Create mappings for different types of coverage areas
    mappings = {}
    
    # Map Kentucky counties (already done, but double-check)
    ky_counties_with_geom = CoverageArea.objects.filter(
        kind='COUNTY',
        ext_ids__state_fips='21'
    ).exclude(geom__isnull=True)
    
    for county in ky_counties_with_geom:
        mappings[f"COUNTY_{county.name}"] = county.id
    
    # Map Kentucky state
    ky_state = CoverageArea.objects.filter(
        kind='STATE',
        ext_ids__state_fips='21'
    ).exclude(geom__isnull=True).first()
    
    if ky_state:
        mappings["STATE_Kentucky"] = ky_state.id
    
    # Map United States
    us_state = CoverageArea.objects.filter(
        kind='STATE',
        ext_ids__state_fips='00'
    ).first()
    
    if us_state:
        mappings["STATE_United States (All States and Territories)"] = us_state.id
    
    # Map cities (if we have any with geometry)
    cities_with_geom = CoverageArea.objects.filter(
        kind='CITY'
    ).exclude(geom__isnull=True)
    
    for city in cities_with_geom:
        mappings[f"CITY_{city.name}"] = city.id
    
    print(f"✅ Created mappings for {len(mappings)} coverage areas with geometry")
    
    # Fix relationships
    fixed_count = 0
    skipped_count = 0
    errors = []
    
    with transaction.atomic():
        for rc in relationships_without_geom:
            ca = rc.coverage_area
            mapping_key = f"{ca.kind}_{ca.name}"
            
            if mapping_key in mappings:
                new_id = mappings[mapping_key]
                old_id = ca.id
                
                try:
                    # Get the new coverage area
                    new_coverage_area = CoverageArea.objects.get(id=new_id)
                    
                    # Update the relationship
                    rc.coverage_area = new_coverage_area
                    rc.updated_by = user
                    rc.save()
                    
                    print(f"✅ Fixed: {rc.resource.name} -> {ca.name} (ID {old_id} -> {new_id})")
                    fixed_count += 1
                    
                except CoverageArea.DoesNotExist:
                    errors.append(f"New coverage area {new_id} not found for {mapping_key}")
                    skipped_count += 1
            else:
                print(f"⚠️  No mapping found for: {ca.kind} - {ca.name} (ID: {ca.id})")
                skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  Fixed relationships: {fixed_count}")
    print(f"  Skipped relationships: {skipped_count}")
    
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    - {error}")
    
    return fixed_count, skipped_count


def verify_fixes():
    """Verify that all resource-coverage relationships now have geometry."""
    print("\n🔍 Verifying Fixes...")
    
    # Check remaining relationships without geometry
    remaining_without_geom = ResourceCoverage.objects.filter(
        coverage_area__geom__isnull=True
    ).count()
    
    total_relationships = ResourceCoverage.objects.count()
    relationships_with_geom = ResourceCoverage.objects.filter(
        coverage_area__geom__isnull=False
    ).count()
    
    print(f"📊 Final Status:")
    print(f"  Total relationships: {total_relationships}")
    print(f"  With geometry: {relationships_with_geom}")
    print(f"  Without geometry: {remaining_without_geom}")
    
    if remaining_without_geom == 0:
        print("🎉 All resource-coverage relationships now have geometry!")
    else:
        print(f"⚠️  {remaining_without_geom} relationships still need geometry")
        
        # Show details of remaining issues
        remaining = ResourceCoverage.objects.filter(
            coverage_area__geom__isnull=True
        ).select_related('resource', 'coverage_area')[:10]
        
        print("  Remaining issues:")
        for rc in remaining:
            print(f"    - {rc.resource.name} -> {rc.coverage_area.name} ({rc.coverage_area.kind})")


def main():
    """Main function to run the comprehensive geometry fix."""
    print("🚀 Starting Comprehensive Geometry Fix...")
    print("=" * 50)
    
    # Step 1: Analyze current state
    analyze_coverage_areas()
    relationships_without_geom = analyze_resource_coverage()
    
    if not relationships_without_geom:
        print("✅ All resource-coverage relationships already have geometry!")
        return
    
    # Step 2: Fix relationships
    fixed_count, skipped_count = fix_coverage_relationships(relationships_without_geom)
    
    # Step 3: Verify fixes
    verify_fixes()
    
    print("\n🎯 Comprehensive Geometry Fix Complete!")


if __name__ == "__main__":
    main()
