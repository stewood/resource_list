"""
Static Resources - Read-only Data Resources

This module provides static MCP resources for read-only data access,
including categories and service types that don't change frequently.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, List
from directory.models import TaxonomyCategory, ServiceType, Resource
from django.db.models import Count


def get_categories_resource() -> Dict[str, Any]:
    """Get all taxonomy categories as a static resource.
    
    This function provides read-only access to all taxonomy categories in the system
    with their resource counts. This data is cached and updated when the resource
    is accessed, making it efficient for frequent lookups.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - categories (list): List of all categories with id, name, slug,
                                   description, resource_count, created_at
                - total_count (int): Total number of categories
                - last_updated (str): ISO timestamp of last update
    """
    try:
        categories = TaxonomyCategory.objects.annotate(
            resource_count=Count('resources')
        ).order_by('name')
        
        categories_data = []
        for category in categories:
            categories_data.append({
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "resource_count": category.resource_count,
                "created_at": category.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "data": {
                "categories": categories_data,
                "total_count": len(categories_data),
                "last_updated": categories.first().created_at.isoformat() if categories.exists() else None
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving categories: {str(e)}",
            "data": None
        }


def get_service_types_resource() -> Dict[str, Any]:
    """Get all service types as a static resource.
    
    This function provides read-only access to all service types in the system
    with their resource counts. This data is cached and updated when the resource
    is accessed, making it efficient for frequent lookups.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - service_types (list): List of all service types with id, name, slug,
                                      description, resource_count, created_at
                - total_count (int): Total number of service types
                - last_updated (str): ISO timestamp of last update
    """
    try:
        service_types = ServiceType.objects.annotate(
            resource_count=Count('resources')
        ).order_by('name')
        
        service_types_data = []
        for service_type in service_types:
            service_types_data.append({
                "id": service_type.id,
                "name": service_type.name,
                "slug": service_type.slug,
                "description": service_type.description,
                "resource_count": service_type.resource_count,
                "created_at": service_type.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "data": {
                "service_types": service_types_data,
                "total_count": len(service_types_data),
                "last_updated": service_types.first().created_at.isoformat() if service_types.exists() else None
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving service types: {str(e)}",
            "data": None
        }


def get_taxonomy_overview_resource() -> Dict[str, Any]:
    """Get taxonomy overview as a static resource.
    
    This function provides a comprehensive overview of the entire taxonomy system
    including summary statistics and top categories and service types by resource count.
    This data is cached and updated when the resource is accessed.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - summary (dict): Overall statistics including total_categories,
                                total_service_types, total_published_resources
                - top_categories (list): Top 10 categories by resource count
                - top_service_types (list): Top 10 service types by resource count
    """
    try:
        # Get counts
        total_categories = TaxonomyCategory.objects.count()
        total_service_types = ServiceType.objects.count()
        total_resources = Resource.objects.filter(status="published").count()
        
        # Get top categories
        top_categories = TaxonomyCategory.objects.annotate(
            resource_count=Count('resources')
        ).filter(resource_count__gt=0).order_by('-resource_count')[:10]
        
        top_categories_data = [
            {
                "id": cat.id,
                "name": cat.name,
                "resource_count": cat.resource_count
            }
            for cat in top_categories
        ]
        
        # Get top service types
        top_service_types = ServiceType.objects.annotate(
            resource_count=Count('resources')
        ).filter(resource_count__gt=0).order_by('-resource_count')[:10]
        
        top_service_types_data = [
            {
                "id": st.id,
                "name": st.name,
                "resource_count": st.resource_count
            }
            for st in top_service_types
        ]
        
        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_categories": total_categories,
                    "total_service_types": total_service_types,
                    "total_published_resources": total_resources
                },
                "top_categories": top_categories_data,
                "top_service_types": top_service_types_data
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving taxonomy overview: {str(e)}",
            "data": None
        }
