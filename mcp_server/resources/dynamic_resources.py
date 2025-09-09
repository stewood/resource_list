"""
Dynamic Resources - Dynamic Resource Templates

This module provides dynamic MCP resources for individual resources
and other data that changes frequently or is user-specific.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, Optional
from directory.models import Resource
from mcp_server.utils.helpers import format_resource_data


def get_resource_template(resource_id: int) -> Dict[str, Any]:
    """Get a specific resource as a dynamic resource template.
    
    This function provides real-time access to a specific resource's complete
    information. The data is fetched fresh each time the resource is accessed,
    ensuring it's always up-to-date with the latest changes.
    
    Args:
        resource_id (int): The unique identifier of the resource to retrieve.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Complete resource information including:
                - id (int): Resource ID
                - name (str): Resource name
                - description (str): Full description
                - category (dict): Category information
                - service_types (list): Service types provided
                - contact (dict): Contact information
                - location (dict): Address information
                - operational (dict): Operational details and flags
                - metadata (dict): Creation/update timestamps and verification info
              None if error
    
    Raises:
        DoesNotExist: If resource_id does not exist
    """
    try:
        resource = Resource.objects.select_related('category').prefetch_related('service_types').get(id=resource_id)
        
        # Use shared formatting function
        resource_data = format_resource_data(
            resource=resource,
            include_verified_by=False,  # This version doesn't include verified_by
            include_notes=False
        )
        
        return {
            "status": "success",
            "data": resource_data
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
            "message": f"Error retrieving resource: {str(e)}",
            "data": None
        }
