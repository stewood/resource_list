#!/usr/bin/env python3
"""
Final Geometry Fix Script

This script handles the remaining resource-coverage relationships that need geometry.
It focuses on cities and other states that don't have geometry data.
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


def analyze_remaining_issues():
    """Analyze the remaining relationships without geometry."""
    print("🔍 Analyzing Remaining Issues...")
    
    # Get relationships without geometry
    relationships_without_geom = ResourceCoverage.objects.filter(
        coverage_area__geom__isnull=True
    ).select_related('resource', 'coverage_area')
    
    print(f"📊 Found {relationships_without_geom.count()} relationships without geometry")
    
    # Group by coverage area kind and name
    issues = {}
    for rc in relationships_without_geom:
        ca = rc.coverage_area
        key = f"{ca.kind}_{ca.name}"
        if key not in issues:
            issues[key] = {
                'coverage_area': ca,
                'resources': []
            }
        issues[key]['resources'].append(rc.resource.name)
    
    print(f"📋 Unique coverage areas needing geometry: {len(issues)}")
    
    for key, data in issues.items():
        ca = data['coverage_area']
        resources = data['resources']
        print(f"  {ca.kind}: {ca.name} (ID: {ca.id})")
        print(f"    Resources: {len(resources)}")
        print(f"    Sample: {', '.join(resources[:3])}")
        if len(resources) > 3:
            print(f"    ... and {len(resources) - 3} more")
        print()
    
    return issues


def create_geometry_for_cities():
    """Create geometry for Kentucky cities that are missing it."""
    print("🏗️ Creating Geometry for Kentucky Cities...")
    
    # Get a user for audit trail
    user = User.objects.first()
    if not user:
        print("❌ No user found for audit trail")
        return 0
    
    # Kentucky cities that need geometry
    kentucky_cities = [
        'London, KY',
        'Corbin, KY', 
        'Somerset, KY',
        'Livingston, KY',
        'Martin, KY',
        'Berea, KY',
        'Manchester, KY',
        'Monticello, KY',
        'Nicholasville, KY',
        'Stanford, KY'
    ]
    
    created_count = 0
    
    for city_name in kentucky_cities:
        # Check if city exists without geometry
        city = CoverageArea.objects.filter(
            name=city_name,
            kind='CITY',
            geom__isnull=True
        ).first()
        
        if city:
            # Create a simple polygon geometry for the city
            # These are approximate coordinates for Kentucky cities
            city_coords = {
                'London, KY': (-84.0833, 37.1289),
                'Corbin, KY': (-84.0969, 36.9487),
                'Somerset, KY': (-84.6041, 37.0920),
                'Livingston, KY': (-84.2166, 37.2981),
                'Martin, KY': (-82.7515, 37.5709),
                'Berea, KY': (-84.2944, 37.5687),
                'Manchester, KY': (-83.7619, 37.1537),
                'Monticello, KY': (-84.8502, 36.8298),
                'Nicholasville, KY': (-84.5730, 37.8806),
                'Stanford, KY': (-84.6619, 37.5279)
            }
            
            if city_name in city_coords:
                lon, lat = city_coords[city_name]
                
                # Create a simple polygon around the city center (small square)
                from django.contrib.gis.geos import Polygon, MultiPolygon
                # Create a small square around the city center (0.01 degree radius)
                radius = 0.01
                city_polygon = Polygon([
                    (lon - radius, lat - radius),
                    (lon + radius, lat - radius),
                    (lon + radius, lat + radius),
                    (lon - radius, lat + radius),
                    (lon - radius, lat - radius)
                ])
                
                # Create MultiPolygon
                multi_polygon = MultiPolygon([city_polygon])
                
                # Update the city with geometry and FIPS codes
                city.geom = multi_polygon
                city.ext_ids = {'state_fips': '21'}  # Kentucky FIPS code
                city.updated_by = user
                city.save()
                
                print(f"✅ Created geometry for {city_name}: Polygon around ({lon}, {lat}) with FIPS codes")
                created_count += 1
    
    print(f"📊 Created geometry for {created_count} cities")
    return created_count


def create_geometry_for_other_states():
    """Create geometry for other states that are missing it."""
    print("🏗️ Creating Geometry for Other States...")
    
    # Get a user for audit trail
    user = User.objects.first()
    if not user:
        print("❌ No user found for audit trail")
        return 0
    
    # States that need geometry (these are approximate center points)
    state_coords = {
        'Alabama': (-86.7911, 32.8067),
        'Georgia': (-83.6431, 33.0406),
        'Maryland': (-76.6413, 39.0639),
        'Mississippi': (-89.6785, 32.7416),
        'New York': (-74.2179, 42.1657),
        'North Carolina': (-79.0193, 35.6301),
        'Ohio': (-82.7937, 40.3888),
        'Pennsylvania': (-77.2098, 40.5908),
        'South Carolina': (-80.9450, 33.8569),
        'Tennessee': (-86.3504, 35.7478),
        'Virginia': (-78.1697, 37.4316),
        'West Virginia': (-80.9545, 38.5976)
    }
    
    # State FIPS codes
    state_fips = {
        'Alabama': '01',
        'Georgia': '13',
        'Maryland': '24',
        'Mississippi': '28',
        'New York': '36',
        'North Carolina': '37',
        'Ohio': '39',
        'Pennsylvania': '42',
        'South Carolina': '45',
        'Tennessee': '47',
        'Virginia': '51',
        'West Virginia': '54'
    }
    
    created_count = 0
    
    for state_name, coords in state_coords.items():
        # Check if state exists without geometry
        state = CoverageArea.objects.filter(
            name=state_name,
            kind='COUNTY',  # These are actually counties named after states
            geom__isnull=True
        ).first()
        
        if state:
            lon, lat = coords
            
            # Create a simple polygon around the state center
            from django.contrib.gis.geos import Polygon, MultiPolygon
            # Create a larger square around the state center (0.1 degree radius)
            radius = 0.1
            state_polygon = Polygon([
                (lon - radius, lat - radius),
                (lon + radius, lat - radius),
                (lon + radius, lat + radius),
                (lon - radius, lat + radius),
                (lon - radius, lat - radius)
            ])
            
            # Create MultiPolygon
            multi_polygon = MultiPolygon([state_polygon])
            
            # Update the state with geometry and FIPS codes
            state.geom = multi_polygon
            if state_name in state_fips:
                state.ext_ids = {
                    'state_fips': state_fips[state_name],
                    'county_fips': '000'  # Placeholder county FIPS
                }
            state.updated_by = user
            state.save()
            
            print(f"✅ Created geometry for {state_name}: Polygon around ({lon}, {lat}) with FIPS codes")
            created_count += 1
    
    print(f"📊 Created geometry for {created_count} states")
    return created_count


def create_geometry_for_united_states():
    """Create geometry for United States coverage area."""
    print("🏗️ Creating Geometry for United States...")
    
    # Get a user for audit trail
    user = User.objects.first()
    if not user:
        print("❌ No user found for audit trail")
        return 0
    
    # Find United States coverage area
    us_area = CoverageArea.objects.filter(
        name='United States (All States and Territories)',
        kind='STATE',
        geom__isnull=True
    ).first()
    
    if us_area:
        # Create a simple polygon covering the continental US
        from django.contrib.gis.geos import Polygon, MultiPolygon
        # Approximate bounding box of continental US
        us_polygon = Polygon([
            (-125.0, 25.0),  # Southwest
            (-125.0, 49.0),  # Northwest  
            (-66.0, 49.0),   # Northeast
            (-66.0, 25.0),   # Southeast
            (-125.0, 25.0)   # Close the polygon
        ])
        
        # Create MultiPolygon
        multi_polygon = MultiPolygon([us_polygon])
        
        # Update the US area with geometry and FIPS codes
        us_area.geom = multi_polygon
        us_area.ext_ids = {'state_fips': '00'}  # Special FIPS code for United States
        us_area.updated_by = user
        us_area.save()
        
        print(f"✅ Created geometry for United States: Polygon covering continental US with FIPS codes")
        return 1
    
    return 0


def verify_final_status():
    """Verify the final status after all fixes."""
    print("\n🔍 Verifying Final Status...")
    
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
    """Main function to run the final geometry fix."""
    print("🚀 Starting Final Geometry Fix...")
    print("=" * 50)
    
    # Step 1: Analyze remaining issues
    issues = analyze_remaining_issues()
    
    if not issues:
        print("✅ All resource-coverage relationships already have geometry!")
        return
    
    # Step 2: Create geometry for cities
    cities_created = create_geometry_for_cities()
    
    # Step 3: Create geometry for other states
    states_created = create_geometry_for_other_states()
    
    # Step 4: Create geometry for United States
    us_created = create_geometry_for_united_states()
    
    # Step 5: Verify final status
    verify_final_status()
    
    print(f"\n📊 Summary:")
    print(f"  Cities with geometry created: {cities_created}")
    print(f"  States with geometry created: {states_created}")
    print(f"  US with geometry created: {us_created}")
    
    print("\n🎯 Final Geometry Fix Complete!")


if __name__ == "__main__":
    main()
