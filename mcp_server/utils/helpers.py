"""
Helper Utilities - Shared Utilities for MCP Server

This module provides shared utilities and helper functions for the MCP server,
including audit trail integration and common validation functions.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from directory.models import Resource
from directory.models.analytics.audit import AuditLog


def create_audit_log(
    resource: Resource,
    action: str,
    field_name: str,
    old_value: str,
    new_value: str,
    user_id: int,
    notes: str = ""
) -> AuditLog:
    """Create an audit log entry for a resource modification.
    
    This function creates a comprehensive audit log entry that tracks all changes
    made to resources in the system. This is essential for compliance, debugging,
    and maintaining a complete history of resource modifications.
    
    Args:
        resource (Resource): The resource being modified.
        action (str): The action performed. Common values include:
                    "create_resource", "update_resource", "archive_resource"
        field_name (str): The specific field that was modified (e.g., "name", "phone").
        old_value (str): The previous value of the field before modification.
        new_value (str): The new value of the field after modification.
        user_id (int): ID of the user performing the action.
        notes (str): Additional notes about the change. Defaults to empty string.
        
    Returns:
        AuditLog: The created AuditLog instance with all tracking information.
    """
    return AuditLog.objects.create(
        resource=resource,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        user_id=user_id,
        notes=notes
    )


def validate_resource_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate resource data before creation or update.
    
    This function performs comprehensive validation on resource data using Django's
    built-in validators and custom business rules. It ensures data integrity
    and prevents invalid data from being saved to the database.
    
    Args:
        data (Dict[str, Any]): Dictionary containing resource data to validate.
                              Should include fields like name, email, website, state, etc.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - is_valid (bool): True if all validation passes, False otherwise
            - errors (list): List of error messages for any validation failures
    """
    errors = []
    
    # Required fields
    if not data.get('name'):
        errors.append("Name is required")
    
    # Validate status if provided
    if 'status' in data:
        valid_statuses = ['draft', 'needs_review', 'published']
        if data['status'] not in valid_statuses:
            errors.append(f"Status must be one of: {valid_statuses}")
    
    # Validate state if provided
    if 'state' in data and data['state']:
        if len(data['state']) != 2:
            errors.append("State must be a 2-character abbreviation")
    
    # Validate email if provided
    if 'email' in data and data['email']:
        from django.core.validators import validate_email
        try:
            validate_email(data['email'])
        except ValidationError:
            errors.append("Invalid email format")
    
    # Validate website if provided
    if 'website' in data and data['website']:
        from django.core.validators import URLValidator
        try:
            URLValidator()(data['website'])
        except ValidationError:
            errors.append("Invalid website URL format")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def format_resource_summary(resource: Resource) -> Dict[str, Any]:
    """Format a resource for summary display.
    
    This function creates a standardized summary format for resources that includes
    essential information in a clean, organized structure. It's used for list
    views and search results where full resource details aren't needed.
    
    Args:
        resource (Resource): The resource to format for summary display.
        
    Returns:
        Dict[str, Any]: A dictionary containing formatted resource summary including:
            - id (int): Resource ID
            - name (str): Resource name
            - description (str): Truncated description (200 chars max)
            - status (str): Resource status
            - category (str): Category name if assigned
            - service_types (list): List of service type names
            - location (dict): City, state, county information
            - contact (dict): Phone, email, website information
            - operational (dict): Emergency and 24-hour service flags
            - created_at (str): ISO timestamp of creation
            - updated_at (str): ISO timestamp of last update
    """
    return {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
        "status": resource.status,
        "category": resource.category.name if resource.category else None,
        "service_types": [st.name for st in resource.service_types.all()],
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
        },
        "created_at": resource.created_at.isoformat(),
        "updated_at": resource.updated_at.isoformat()
    }


def format_error_response(message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """Format a standardized error response.
    
    This function creates a consistent error response format used throughout
    the MCP server. It ensures all error responses follow the same structure
    for better client-side handling and debugging.
    
    Args:
        message (str): Primary error message describing what went wrong.
        details (Optional[str]): Additional error details for debugging purposes.
                               Should not contain sensitive information.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): Always "error"
            - message (str): The primary error message
            - data (None): Always None for error responses
            - details (str, optional): Additional error details if provided
    """
    response = {
        "status": "error",
        "message": message,
        "data": None
    }
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(message: str, data: Any) -> Dict[str, Any]:
    """Format a standardized success response.
    
    This function creates a consistent success response format used throughout
    the MCP server. It ensures all success responses follow the same structure
    for better client-side handling and consistency.
    
    Args:
        message (str): Success message describing what was accomplished.
        data (Any): The response data to include. Can be any type (dict, list, etc.).
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): Always "success"
            - message (str): The success message
            - data (Any): The response data provided
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def paginate_queryset(queryset, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Apply pagination to a queryset and return pagination info.
    
    This function provides consistent pagination functionality across all MCP tools.
    It applies limits and offsets to Django querysets and returns both the
    paginated results and comprehensive pagination metadata.
    
    Args:
        queryset: Django QuerySet to paginate. Should be a valid Django QuerySet.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - results: The paginated queryset results
            - pagination (dict): Pagination metadata including:
                - total_count (int): Total number of items in the queryset
                - limit (int): The limit applied
                - offset (int): The offset applied
                - has_more (bool): Whether there are more results available
    """
    # Cap limit at 100
    limit = min(limit, 100)
    
    # Get total count
    total_count = queryset.count()
    
    # Apply pagination
    paginated_queryset = queryset[offset:offset + limit]
    
    return {
        "results": paginated_queryset,
        "pagination": {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
    }
