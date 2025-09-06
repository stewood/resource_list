"""
CLI Utilities Module

This module provides shared utilities and helper functions for the resource CLI
commands. It includes JSON formatting, validation helpers, and common operations
that are used across multiple commands.

Functions:
    - format_resource_data: Format resource data for JSON output
    - format_service_type_data: Format service type data for JSON output
    - validate_json_input: Validate and parse JSON input strings
    - format_error_response: Format error responses consistently
    - format_success_response: Format success responses consistently
    - get_user_info: Get information about the current user
    - validate_resource_id: Validate resource ID and existence

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import json
import datetime
from typing import Any, Dict, List, Optional, Union

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User

from directory.models import Resource, TaxonomyCategory, ServiceType


def format_resource_data(resource: Resource, include_related: bool = True) -> Dict[str, Any]:
    """
    Format resource data for JSON output.
    
    This function takes a Resource instance and formats it into a dictionary
    suitable for JSON serialization. It handles related objects and converts
    Django model instances to serializable data.
    
    Args:
        resource: Resource instance to format
        include_related: Whether to include related data (categories, service types)
        
    Returns:
        Dict containing formatted resource data
        
    Example:
        >>> resource = Resource.objects.get(id=1)
        >>> data = format_resource_data(resource)
        >>> print(json.dumps(data, indent=2))
    """
    data = {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "status": resource.status,
        "phone": resource.phone,
        "email": resource.email,
        "website": resource.website,
        "address1": resource.address1,
        "address2": resource.address2,
        "city": resource.city,
        "state": resource.state,
        "county": resource.county,
        "postal_code": resource.postal_code,
        "hours_of_operation": resource.hours_of_operation,
        "is_emergency_service": resource.is_emergency_service,
        "is_24_hour_service": resource.is_24_hour_service,
        "eligibility_requirements": resource.eligibility_requirements,
        "populations_served": resource.populations_served,
        "insurance_accepted": resource.insurance_accepted,
        "cost_information": resource.cost_information,
        "languages_available": resource.languages_available,
        "capacity": resource.capacity,
        "source": resource.source,
        "notes": resource.notes,
        "verification_frequency_days": resource.verification_frequency_days,
        "created_at": resource.created_at,
        "updated_at": resource.updated_at,
        "is_deleted": resource.is_deleted,
        "is_archived": resource.is_archived,
    }
    
    # Add related data if requested
    if include_related:
        if resource.category:
            data["category"] = {
                "id": resource.category.id,
                "name": resource.category.name,
                "description": resource.category.description
            }
        
        if resource.service_types.exists():
            data["service_types"] = [
                {
                    "id": st.id,
                    "name": st.name,
                    "description": st.description
                }
                for st in resource.service_types.all()
            ]
        
        if resource.coverage_areas.exists():
            data["coverage_areas"] = []
            for ca in resource.coverage_areas.all():
                coverage_data = {
                    "id": ca.id,
                    "name": ca.name,
                    "kind": ca.kind
                }
                
                # Add state and county from ext_ids if available
                if ca.ext_ids:
                    if "state_fips" in ca.ext_ids:
                        coverage_data["state_fips"] = ca.ext_ids["state_fips"]
                    if "county_fips" in ca.ext_ids:
                        coverage_data["county_fips"] = ca.ext_ids["county_fips"]
                
                data["coverage_areas"].append(coverage_data)
        
        if resource.last_verified_by:
            data["last_verified_by"] = {
                "id": resource.last_verified_by.id,
                "username": resource.last_verified_by.username
            }
        
        if resource.created_by:
            data["created_by"] = {
                "id": resource.created_by.id,
                "username": resource.created_by.username
            }
        
        if resource.updated_by:
            data["updated_by"] = {
                "id": resource.updated_by.id,
                "username": resource.updated_by.username
            }
    
    return data


def format_service_type_data(service_type: ServiceType) -> Dict[str, Any]:
    """
    Format service type data for JSON output.
    
    This function takes a ServiceType instance and formats it into a dictionary
    suitable for JSON serialization.
    
    Args:
        service_type: ServiceType instance to format
        
    Returns:
        Dict containing formatted service type data
        
    Example:
        >>> service_type = ServiceType.objects.get(id=1)
        >>> data = format_service_type_data(service_type)
        >>> print(json.dumps(data, indent=2))
    """
    data = {
        "id": service_type.id,
        "name": service_type.name,
        "description": service_type.description,
        "created_at": service_type.created_at,
    }
    
    # Add related data if available
    if hasattr(service_type, 'resources'):
        data["resource_count"] = service_type.resources.count()
    
    return data


def validate_json_input(json_string: str) -> Dict[str, Any]:
    """
    Validate and parse JSON input string.
    
    This function validates that a JSON string is properly formatted and
    returns the parsed data. It provides helpful error messages for
    common JSON parsing issues.
    
    Args:
        json_string: JSON string to validate and parse
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        ValueError: If JSON is invalid or cannot be parsed
        
    Example:
        >>> try:
        ...     data = validate_json_input('{"name": "Test Resource"}')
        ...     print(data["name"])
        ... except ValueError as e:
        ...     print(f"Invalid JSON: {e}")
    """
    if not json_string or not json_string.strip():
        raise ValueError("JSON string cannot be empty")
    
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    if not isinstance(data, dict):
        raise ValueError("JSON input must be an object (dictionary)")
    
    return data


def format_error_response(message: str, error_code: Optional[str] = None, 
                         details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format error responses consistently.
    
    This function creates a standardized error response format that
    includes the error message, timestamp, and optional error code
    and details.
    
    Args:
        message: Error message to display
        error_code: Optional error code for programmatic handling
        details: Optional dictionary with additional error details
        
    Returns:
        Formatted error response dictionary
        
    Example:
        >>> error = format_error_response("Resource not found", "NOT_FOUND", {"id": 123})
        >>> print(json.dumps(error, indent=2))
    """
    response = {
        "error": True,
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(message: str, data: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format success responses consistently.
    
    This function creates a standardized success response format that
    includes the success message, timestamp, and optional data and metadata.
    
    Args:
        message: Success message to display
        data: Optional data to include in the response
        metadata: Optional metadata about the operation
        
    Returns:
        Formatted success response dictionary
        
    Example:
        >>> success = format_success_response("Resource created", {"id": 123})
        >>> print(json.dumps(success, indent=2))
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if data:
        response["data"] = data
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def get_user_info(user: Optional[User] = None) -> Dict[str, Any]:
    """
    Get information about a user.
    
    This function extracts user information in a standardized format
    for use in CLI responses and logging.
    
    Args:
        user: User instance to get information about (defaults to None)
        
    Returns:
        Dictionary containing user information
        
    Example:
        >>> user_info = get_user_info(user)
        >>> print(f"User: {user_info['username']}")
    """
    if not user:
        return {
            "id": None,
            "username": "system",
            "email": None,
            "is_authenticated": False
        }
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_authenticated": user.is_authenticated,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser
    }


def validate_resource_id(resource_id: int) -> Resource:
    """
    Validate resource ID and return the resource instance.
    
    This function validates that a resource ID is valid and returns
    the corresponding Resource instance. It provides helpful error
    messages for common validation issues.
    
    Args:
        resource_id: Numeric ID of the resource to validate
        
    Returns:
        Resource instance if found and valid
        
    Raises:
        ValueError: If resource ID is invalid
        ObjectDoesNotExist: If resource with the given ID doesn't exist
        
    Example:
        >>> try:
        ...     resource = validate_resource_id(123)
        ...     print(f"Found resource: {resource.name}")
        ... except (ValueError, ObjectDoesNotExist) as e:
        ...     print(f"Error: {e}")
    """
    if not isinstance(resource_id, int) or resource_id <= 0:
        raise ValueError("Resource ID must be a positive integer")
    
    try:
        resource = Resource.objects.get(id=resource_id)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(f"Resource with ID {resource_id} not found")
    
    return resource


def format_list_response(
    resources: List[Resource], 
    total_count: int, 
    page: int, 
    page_size: int, 
    filters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format a list of resources for JSON response.
    
    Args:
        resources: List of Resource instances
        total_count: Total number of resources matching filters
        page: Current page number
        page_size: Number of resources per page
        filters: Applied filters
        
    Returns:
        Dict containing formatted list response
    """
    # Format each resource
    formatted_resources = []
    for resource in resources:
        resource_data = format_resource_data(resource, include_related=True)
        formatted_resources.append(resource_data)
    
    # Calculate pagination info
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    response = {
        "data": formatted_resources,
        "pagination": {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        },
        "metadata": {
            "filters_applied": filters,
            "timestamp": str(datetime.datetime.now())
        }
    }
    
    return response


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if a status transition is allowed.
    
    Args:
        current_status: Current status of the resource
        new_status: New status to transition to
        
    Returns:
        True if transition is valid, False otherwise
    """
    # Define valid status transitions
    valid_transitions = {
        "draft": ["needs_review"],
        "needs_review": ["published", "draft"],
        "published": ["draft", "needs_review"]
    }
    
    # Check if current status exists and if transition is valid
    if current_status not in valid_transitions:
        return False
    
    return new_status in valid_transitions[current_status]


def validate_service_areas(area_inputs: List[str], resource_state: Optional[str] = None, auto_resolve_duplicates: bool = False) -> Dict[str, Any]:
    """
    Validate service area inputs and return validation results.
    
    This function validates a list of service area inputs (names or IDs)
    and returns a dictionary with validation results including valid areas,
    invalid areas, and any errors encountered.
    
    Args:
        area_inputs: List of service area names or IDs to validate
        resource_state: Optional state code to help disambiguate areas
        auto_resolve_duplicates: Whether to automatically resolve duplicate names
        
    Returns:
        Dict containing validation results:
        - valid_areas: List of valid area names/IDs
        - invalid_areas: List of invalid area names/IDs
        - errors: List of error messages
        - success: Boolean indicating if validation was successful
        - ambiguous_areas: List of areas with duplicate names (if any)
        - suggestions: Dictionary of suggestions for invalid areas
        
    Example:
        >>> result = validate_service_areas(["Kentucky", "Tennessee", "Invalid Area"])
        >>> print(result)
        {
            'valid_areas': ['Kentucky', 'Tennessee'],
            'invalid_areas': ['Invalid Area'],
            'errors': ['Service area "Invalid Area" not found'],
            'success': False,
            'ambiguous_areas': [],
            'suggestions': {}
        }
    """
    from directory.models.geographic.coverage_area import CoverageArea
    
    if not area_inputs:
        return {
            'valid_areas': [],
            'invalid_areas': [],
            'errors': [],
            'success': True,
            'ambiguous_areas': [],
            'suggestions': {}
        }
    
    valid_areas = []
    invalid_areas = []
    errors = []
    ambiguous_areas = []
    suggestions = {}
    
    for area_input in area_inputs:
        if not area_input or not area_input.strip():
            continue
            
        area_input = area_input.strip()
        
        # Try to find the service area
        try:
            # First try to find by ID if it's numeric
            if area_input.isdigit():
                area = CoverageArea.objects.get(id=int(area_input))
                valid_areas.append({
                    'id': area.id,
                    'name': area.name,
                    'kind': area.kind,
                    'state_fips': getattr(area, 'state_fips', None)
                })
            else:
                # Try to find by name
                areas = CoverageArea.objects.filter(name__iexact=area_input)
                
                if areas.count() == 1:
                    # Single match found
                    area = areas.first()
                    valid_areas.append({
                        'id': area.id,
                        'name': area.name,
                        'kind': area.kind,
                        'state_fips': getattr(area, 'state_fips', None)
                    })
                elif areas.count() > 1:
                    # Multiple matches found - this is ambiguous
                    if auto_resolve_duplicates and resource_state:
                        # Try to resolve by state if auto-resolve is enabled
                        state_areas = areas.filter(state_fips=resource_state)
                        if state_areas.count() == 1:
                            area = state_areas.first()
                            valid_areas.append({
                                'id': area.id,
                                'name': area.name,
                                'kind': area.kind,
                                'state_fips': getattr(area, 'state_fips', None)
                            })
                        else:
                            # Still ambiguous even with state
                            ambiguous_areas.append({
                                'name': area_input,
                                'matches': [
                                    {
                                        'id': a.id,
                                        'name': a.name,
                                        'kind': a.kind,
                                        'state_fips': getattr(a, 'state_fips', None)
                                    }
                                    for a in areas
                                ]
                            })
                    else:
                        # Don't auto-resolve, mark as ambiguous
                        ambiguous_areas.append({
                            'name': area_input,
                            'matches': [
                                {
                                    'id': a.id,
                                    'name': a.name,
                                    'kind': a.kind,
                                    'state_fips': getattr(a, 'state_fips', None)
                                }
                                for a in areas
                            ]
                        })
                else:
                    # No matches found
                    invalid_areas.append(area_input)
                    errors.append(f'Service area "{area_input}" not found')
                    
        except CoverageArea.DoesNotExist:
            invalid_areas.append(area_input)
            errors.append(f'Service area "{area_input}" not found')
        except Exception as e:
            invalid_areas.append(area_input)
            errors.append(f'Error validating service area "{area_input}": {str(e)}')
    
    success = len(invalid_areas) == 0 and len(ambiguous_areas) == 0
    
    return {
        'valid_areas': valid_areas,
        'invalid_areas': invalid_areas,
        'errors': errors,
        'success': success,
        'ambiguous_areas': ambiguous_areas,
        'suggestions': suggestions
    }
