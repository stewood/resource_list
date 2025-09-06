"""
Search Tools - Advanced Search and Discovery

This module provides MCP tools for searching and discovering resources
in the Community Resource Directory using the existing FTS5 full-text
search capabilities and advanced filtering options.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional
from asgiref.sync import sync_to_async
from directory.models import Resource, TaxonomyCategory, ServiceType


async def search_resources(
    query: str,
    search_type: str = "combined",
    category_id: Optional[int] = None,
    service_type_id: Optional[int] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    is_emergency_service: Optional[bool] = None,
    is_24_hour_service: Optional[bool] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Search resources using advanced search capabilities with FTS5 integration.
    
    This function provides powerful search functionality using full-text search (FTS5)
    combined with exact matching and additional filtering options. It's ideal
    for finding resources based on content, location, and service characteristics.
    
    Args:
        query (str): The search query string. This is searched across resource
                    names, descriptions, and other text fields.
        search_type (str): Type of search to perform. Valid values:
                          - "fts": Full-text search using FTS5 (fastest, most flexible)
                          - "exact": Exact string matching (precise but limited)
                          - "combined": Both FTS and exact matching (comprehensive)
                          Defaults to "combined".
        category_id (Optional[int]): Filter results by taxonomy category ID.
        service_type_id (Optional[int]): Filter results by service type ID.
        city (Optional[str]): Filter by city name (case-insensitive partial match).
        state (Optional[str]): Filter by state abbreviation (exact match).
        county (Optional[str]): Filter by county name (case-insensitive partial match).
        is_emergency_service (Optional[bool]): Filter by emergency service flag.
        is_24_hour_service (Optional[bool]): Filter by 24-hour service flag.
        status (Optional[str]): Filter by resource status ("draft", "needs_review", "published").
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - query (str): The search query used
                - search_type (str): The search type used
                - results (list): List of matching resources with summary information
                - pagination (dict): Pagination information
                - filters_applied (dict): Summary of all filters that were applied
              None if error
    """
    try:
        # Validate search type
        valid_search_types = ["fts", "exact", "combined"]
        if search_type not in valid_search_types:
            return {
                "status": "error",
                "message": f"Invalid search_type '{search_type}'. Must be one of: {valid_search_types}",
                "data": None
            }
        
        # Start with base queryset
        queryset = Resource.objects.all()
        
        # Apply search based on type
        if search_type == "fts":
            # Use FTS5 full-text search
            results = await sync_to_async(Resource.objects.search_fts)(query)
        elif search_type == "exact":
            # Use exact match search
            results = await sync_to_async(Resource.objects.search_exact)(query)
        else:  # combined
            # Use combined search (FTS5 + exact matches)
            results = await sync_to_async(Resource.objects.search_combined)(query)
        
        # Apply additional filters
        if category_id:
            results = await sync_to_async(lambda: results.filter(category_id=category_id))()
        if service_type_id:
            results = await sync_to_async(lambda: results.filter(service_types__id=service_type_id))()
        if city:
            results = await sync_to_async(lambda: results.filter(city__icontains=city))()
        if state:
            results = await sync_to_async(lambda: results.filter(state__iexact=state))()
        if county:
            results = await sync_to_async(lambda: results.filter(county__icontains=county))()
        if is_emergency_service is not None:
            results = await sync_to_async(lambda: results.filter(is_emergency_service=is_emergency_service))()
        if is_24_hour_service is not None:
            results = await sync_to_async(lambda: results.filter(is_24_hour_service=is_24_hour_service))()
        if status:
            results = await sync_to_async(lambda: results.filter(status=status))()
        
        # Get total count
        total_count = await sync_to_async(results.count)()
        
        # Apply pagination
        limit = min(limit, 100)  # Cap at 100
        resources = await sync_to_async(list)(
            await sync_to_async(lambda: results.select_related('category').prefetch_related('service_types')[offset:offset + limit])()
        )
        
        # Format results
        resource_list = []
        for resource in resources:
            resource_list.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                "status": resource.status,
                "category": resource.category.name if resource.category else None,
                "service_types": [st.name for st in await sync_to_async(list)(resource.service_types.all())],
                "location": {
                    "city": resource.city,
                    "state": resource.state,
                    "county": resource.county
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
                "created_at": resource.created_at.isoformat(),
                "updated_at": resource.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "message": f"Found {len(resource_list)} resources matching '{query}'",
            "data": {
                "query": query,
                "search_type": search_type,
                "results": resource_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "filters_applied": {
                    "category_id": category_id,
                    "service_type_id": service_type_id,
                    "city": city,
                    "state": state,
                    "county": county,
                    "is_emergency_service": is_emergency_service,
                    "is_24_hour_service": is_24_hour_service,
                    "status": status
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching resources: {str(e)}",
            "data": None
        }


async def search_emergency_services(
    city: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Search for emergency and crisis services by location.
    
    This specialized function finds emergency and crisis services that are marked
    as emergency services and are published. It's designed for urgent situations
    where immediate access to crisis resources is needed.
    
    Args:
        city (Optional[str]): Filter by city name (case-insensitive partial match).
        state (Optional[str]): Filter by state abbreviation (exact match, e.g., "KY").
        county (Optional[str]): Filter by county name (case-insensitive partial match).
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - emergency_services (list): List of emergency services with
                                           detailed operational information
                - total_count (int): Total number of emergency services found
                - location_filter (dict): Summary of location filters applied
              None if error
    """
    try:
        # Search for emergency services
        results = await sync_to_async(lambda: Resource.objects.filter(
            is_emergency_service=True,
            status="published"
        ))()
        
        # Apply location filters
        if city:
            results = await sync_to_async(lambda: results.filter(city__icontains=city))()
        if state:
            results = await sync_to_async(lambda: results.filter(state__iexact=state))()
        if county:
            results = await sync_to_async(lambda: results.filter(county__icontains=county))()
        
        # Get total count
        total_count = await sync_to_async(results.count)()
        
        # Apply limit
        limit = min(limit, 100)  # Cap at 100
        resources = await sync_to_async(list)(
            results.select_related('category').prefetch_related('service_types')[:limit]
        )
        
        # Format results
        resource_list = []
        for resource in resources:
            resource_list.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                "category": resource.category.name if resource.category else None,
                "service_types": [st.name for st in await sync_to_async(list)(resource.service_types.all())],
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
                    "is_24_hour_service": resource.is_24_hour_service,
                    "hours_of_operation": resource.hours_of_operation,
                    "eligibility_requirements": resource.eligibility_requirements,
                    "populations_served": resource.populations_served
                }
            })
        
        return {
            "status": "success",
            "message": f"Found {len(resource_list)} emergency services",
            "data": {
                "emergency_services": resource_list,
                "total_count": total_count,
                "location_filter": {
                    "city": city,
                    "state": state,
                    "county": county
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching emergency services: {str(e)}",
            "data": None
        }


async def search_by_location(
    city: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    category_id: Optional[int] = None,
    service_type_id: Optional[int] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Search resources by geographic location with optional service filtering.
    
    This function finds published resources within specific geographic areas and
    optionally filters by service category or type. It's useful for finding
    all available services in a particular location or region.
    
    Args:
        city (Optional[str]): Filter by city name (case-insensitive partial match).
        state (Optional[str]): Filter by state abbreviation (exact match, e.g., "KY").
        county (Optional[str]): Filter by county name (case-insensitive partial match).
        category_id (Optional[int]): Filter by taxonomy category ID.
                                   Use list_categories to get category IDs.
        service_type_id (Optional[int]): Filter by service type ID.
                                       Use list_service_types to get service type IDs.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - resources (list): List of resources in the specified location
                - total_count (int): Total number of resources found
                - location_filter (dict): Summary of location filters applied
                - category_filter (int): Category ID filter applied (if any)
                - service_type_filter (int): Service type ID filter applied (if any)
              None if error
    """
    try:
        # Start with published resources
        results = await sync_to_async(lambda: Resource.objects.filter(status="published"))()
        
        # Apply location filters
        if city:
            results = await sync_to_async(lambda: results.filter(city__icontains=city))()
        if state:
            results = await sync_to_async(lambda: results.filter(state__iexact=state))()
        if county:
            results = await sync_to_async(lambda: results.filter(county__icontains=county))()
        
        # Apply category and service type filters
        if category_id:
            results = await sync_to_async(lambda: results.filter(category_id=category_id))()
        if service_type_id:
            results = await sync_to_async(lambda: results.filter(service_types__id=service_type_id))()
        
        # Get total count
        total_count = await sync_to_async(results.count)()
        
        # Apply limit
        limit = min(limit, 100)  # Cap at 100
        resources = await sync_to_async(list)(
            results.select_related('category').prefetch_related('service_types')[:limit]
        )
        
        # Format results
        resource_list = []
        for resource in resources:
            resource_list.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                "category": resource.category.name if resource.category else None,
                "service_types": [st.name for st in await sync_to_async(list)(resource.service_types.all())],
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
            "message": f"Found {len(resource_list)} resources in specified location",
            "data": {
                "resources": resource_list,
                "total_count": total_count,
                "location_filter": {
                    "city": city,
                    "state": state,
                    "county": county
                },
                "category_filter": category_id,
                "service_type_filter": service_type_id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching by location: {str(e)}",
            "data": None
        }
