"""
Taxonomy Tools - Category and Service Type Management

This module provides MCP tools for managing and querying the taxonomy
system of the Community Resource Directory, including categories and
service types with resource count aggregation.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional
from django.db.models import Count
from asgiref.sync import sync_to_async
from directory.models import TaxonomyCategory, ServiceType, Resource


async def list_categories(
    include_resource_count: bool = True,
    published_only: bool = True
) -> Dict[str, Any]:
    """List all taxonomy categories with optional resource counts.
    
    This function retrieves all available taxonomy categories in the system,
    optionally including the count of resources in each category. Categories
    are the top-level classification system for organizing resources.
    
    Args:
        include_resource_count (bool): Whether to include the number of resources
                                     in each category. Defaults to True.
        published_only (bool): Whether to count only published resources when
                             calculating resource counts. Defaults to True.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - categories (list): List of category objects with id, name, slug,
                                   description, created_at, and optionally resource_count
                - total_count (int): Total number of categories
                - include_resource_count (bool): Whether resource counts were included
                - published_only (bool): Whether only published resources were counted
              None if error
    """
    try:
        # Start with base queryset
        categories = TaxonomyCategory.objects.all().order_by('name')
        
        # Add resource count if requested
        if include_resource_count:
            categories = categories.annotate(resource_count=Count('resources'))
        
        # Get categories as list
        categories_list = await sync_to_async(list)(categories)
        
        # Format results
        category_list = []
        for category in categories_list:
            category_data = {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "created_at": category.created_at.isoformat()
            }
            
            if include_resource_count:
                category_data["resource_count"] = getattr(category, 'resource_count', 0)
            
            category_list.append(category_data)
        
        return {
            "status": "success",
            "message": f"Retrieved {len(category_list)} categories",
            "data": {
                "categories": category_list,
                "total_count": len(category_list),
                "include_resource_count": include_resource_count,
                "published_only": published_only
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing categories: {str(e)}",
            "data": None
        }


async def get_category(category_id: int, include_resources: bool = False) -> Dict[str, Any]:
    """Get detailed information about a specific category.
    
    This function retrieves comprehensive information about a single taxonomy
    category, optionally including all resources that belong to that category.
    
    Args:
        category_id (int): The unique identifier of the category to retrieve.
        include_resources (bool): Whether to include a list of all resources
                                in this category. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains category information including:
                - id (int): Category ID
                - name (str): Category name
                - slug (str): URL-friendly category identifier
                - description (str): Category description
                - created_at (str): ISO timestamp of creation
                - resource_count (int): Number of resources in this category
                - resources (list, optional): List of resources in this category
                                            if include_resources is True
              None if error
    
    Raises:
        DoesNotExist: If category_id does not exist
    """
    try:
        category = await sync_to_async(TaxonomyCategory.objects.get)(id=category_id)
        
        category_data = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": category.created_at.isoformat()
        }
        
        # Add resource count
        if include_resources:
            resources = Resource.objects.filter(
                category=category,
                status="published"
            ).select_related('category').prefetch_related('service_types')
            
            resources_list = await sync_to_async(list)(resources)
            resource_list = []
            for resource in resources_list:
                resource_list.append({
                    "id": resource.id,
                    "name": resource.name,
                    "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
                    "status": resource.status,
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
                        "is_24_hour_service": resource.is_24_hour_service
                    }
                })
            
            category_data["resources"] = resource_list
            category_data["resource_count"] = len(resource_list)
        else:
            # Just get the count
            category_data["resource_count"] = await sync_to_async(
                Resource.objects.filter(
                    category=category,
                    status="published"
                ).count
            )()
        
        return {
            "status": "success",
            "message": f"Retrieved category '{category.name}'",
            "data": category_data
        }
        
    except TaxonomyCategory.DoesNotExist:
        return {
            "status": "error",
            "message": f"Category with ID {category_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving category: {str(e)}",
            "data": None
        }


async def list_service_types(
    category_id: Optional[int] = None,
    include_resource_count: bool = True,
    published_only: bool = True
) -> Dict[str, Any]:
    """List service types with optional filtering and resource counts.
    
    This function retrieves service types, which are the specific types of services
    that resources can provide. Service types are more granular than categories
    and can be filtered by category to show only relevant service types.
    
    Args:
        category_id (Optional[int]): Filter service types to only those that
                                   are used by resources in this category.
        include_resource_count (bool): Whether to include the number of resources
                                     that provide each service type. Defaults to True.
        published_only (bool): Whether to count only published resources when
                             calculating resource counts. Defaults to True.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - service_types (list): List of service type objects with id, name,
                                      slug, description, created_at, and optionally
                                      resource_count
                - total_count (int): Total number of service types
                - category_filter (int): Category ID filter applied (if any)
                - include_resource_count (bool): Whether resource counts were included
                - published_only (bool): Whether only published resources were counted
              None if error
    """
    try:
        # Start with base queryset
        service_types = ServiceType.objects.all().order_by('name')
        
        # Filter by category if specified
        if category_id:
            # Get resources in this category and their service types
            category_resources = Resource.objects.filter(
                category_id=category_id,
                status="published" if published_only else None
            )
            category_resources_list = await sync_to_async(list)(category_resources)
            service_type_ids = set()
            for resource in category_resources_list:
                service_type_ids.update(await sync_to_async(list)(resource.service_types.values_list('id', flat=True)))
            service_types = service_types.filter(id__in=service_type_ids)
        
        # Add resource count if requested
        if include_resource_count:
            service_types = service_types.annotate(resource_count=Count('resources'))
        
        # Get service types as list
        service_types_list = await sync_to_async(list)(service_types)
        
        # Format results
        service_type_list = []
        for service_type in service_types_list:
            service_type_data = {
                "id": service_type.id,
                "name": service_type.name,
                "slug": service_type.slug,
                "description": service_type.description,
                "created_at": service_type.created_at.isoformat()
            }
            
            if include_resource_count:
                service_type_data["resource_count"] = getattr(service_type, 'resource_count', 0)
            
            service_type_list.append(service_type_data)
        
        return {
            "status": "success",
            "message": f"Retrieved {len(service_type_list)} service types",
            "data": {
                "service_types": service_type_list,
                "total_count": len(service_type_list),
                "category_filter": category_id,
                "include_resource_count": include_resource_count,
                "published_only": published_only
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing service types: {str(e)}",
            "data": None
        }


async def get_service_type(service_type_id: int, include_resources: bool = False) -> Dict[str, Any]:
    """Get detailed information about a specific service type.
    
    This function retrieves comprehensive information about a single service type,
    optionally including all resources that provide this type of service.
    
    Args:
        service_type_id (int): The unique identifier of the service type to retrieve.
        include_resources (bool): Whether to include a list of all resources
                                that provide this service type. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains service type information including:
                - id (int): Service type ID
                - name (str): Service type name
                - slug (str): URL-friendly service type identifier
                - description (str): Service type description
                - created_at (str): ISO timestamp of creation
                - resource_count (int): Number of resources providing this service type
                - resources (list, optional): List of resources providing this service type
                                            if include_resources is True
              None if error
    
    Raises:
        DoesNotExist: If service_type_id does not exist
    """
    try:
        service_type = await sync_to_async(ServiceType.objects.get)(id=service_type_id)
        
        service_type_data = {
            "id": service_type.id,
            "name": service_type.name,
            "slug": service_type.slug,
            "description": service_type.description,
            "created_at": service_type.created_at.isoformat()
        }
        
        # Add resource count and list if requested
        if include_resources:
            resources = Resource.objects.filter(
                service_types=service_type,
                status="published"
            ).select_related('category').prefetch_related('service_types')
            
            resources_list = await sync_to_async(list)(resources)
            resource_list = []
            for resource in resources_list:
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
                        "is_24_hour_service": resource.is_24_hour_service
                    }
                })
            
            service_type_data["resources"] = resource_list
            service_type_data["resource_count"] = len(resource_list)
        else:
            # Just get the count
            service_type_data["resource_count"] = await sync_to_async(
                Resource.objects.filter(
                    service_types=service_type,
                    status="published"
                ).count
            )()
        
        return {
            "status": "success",
            "message": f"Retrieved service type '{service_type.name}'",
            "data": service_type_data
        }
        
    except ServiceType.DoesNotExist:
        return {
            "status": "error",
            "message": f"Service type with ID {service_type_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving service type: {str(e)}",
            "data": None
        }


async def get_taxonomy_summary() -> Dict[str, Any]:
    """Get a comprehensive summary of the taxonomy system.
    
    This function provides an overview of the entire taxonomy system including
    counts of categories, service types, and resources, plus the top
    categories and service types by resource count.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains taxonomy summary including:
                - categories (dict): Category statistics:
                    - total (int): Total number of categories
                    - with_resources (int): Categories that have resources
                    - top_categories (list): Top 5 categories by resource count
                - service_types (dict): Service type statistics:
                    - total (int): Total number of service types
                    - with_resources (int): Service types that have resources
                    - top_service_types (list): Top 5 service types by resource count
                - resources (dict): Resource statistics:
                    - total (int): Total number of resources
                    - published (int): Number of published resources
                    - draft (int): Number of draft resources
                    - needs_review (int): Number of resources needing review
              None if error
    """
    try:
        # Get category counts
        total_categories = await sync_to_async(TaxonomyCategory.objects.count)()
        categories_with_resources = await sync_to_async(
            TaxonomyCategory.objects.filter(
                resources__isnull=False
            ).distinct().count
        )()
        
        # Get service type counts
        total_service_types = await sync_to_async(ServiceType.objects.count)()
        service_types_with_resources = await sync_to_async(
            ServiceType.objects.filter(
                resources__isnull=False
            ).distinct().count
        )()
        
        # Get resource counts by status
        total_resources = await sync_to_async(Resource.objects.count)()
        published_resources = await sync_to_async(Resource.objects.filter(status="published").count)()
        draft_resources = await sync_to_async(Resource.objects.filter(status="draft").count)()
        needs_review_resources = await sync_to_async(Resource.objects.filter(status="needs_review").count)()
        
        # Get top categories by resource count
        top_categories = TaxonomyCategory.objects.annotate(
            resource_count=Count('resources')
        ).filter(resource_count__gt=0).order_by('-resource_count')[:5]
        
        top_categories_list = [
            {
                "id": cat.id,
                "name": cat.name,
                "resource_count": cat.resource_count
            }
            for cat in await sync_to_async(list)(top_categories)
        ]
        
        # Get top service types by resource count
        top_service_types = ServiceType.objects.annotate(
            resource_count=Count('resources')
        ).filter(resource_count__gt=0).order_by('-resource_count')[:5]
        
        top_service_types_list = [
            {
                "id": st.id,
                "name": st.name,
                "resource_count": st.resource_count
            }
            for st in await sync_to_async(list)(top_service_types)
        ]
        
        return {
            "status": "success",
            "message": "Taxonomy summary retrieved successfully",
            "data": {
                "categories": {
                    "total": total_categories,
                    "with_resources": categories_with_resources,
                    "top_categories": top_categories_list
                },
                "service_types": {
                    "total": total_service_types,
                    "with_resources": service_types_with_resources,
                    "top_service_types": top_service_types_list
                },
                "resources": {
                    "total": total_resources,
                    "published": published_resources,
                    "draft": draft_resources,
                    "needs_review": needs_review_resources
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving taxonomy summary: {str(e)}",
            "data": None
        }
