"""
GIS Tools - Geographic and Spatial Service Area Management

This module provides MCP tools for managing geographic service areas and
spatial queries in the Community Resource Directory. It handles coverage
areas (cities, counties, states, nationwide, radius) and resource coverage
assignments for the London, KY based application.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional
from asgiref.sync import sync_to_async
from directory.models import Resource, CoverageArea, ResourceCoverage


async def list_coverage_areas(
    kind: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List coverage areas with optional filtering.
    
    This function retrieves geographic coverage areas that define service territories
    for resources. Coverage areas can be cities, counties, states, custom polygons,
    or radius-based areas around specific points.
    
    Args:
        kind (Optional[str]): Filter by coverage area type. Valid values:
                            - "CITY": City-level coverage areas
                            - "COUNTY": County-level coverage areas
                            - "STATE": State-level coverage areas
                            - "RADIUS": Radius-based coverage areas
                            - "POLYGON": Custom polygon coverage areas
        state (Optional[str]): Filter by state for administrative areas (cities/counties).
                             Use two-letter state abbreviation (e.g., "KY").
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - coverage_areas (list): List of coverage area objects with id, kind,
                                       name, display_name, fips_codes, and geometry info
                - pagination (dict): Pagination information
                - filters_applied (dict): Summary of filters applied
              None if error
    """
    try:
        # Start with base queryset
        queryset = CoverageArea.objects.all().order_by('kind', 'name')
        
        # Apply filters
        if kind:
            queryset = queryset.filter(kind=kind)
        if state:
            # Filter by state in external IDs for administrative areas
            queryset = queryset.filter(ext_ids__state_fips=state)
        
        # Get total count
        total_count = await sync_to_async(queryset.count)()
        
        # Apply pagination
        limit = min(limit, 100)  # Cap at 100
        areas = await sync_to_async(list)(
            queryset[offset:offset + limit]
        )
        
        # Format results
        area_list = []
        for area in areas:
            area_data = {
                "id": area.id,
                "kind": area.kind,
                "name": area.name,
                "display_name": area.display_name,
                "fips_codes": area.fips_codes,
                "is_administrative": area.is_administrative,
                "is_custom": area.is_custom,
                "created_at": area.created_at.isoformat()
            }
            
            # Add kind-specific data
            if area.kind == "RADIUS":
                area_data["radius_miles"] = area.get_radius_miles()
                area_data["center_coordinates"] = area.get_center_coordinates()
            elif area.kind in ["CITY", "COUNTY", "STATE"]:
                area_data["fips_codes"] = area.fips_codes
            
            # Add geometry info if available
            if hasattr(area, 'geom') and area.geom:
                area_data["bounds"] = area.get_bounds()
                area_data["area_sq_miles"] = area.get_area_sq_miles()
            
            area_list.append(area_data)
        
        return {
            "status": "success",
            "message": f"Retrieved {len(area_list)} coverage areas",
            "data": {
                "coverage_areas": area_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "filters_applied": {
                    "kind": kind,
                    "state": state
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing coverage areas: {str(e)}",
            "data": None
        }


async def get_coverage_area(coverage_area_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific coverage area.
    
    This function retrieves comprehensive information about a single coverage area
    including its geographic boundaries, resource count, and type-specific
    information such as radius for radius-based areas or FIPS codes for
    administrative areas.
    
    Args:
        coverage_area_id (int): The unique identifier of the coverage area to retrieve.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains coverage area information including:
                - id (int): Coverage area ID
                - kind (str): Type of coverage area (CITY, COUNTY, STATE, RADIUS, POLYGON)
                - name (str): Coverage area name
                - display_name (str): Human-readable display name
                - fips_codes (dict): FIPS codes for administrative areas
                - is_administrative (bool): Whether this is an administrative area
                - is_custom (bool): Whether this is a custom-defined area
                - resource_count (int): Number of resources covering this area
                - created_at (str): ISO timestamp of creation
                - updated_at (str): ISO timestamp of last update
                - radius_miles (float, optional): Radius in miles for RADIUS type areas
                - center_coordinates (dict, optional): Center point for RADIUS type areas
                - bounds (dict, optional): Geographic bounds if geometry available
                - area_sq_miles (float, optional): Area in square miles if geometry available
                - perimeter_miles (float, optional): Perimeter in miles if geometry available
              None if error
    
    Raises:
        DoesNotExist: If coverage_area_id does not exist
    """
    try:
        area = await sync_to_async(CoverageArea.objects.get)(id=coverage_area_id)
        
        # Get resource count for this area
        resource_count = await sync_to_async(
            ResourceCoverage.objects.filter(coverage_area=area).count
        )()
        
        area_data = {
            "id": area.id,
            "kind": area.kind,
            "name": area.name,
            "display_name": area.display_name,
            "fips_codes": area.fips_codes,
            "is_administrative": area.is_administrative,
            "is_custom": area.is_custom,
            "resource_count": resource_count,
            "created_at": area.created_at.isoformat(),
            "updated_at": area.updated_at.isoformat()
        }
        
        # Add kind-specific data
        if area.kind == "RADIUS":
            area_data["radius_miles"] = area.get_radius_miles()
            area_data["center_coordinates"] = area.get_center_coordinates()
        elif area.kind in ["CITY", "COUNTY", "STATE"]:
            area_data["fips_codes"] = area.fips_codes
        
        # Add geometry info if available
        if hasattr(area, 'geom') and area.geom:
            area_data["bounds"] = area.get_bounds()
            area_data["area_sq_miles"] = area.get_area_sq_miles()
            area_data["perimeter_miles"] = area.get_perimeter_miles()
        
        return {
            "status": "success",
            "message": f"Retrieved coverage area '{area.name}'",
            "data": area_data
        }
        
    except CoverageArea.DoesNotExist:
        return {
            "status": "error",
            "message": f"Coverage area with ID {coverage_area_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving coverage area: {str(e)}",
            "data": None
        }


async def search_resources_by_coverage_area(
    coverage_area_id: int,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Search for resources that cover a specific geographic area.
    
    This function finds all resources that have been assigned to cover a specific
    coverage area. This is useful for finding all services available in a
    particular geographic region.
    
    Args:
        coverage_area_id (int): The unique identifier of the coverage area to search within.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - coverage_area (dict): Information about the coverage area searched
                - resources (list): List of resources covering this area with
                                 coverage assignment details
                - pagination (dict): Pagination information
              None if error
    
    Raises:
        DoesNotExist: If coverage_area_id does not exist
    """
    try:
        # Get the coverage area
        coverage_area = await sync_to_async(CoverageArea.objects.get)(id=coverage_area_id)
        
        # Find resources that cover this area
        def get_resource_coverages():
            return ResourceCoverage.objects.filter(
                coverage_area=coverage_area
            ).select_related('resource', 'resource__category').prefetch_related('resource__service_types')
        
        resource_coverages = await sync_to_async(get_resource_coverages)()
        
        # Get total count
        total_count = await sync_to_async(resource_coverages.count)()
        
        # Apply pagination
        limit = min(limit, 100)  # Cap at 100
        coverages = await sync_to_async(list)(
            resource_coverages[offset:offset + limit]
        )
        
        # Format results
        resource_list = []
        for coverage in coverages:
            resource = coverage.resource
            # Get service types synchronously since we're already in an async context
            service_types = list(resource.service_types.all())
            resource_list.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                "status": resource.status,
                "category": resource.category.name if resource.category else None,
                "service_types": [st.name for st in service_types],
                "location": {
                    "city": resource.city,
                    "state": resource.state,
                    "county": resource.county,
                    "address1": resource.address1,
                    "postal_code": resource.postal_code
                },
                "contact": {
                    "phone": resource.phone,
                    "email": resource.email,
                    "website": resource.website
                },
                "operational": {
                    "is_emergency_service": resource.is_emergency_service,
                    "is_24_hour_service": resource.is_24_hour_service,
                    "hours_of_operation": resource.hours_of_operation
                },
                "coverage_assignment": {
                    "coverage_area_id": coverage.coverage_area.id,
                    "coverage_area_name": coverage.coverage_area.name,
                    "coverage_area_kind": coverage.coverage_area.kind,
                    "assigned_at": coverage.created_at.isoformat()
                },
                "created_at": resource.created_at.isoformat(),
                "updated_at": resource.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "message": f"Found {len(resource_list)} resources covering '{coverage_area.name}'",
            "data": {
                "coverage_area": {
                    "id": coverage_area.id,
                    "name": coverage_area.name,
                    "kind": coverage_area.kind,
                    "display_name": coverage_area.display_name
                },
                "resources": resource_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except CoverageArea.DoesNotExist:
        return {
            "status": "error",
            "message": f"Coverage area with ID {coverage_area_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching resources by coverage area: {str(e)}",
            "data": None
        }


async def assign_coverage_area_to_resource(
    resource_id: int,
    coverage_area_id: int,
    assigned_by_user_id: int = 1
) -> Dict[str, Any]:
    """Assign a coverage area to a resource.
    
    This function creates a relationship between a resource and a coverage area,
    indicating that the resource provides services within that geographic area.
    Resources can be assigned to multiple coverage areas.
    
    Args:
        resource_id (int): The unique identifier of the resource to assign.
        coverage_area_id (int): The unique identifier of the coverage area to assign.
        assigned_by_user_id (int): ID of the user making the assignment. Defaults to 1.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains assignment details including:
                - assignment_id (int): ID of the created assignment
                - resource (dict): Resource information (id, name)
                - coverage_area (dict): Coverage area information (id, name, kind, display_name)
                - assigned_at (str): ISO timestamp of assignment
              None if error
    
    Raises:
        DoesNotExist: If resource_id or coverage_area_id does not exist
        ValidationError: If assignment already exists
    """
    try:
        # Get the resource and coverage area
        resource = await sync_to_async(Resource.objects.get)(id=resource_id)
        coverage_area = await sync_to_async(CoverageArea.objects.get)(id=coverage_area_id)
        
        # Check if assignment already exists
        existing_assignment = await sync_to_async(
            ResourceCoverage.objects.filter(
                resource=resource,
                coverage_area=coverage_area
            ).exists
        )()
        
        if existing_assignment:
            return {
                "status": "error",
                "message": f"Resource '{resource.name}' already covers '{coverage_area.name}'",
                "data": None
            }
        
        # Create the assignment
        from django.contrib.auth.models import User
        try:
            user = await sync_to_async(User.objects.get)(id=assigned_by_user_id)
        except User.DoesNotExist:
            user = await sync_to_async(User.objects.first)()  # Fallback to first user
        
        assignment = await sync_to_async(ResourceCoverage.objects.create)(
            resource=resource,
            coverage_area=coverage_area,
            created_by=user
        )
        
        return {
            "status": "success",
            "message": f"Successfully assigned '{coverage_area.name}' to '{resource.name}'",
            "data": {
                "assignment_id": assignment.id,
                "resource": {
                    "id": resource.id,
                    "name": resource.name
                },
                "coverage_area": {
                    "id": coverage_area.id,
                    "name": coverage_area.name,
                    "kind": coverage_area.kind,
                    "display_name": coverage_area.display_name
                },
                "assigned_at": assignment.created_at.isoformat()
            }
        }
        
    except Resource.DoesNotExist:
        return {
            "status": "error",
            "message": f"Resource with ID {resource_id} not found",
            "data": None
        }
    except CoverageArea.DoesNotExist:
        return {
            "status": "error",
            "message": f"Coverage area with ID {coverage_area_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error assigning coverage area: {str(e)}",
            "data": None
        }


async def remove_coverage_area_from_resource(
    resource_id: int,
    coverage_area_id: int,
    removed_by_user_id: int = 1
) -> Dict[str, Any]:
    """Remove a coverage area assignment from a resource.
    
    This function removes the relationship between a resource and a coverage area,
    indicating that the resource no longer provides services within that
    geographic area.
    
    Args:
        resource_id (int): The unique identifier of the resource.
        coverage_area_id (int): The unique identifier of the coverage area to remove.
        removed_by_user_id (int): ID of the user making the removal. Defaults to 1.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains removal confirmation including:
                - resource (dict): Resource information (id, name)
                - coverage_area (dict): Coverage area information (id, name, kind, display_name)
                - removed_at (str): ISO timestamp of removal
              None if error
    
    Raises:
        DoesNotExist: If resource_id, coverage_area_id, or assignment does not exist
    """
    try:
        # Get the resource and coverage area
        resource = await sync_to_async(Resource.objects.get)(id=resource_id)
        coverage_area = await sync_to_async(CoverageArea.objects.get)(id=coverage_area_id)
        
        # Find and delete the assignment
        assignment = await sync_to_async(
            ResourceCoverage.objects.get
        )(resource=resource, coverage_area=coverage_area)
        
        await sync_to_async(assignment.delete)()
        
        return {
            "status": "success",
            "message": f"Successfully removed '{coverage_area.name}' from '{resource.name}'",
            "data": {
                "resource": {
                    "id": resource.id,
                    "name": resource.name
                },
                "coverage_area": {
                    "id": coverage_area.id,
                    "name": coverage_area.name,
                    "kind": coverage_area.kind,
                    "display_name": coverage_area.display_name
                },
                "removed_at": assignment.created_at.isoformat()
            }
        }
        
    except Resource.DoesNotExist:
        return {
            "status": "error",
            "message": f"Resource with ID {resource_id} not found",
            "data": None
        }
    except CoverageArea.DoesNotExist:
        return {
            "status": "error",
            "message": f"Coverage area with ID {coverage_area_id} not found",
            "data": None
        }
    except ResourceCoverage.DoesNotExist:
        return {
            "status": "error",
            "message": f"Resource '{resource.name}' does not cover '{coverage_area.name}'",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error removing coverage area: {str(e)}",
            "data": None
        }


async def get_resource_coverage_areas(resource_id: int) -> Dict[str, Any]:
    """Get all coverage areas assigned to a resource.
    
    This function retrieves all coverage areas that have been assigned to a specific
    resource, showing the complete geographic service area for that resource.
    
    Args:
        resource_id (int): The unique identifier of the resource.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - resource (dict): Resource information (id, name)
                - coverage_areas (list): List of coverage areas assigned to this resource
                                       with assignment timestamps
                - total_count (int): Total number of coverage areas assigned
              None if error
    
    Raises:
        DoesNotExist: If resource_id does not exist
    """
    try:
        # Get the resource
        resource = await sync_to_async(Resource.objects.get)(id=resource_id)
        
        # Get all coverage area assignments
        assignments = ResourceCoverage.objects.filter(
            resource=resource
        ).select_related('coverage_area')
        
        assignments_list = await sync_to_async(list)(assignments)
        
        # Format results
        coverage_areas = []
        for assignment in assignments_list:
            area = assignment.coverage_area
            coverage_areas.append({
                "id": area.id,
                "kind": area.kind,
                "name": area.name,
                "display_name": area.display_name,
                "fips_codes": area.fips_codes,
                "is_administrative": area.is_administrative,
                "is_custom": area.is_custom,
                "assigned_at": assignment.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "message": f"Retrieved {len(coverage_areas)} coverage areas for '{resource.name}'",
            "data": {
                "resource": {
                    "id": resource.id,
                    "name": resource.name
                },
                "coverage_areas": coverage_areas,
                "total_count": len(coverage_areas)
            }
        }
        
    except Resource.DoesNotExist:
        return {
            "status": "error",
            "message": f"Resource with ID {resource_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving resource coverage areas: {str(e)}",
            "data": None
        }


async def search_resources_by_point(
    latitude: float,
    longitude: float,
    radius_miles: float = 25.0,
    limit: int = 50
) -> Dict[str, Any]:
    """Search for resources within a radius of a specific geographic point.
    
    This function performs spatial search to find resources within a specified radius
    of a geographic coordinate. It searches through radius-based coverage areas
    and administrative areas to find all resources that serve the specified location.
    
    Args:
        latitude (float): Latitude of the search point in decimal degrees.
                         Valid range: -90.0 to 90.0
        longitude (float): Longitude of the search point in decimal degrees.
                          Valid range: -180.0 to 180.0
        radius_miles (float): Search radius in miles. Defaults to 25.0 miles.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - search_point (dict): Search parameters (latitude, longitude, radius_miles)
                - resources (list): List of resources within the search radius
                - total_count (int): Total number of resources found
                - coverage_areas_searched (int): Number of coverage areas searched
              None if error
    
    Note:
        This function uses a simplified distance calculation for radius-based areas.
        For production use with complex geometries, a full GIS implementation
        would be recommended.
    """
    try:
        # Convert miles to meters for database query
        radius_meters = radius_miles * 1609.34
        
        # Find coverage areas that contain or are near this point
        # This includes radius-based areas and administrative areas
        coverage_areas = CoverageArea.objects.all()
        
        # Filter coverage areas that might contain this point
        # For now, we'll get all areas and filter in Python
        # In a full GIS implementation, this would use spatial queries
        all_areas = await sync_to_async(list)(coverage_areas)
        
        relevant_areas = []
        for area in all_areas:
            # Check if point is within radius-based areas
            if area.kind == "RADIUS" and area.center:
                # Calculate distance (simplified - would use proper GIS in production)
                center_lat = area.center.y
                center_lon = area.center.x
                distance = ((latitude - center_lat) ** 2 + (longitude - center_lon) ** 2) ** 0.5
                # Rough conversion: 1 degree ≈ 69 miles
                distance_miles = distance * 69
                if distance_miles <= radius_miles:
                    relevant_areas.append(area)
            # For administrative areas, we'd need proper GIS intersection
            # For now, include all administrative areas as potential matches
            elif area.kind in ["CITY", "COUNTY", "STATE"]:
                relevant_areas.append(area)
        
        # Get resources from relevant coverage areas
        resource_ids = set()
        for area in relevant_areas:
            assignments = ResourceCoverage.objects.filter(coverage_area=area)
            area_resource_ids = await sync_to_async(list)(
                assignments.values_list('resource_id', flat=True)
            )
            resource_ids.update(area_resource_ids)
        
        # Get the actual resources
        if not resource_ids:
            return {
                "status": "success",
                "message": f"No resources found within {radius_miles} miles of the point",
                "data": {
                    "search_point": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius_miles": radius_miles
                    },
                    "resources": [],
                    "total_count": 0
                }
            }
        
        resources = Resource.objects.filter(
            id__in=resource_ids,
            status="published"
        ).select_related('category').prefetch_related('service_types')
        
        # Apply limit
        limit = min(limit, 100)  # Cap at 100
        resources_list = await sync_to_async(list)(resources[:limit])
        
        # Format results
        resource_list = []
        for resource in resources_list:
            resource_list.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                "status": resource.status,
                "category": resource.category.name if resource.category else None,
                "service_types": [st.name for st in list(resource.service_types.all())],
                "location": {
                    "city": resource.city,
                    "state": resource.state,
                    "county": resource.county,
                    "address1": resource.address1,
                    "postal_code": resource.postal_code
                },
                "contact": {
                    "phone": resource.phone,
                    "email": resource.email,
                    "website": resource.website
                },
                "operational": {
                    "is_emergency_service": resource.is_emergency_service,
                    "is_24_hour_service": resource.is_24_hour_service,
                    "hours_of_operation": resource.hours_of_operation
                }
            })
        
        return {
            "status": "success",
            "message": f"Found {len(resource_list)} resources within {radius_miles} miles",
            "data": {
                "search_point": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_miles": radius_miles
                },
                "resources": resource_list,
                "total_count": len(resource_list),
                "coverage_areas_searched": len(relevant_areas)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching resources by point: {str(e)}",
            "data": None
        }
