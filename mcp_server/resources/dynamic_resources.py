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
        
        resource_data = {
            "id": resource.id,
            "name": resource.name,
            "description": resource.description,
            "category": {
                "id": resource.category.id if resource.category else None,
                "name": resource.category.name if resource.category else None
            },
            "service_types": [
                {"id": st.id, "name": st.name}
                for st in resource.service_types.all()
            ],
            "contact": {
                "phone": resource.phone,
                "email": resource.email,
                "website": resource.website
            },
            "location": {
                "address1": resource.address1,
                "address2": resource.address2,
                "city": resource.city,
                "state": resource.state,
                "county": resource.county,
                "postal_code": resource.postal_code
            },
            "operational": {
                "status": resource.status,
                "hours_of_operation": resource.hours_of_operation,
                "is_emergency_service": resource.is_emergency_service,
                "is_24_hour_service": resource.is_24_hour_service,
                "eligibility_requirements": resource.eligibility_requirements,
                "populations_served": resource.populations_served,
                "insurance_accepted": resource.insurance_accepted,
                "cost_information": resource.cost_information,
                "languages_available": resource.languages_available,
                "capacity": resource.capacity
            },
            "metadata": {
                "created_at": resource.created_at.isoformat(),
                "updated_at": resource.updated_at.isoformat(),
                "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                "verification_frequency_days": resource.verification_frequency_days,
                "source": resource.source
            }
        }
        
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
