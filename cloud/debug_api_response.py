#!/usr/bin/env python3
"""
Debug API Response Script

This script tests the API response logic to see why bounds are not being included
in the staging API response.
"""

import os
import sys
import django

def debug_api_response():
    """Debug the API response logic."""
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    from django.conf import settings
    
    print("🔍 Debugging API Response Logic...")
    
    # Test with resource 321
    try:
        resource = Resource.objects.get(id=321)
        print(f"✅ Found resource: {resource.name}")
        
        # Check settings
        print(f"📊 Settings check:")
        print(f"  - GIS_ENABLED: {getattr(settings, 'GIS_ENABLED', 'Not set')}")
        print(f"  - Has GIS_ENABLED: {hasattr(settings, 'GIS_ENABLED')}")
        
        # Test coverage areas
        coverage_areas = resource.coverage_areas.all()
        print(f"📊 Found {coverage_areas.count()} coverage areas")
        
        for ca in coverage_areas:
            print(f"\n🔍 Testing coverage area: {ca.name} (ID: {ca.id})")
            print(f"  - Has geom: {ca.geom is not None}")
            print(f"  - Geom type: {ca.geom.geom_type if ca.geom else 'None'}")
            
            if ca.geom:
                try:
                    bounds = ca.geom.extent
                    print(f"  - Extent: {bounds}")
                    print(f"  - Bounds dict: {{'west': {bounds[0]}, 'south': {bounds[1]}, 'east': {bounds[2]}, 'north': {bounds[3]}}}")
                except Exception as e:
                    print(f"  - ❌ Error getting extent: {e}")
            
            # Test the association
            try:
                association = ResourceCoverage.objects.get(
                    resource=resource,
                    coverage_area=ca
                )
                print(f"  - ✅ Association found")
                
                # Test the exact logic from the API view
                area_data = {
                    'id': ca.id,
                    'name': ca.name,
                    'kind': ca.kind,
                    'ext_ids': ca.ext_ids or {},
                    'attached_at': association.created_at.isoformat(),
                    'attached_by': association.created_by.username,
                    'notes': association.notes or ''
                }
                
                print(f"  - Base area_data: {area_data}")
                
                # Test the bounds logic
                if ca.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                    print(f"  - ✅ All conditions met for bounds")
                    try:
                        bounds = ca.geom.extent
                        area_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                        print(f"  - ✅ Bounds added: {area_data['bounds']}")
                    except Exception as e:
                        print(f"  - ❌ Error adding bounds: {e}")
                else:
                    print(f"  - ❌ Conditions not met for bounds:")
                    print(f"    - ca.geom: {ca.geom is not None}")
                    print(f"    - hasattr(settings, 'GIS_ENABLED'): {hasattr(settings, 'GIS_ENABLED')}")
                    print(f"    - settings.GIS_ENABLED: {getattr(settings, 'GIS_ENABLED', 'Not set')}")
                
            except ResourceCoverage.DoesNotExist:
                print(f"  - ❌ Association not found")
            except Exception as e:
                print(f"  - ❌ Error with association: {e}")
        
    except Resource.DoesNotExist:
        print("❌ Resource 321 not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api_response()
