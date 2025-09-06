"""
Resource Tools - CRUD Operations for Resources

This module provides MCP tools for performing CRUD operations on resources
in the Community Resource Directory. All operations include comprehensive
validation, error handling, and audit trail preservation.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from asgiref.sync import sync_to_async
from directory.models import Resource, TaxonomyCategory, ServiceType
from directory.models.analytics.audit import AuditLog


async def create_resource(
    name: str,
    description: str = "",
    category_id: Optional[int] = None,
    service_type_ids: Optional[List[int]] = None,
    phone: str = "",
    email: str = "",
    website: str = "",
    address1: str = "",
    address2: str = "",
    city: str = "",
    state: str = "",
    county: str = "",
    postal_code: str = "",
    hours_of_operation: str = "",
    is_emergency_service: bool = False,
    is_24_hour_service: bool = False,
    eligibility_requirements: str = "",
    populations_served: str = "",
    insurance_accepted: str = "",
    cost_information: str = "",
    languages_available: str = "",
    capacity: str = "",
    notes: str = "",
    created_by_user_id: int = 1,  # Default to admin user
) -> Dict[str, Any]:
    """Create a new resource in the Community Resource Directory.
    
    This function creates a new resource entry with comprehensive validation,
    audit trail creation, and proper relationship handling. The resource is
    created in "draft" status and requires review before being published.
    
    Args:
        name (str): The name of the resource (required). This is the primary
                   identifier and should be descriptive and unique.
        description (str): Detailed description of the resource and its services.
                          This is visible to the public and should be comprehensive.
        category_id (Optional[int]): ID of the taxonomy category this resource
                                   belongs to. Use list_categories_tool to get
                                   available categories.
        service_type_ids (Optional[List[int]]): List of service type IDs that this
                                              resource provides. Use list_service_types_tool
                                              to get available service types.
        phone (str): Primary contact phone number. Should include area code.
        email (str): Primary contact email address. Must be valid email format.
        website (str): Resource's website URL. Must be valid URL format.
        address1 (str): Primary street address line.
        address2 (str): Secondary address line (suite, unit, etc.).
        city (str): City name where the resource is located.
        state (str): Two-letter state abbreviation (e.g., "KY", "CA").
        county (str): County or parish name where the resource is located.
        postal_code (str): ZIP code or postal code.
        hours_of_operation (str): Service hours and availability information.
                                 Can include days, times, and special schedules.
        is_emergency_service (bool): Whether this resource provides emergency
                                   or crisis services. Important for emergency
                                   service searches.
        is_24_hour_service (bool): Whether the service is available 24/7.
                                  Important for after-hours service searches.
        eligibility_requirements (str): Who can access this service, including
                                       age restrictions, income requirements,
                                       residency requirements, etc.
        populations_served (str): Target demographics served (e.g., "Adults",
                                 "Children", "Seniors", "Veterans").
        insurance_accepted (str): Types of insurance accepted or payment methods.
        cost_information (str): Fee structure, sliding scale, free services, etc.
        languages_available (str): Languages in which services are provided.
        capacity (str): Service capacity information (number of clients,
                       waiting lists, etc.).
        notes (str): Internal notes not visible to the public. Use for
                    administrative information, internal contacts, etc.
        created_by_user_id (int): ID of the user creating this resource.
                                 Defaults to 1 (admin user).
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains created resource details including ID,
                          name, status, created_at timestamp, category name,
                          and service type names if successful, None if error
    
    Raises:
        ValidationError: If required fields are missing or data format is invalid
        DoesNotExist: If category_id or service_type_ids reference non-existent records
    """
    try:
        # Validate category if provided
        category = None
        if category_id:
            try:
                category = await sync_to_async(TaxonomyCategory.objects.get)(id=category_id)
            except TaxonomyCategory.DoesNotExist:
                return {
                    "status": "error",
                    "message": f"Category with ID {category_id} not found",
                    "data": None
                }
        
        # Validate service types if provided
        service_types = []
        if service_type_ids:
            try:
                service_types = await sync_to_async(list)(ServiceType.objects.filter(id__in=service_type_ids))
                if len(service_types) != len(service_type_ids):
                    found_ids = [st.id for st in service_types]
                    missing_ids = [sid for sid in service_type_ids if sid not in found_ids]
                    return {
                        "status": "error",
                        "message": f"Service types with IDs {missing_ids} not found",
                        "data": None
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error validating service types: {str(e)}",
                    "data": None
                }
        
        # Create the resource
        resource = await sync_to_async(Resource.objects.create)(
            name=name,
            description=description,
            category=category,
            phone=phone,
            email=email,
            website=website,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            county=county,
            postal_code=postal_code,
            hours_of_operation=hours_of_operation,
            is_emergency_service=is_emergency_service,
            is_24_hour_service=is_24_hour_service,
            eligibility_requirements=eligibility_requirements,
            populations_served=populations_served,
            insurance_accepted=insurance_accepted,
            cost_information=cost_information,
            languages_available=languages_available,
            capacity=capacity,
            notes=notes,
            created_by_id=created_by_user_id,
            updated_by_id=created_by_user_id,
            status="draft"  # Start as draft
        )
        
        # Add service types if provided
        if service_types:
            await sync_to_async(resource.service_types.set)(service_types)
        
        # Create audit log entry
        from django.contrib.auth.models import User
        try:
            user = await sync_to_async(User.objects.get)(id=created_by_user_id)
        except User.DoesNotExist:
            user = await sync_to_async(User.objects.first)()  # Fallback to first user
        
        await sync_to_async(AuditLog.objects.create)(
            actor=user,
            action="create_resource",
            target_table="resource",
            target_id=str(resource.id),
            metadata_json=json.dumps({
                "resource_name": name,
                "field_name": "resource",
                "old_value": "",
                "new_value": f"Resource '{name}' created",
                "notes": "Resource created via MCP server"
            })
        )
        
        return {
            "status": "success",
            "message": f"Resource '{name}' created successfully",
            "data": {
                "id": resource.id,
                "name": resource.name,
                "status": resource.status,
                "created_at": resource.created_at.isoformat(),
                "category": category.name if category else None,
                "service_types": [st.name for st in service_types]
            }
        }
            
    except ValidationError as e:
        return {
            "status": "error",
            "message": f"Validation error: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating resource: {str(e)}",
            "data": None
        }


def get_resource(resource_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific resource.
    
    This function retrieves comprehensive information about a single resource
    including all contact details, location information, operational details,
    service types, category, and metadata. This is useful for getting
    complete resource information for display or editing purposes.
    
    Args:
        resource_id (int): The unique identifier of the resource to retrieve.
                          Use list_resources or search_resources to find resource IDs.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Complete resource information including:
                - id (int): Resource ID
                - name (str): Resource name
                - description (str): Full description
                - category (dict): Category information with id and name
                - service_types (list): List of service type objects with id and name
                - contact (dict): Phone, email, website
                - location (dict): Address information
                - operational (dict): Status, hours, emergency flags, etc.
                - metadata (dict): Creation/update timestamps, verification info
              None if error
    
    Raises:
        DoesNotExist: If resource_id does not exist in the database
    """
    try:
        resource = Resource.objects.select_related('category').prefetch_related('service_types').get(id=resource_id)
        service_types = list(resource.service_types.all())
        
        return {
            "status": "success",
            "message": f"Resource '{resource.name}' retrieved successfully",
            "data": {
                "id": resource.id,
                "name": resource.name,
                "description": resource.description,
                "category": {
                    "id": resource.category.id if resource.category else None,
                    "name": resource.category.name if resource.category else None
                },
                "service_types": [
                    {"id": st.id, "name": st.name}
                    for st in service_types
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
                    "last_verified_by": resource.last_verified_by.username if resource.last_verified_by else None,
                    "verification_frequency_days": resource.verification_frequency_days,
                    "notes": resource.notes
                }
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
            "message": f"Error retrieving resource: {str(e)}",
            "data": None
        }


async def update_resource(
    resource_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    service_type_ids: Optional[List[int]] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    website: Optional[str] = None,
    address1: Optional[str] = None,
    address2: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    postal_code: Optional[str] = None,
    hours_of_operation: Optional[str] = None,
    is_emergency_service: Optional[bool] = None,
    is_24_hour_service: Optional[bool] = None,
    eligibility_requirements: Optional[str] = None,
    populations_served: Optional[str] = None,
    insurance_accepted: Optional[str] = None,
    cost_information: Optional[str] = None,
    languages_available: Optional[str] = None,
    capacity: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
    last_verified_at: Optional[str] = None,
    last_verified_by: Optional[int] = None,
    verification_frequency_days: Optional[int] = None,
    updated_by_user_id: int = 1,  # Default to admin user
) -> Dict[str, Any]:
    """Update an existing resource in the Community Resource Directory.
    
    This function allows you to update any field of an existing resource. Only
    the fields you provide will be updated - all other fields remain unchanged.
    All changes are tracked in the audit trail for compliance and history.
    
    Args:
        resource_id (int): The unique identifier of the resource to update.
        name (Optional[str]): New resource name.
        description (Optional[str]): New resource description.
        category_id (Optional[int]): New category ID. Set to 0 to clear category.
        service_type_ids (Optional[List[int]]): New list of service type IDs.
        phone (Optional[str]): New phone number.
        email (Optional[str]): New email address.
        website (Optional[str]): New website URL.
        address1 (Optional[str]): New primary address.
        address2 (Optional[str]): New secondary address.
        city (Optional[str]): New city name.
        state (Optional[str]): New state abbreviation (2 characters).
        county (Optional[str]): New county name.
        postal_code (Optional[str]): New postal code.
        hours_of_operation (Optional[str]): New hours of operation.
        is_emergency_service (Optional[bool]): New emergency service flag.
        is_24_hour_service (Optional[bool]): New 24-hour service flag.
        eligibility_requirements (Optional[str]): New eligibility requirements.
        populations_served (Optional[str]): New populations served.
        insurance_accepted (Optional[str]): New insurance accepted.
        cost_information (Optional[str]): New cost information.
        languages_available (Optional[str]): New languages available.
        capacity (Optional[str]): New capacity information.
        notes (Optional[str]): New internal notes.
        status (Optional[str]): New status. Valid values: "draft", "needs_review", "published".
        updated_by_user_id (int): ID of the user making the update. Defaults to 1.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains updated resource details including:
                - id (int): Resource ID
                - name (str): Updated resource name
                - status (str): Current status
                - updated_at (str): ISO timestamp of update
                - changes_made (int): Number of fields that were changed
                - fields_updated (list): List of field names that were updated
              None if error
    
    Raises:
        DoesNotExist: If resource_id does not exist
        ValidationError: If provided data is invalid
    """
    try:
        resource = await sync_to_async(Resource.objects.get)(id=resource_id)
        
        # Track changes for audit trail
        changes = []
        
        # Update fields if provided
        if name is not None and name != resource.name:
            changes.append(("name", resource.name, name))
            resource.name = name
            
        if description is not None and description != resource.description:
            changes.append(("description", resource.description, description))
            resource.description = description
            
        if category_id is not None:
            if category_id == 0:  # Clear category
                if resource.category:
                    changes.append(("category", resource.category.name, ""))
                    resource.category = None
            else:
                try:
                    new_category = await sync_to_async(TaxonomyCategory.objects.get)(id=category_id)
                    if resource.category != new_category:
                        changes.append(("category", 
                                       resource.category.name if resource.category else "", 
                                       new_category.name))
                        resource.category = new_category
                except TaxonomyCategory.DoesNotExist:
                    return {
                        "status": "error",
                        "message": f"Category with ID {category_id} not found",
                        "data": None
                    }
        
        # Update other fields
        field_updates = [
            ("phone", phone), ("email", email), ("website", website),
            ("address1", address1), ("address2", address2), ("city", city),
            ("state", state), ("county", county), ("postal_code", postal_code),
            ("hours_of_operation", hours_of_operation),
            ("eligibility_requirements", eligibility_requirements),
            ("populations_served", populations_served),
            ("insurance_accepted", insurance_accepted),
            ("cost_information", cost_information),
            ("languages_available", languages_available),
            ("capacity", capacity), ("notes", notes), ("status", status)
        ]
        
        # Handle verification fields
        if last_verified_at is not None:
            from datetime import datetime
            from django.utils import timezone
            try:
                # Handle both Z and +00:00 timezone formats
                if last_verified_at.endswith('Z'):
                    verified_datetime = datetime.fromisoformat(last_verified_at.replace('Z', '+00:00'))
                else:
                    verified_datetime = datetime.fromisoformat(last_verified_at)
                
                # If datetime is already timezone-aware, use it directly
                # If it's naive, make it timezone-aware
                if verified_datetime.tzinfo is None:
                    verified_datetime = timezone.make_aware(verified_datetime)
                
                if resource.last_verified_at != verified_datetime:
                    changes.append(("last_verified_at", resource.last_verified_at, verified_datetime))
                    resource.last_verified_at = verified_datetime
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Invalid date format for last_verified_at: {last_verified_at}. Use ISO format (YYYY-MM-DDTHH:MM:SS). Error: {str(e)}",
                    "data": None
                }
        
        if last_verified_by is not None:
            from django.contrib.auth.models import User
            try:
                verifier = await sync_to_async(User.objects.get)(id=last_verified_by)
                if resource.last_verified_by != verifier:
                    changes.append(("last_verified_by", 
                                   resource.last_verified_by.username if resource.last_verified_by else "", 
                                   verifier.username))
                    resource.last_verified_by = verifier
            except User.DoesNotExist:
                return {
                    "status": "error",
                    "message": f"User with ID {last_verified_by} not found for last_verified_by",
                    "data": None
                }
        
        if verification_frequency_days is not None:
            if resource.verification_frequency_days != verification_frequency_days:
                changes.append(("verification_frequency_days", resource.verification_frequency_days, verification_frequency_days))
                resource.verification_frequency_days = verification_frequency_days
        
        for field_name, new_value in field_updates:
            if new_value is not None:
                old_value = getattr(resource, field_name)
                if old_value != new_value:
                    changes.append((field_name, old_value, new_value))
                    setattr(resource, field_name, new_value)
        
        # Handle boolean fields
        if is_emergency_service is not None and is_emergency_service != resource.is_emergency_service:
            changes.append(("is_emergency_service", resource.is_emergency_service, is_emergency_service))
            resource.is_emergency_service = is_emergency_service
            
        if is_24_hour_service is not None and is_24_hour_service != resource.is_24_hour_service:
            changes.append(("is_24_hour_service", resource.is_24_hour_service, is_24_hour_service))
            resource.is_24_hour_service = is_24_hour_service
        
        # Update service types if provided
        if service_type_ids is not None:
            try:
                new_service_types = await sync_to_async(list)(ServiceType.objects.filter(id__in=service_type_ids))
                if len(new_service_types) != len(service_type_ids):
                    found_ids = [st.id for st in new_service_types]
                    missing_ids = [sid for sid in service_type_ids if sid not in found_ids]
                    return {
                        "status": "error",
                        "message": f"Service types with IDs {missing_ids} not found",
                        "data": None
                    }
                
                old_service_types = await sync_to_async(list)(resource.service_types.all())
                if set(st.id for st in old_service_types) != set(st.id for st in new_service_types):
                    changes.append(("service_types", 
                                   [st.name for st in old_service_types],
                                   [st.name for st in new_service_types]))
                    await sync_to_async(resource.service_types.set)(new_service_types)
                    
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error updating service types: {str(e)}",
                    "data": None
                }
        
        # Save the resource
        resource.updated_by_id = updated_by_user_id
        
        # If any changes were made, set status to "needs_review" for human review
        if changes:
            if resource.status == "published":
                changes.append(("status", resource.status, "needs_review"))
                resource.status = "needs_review"
        
        await sync_to_async(resource.save)()
        
        # Create audit log entries for changes
        from django.contrib.auth.models import User
        try:
            user = await sync_to_async(User.objects.get)(id=updated_by_user_id)
        except User.DoesNotExist:
            user = await sync_to_async(User.objects.first)()  # Fallback to first user
        
        for field_name, old_value, new_value in changes:
            await sync_to_async(AuditLog.objects.create)(
                actor=user,
                action="update_resource",
                target_table="resource",
                target_id=str(resource.id),
                metadata_json=json.dumps({
                    "resource_name": resource.name,
                    "field_name": field_name,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "notes": f"Field updated via MCP server"
                })
            )
        
        return {
            "status": "success",
            "message": f"Resource '{resource.name}' updated successfully",
            "data": {
                "id": resource.id,
                "name": resource.name,
                "status": resource.status,
                "updated_at": resource.updated_at.isoformat(),
                "changes_made": len(changes),
                "fields_updated": [change[0] for change in changes]
            }
        }
            
    except Resource.DoesNotExist:
        return {
            "status": "error",
            "message": f"Resource with ID {resource_id} not found",
            "data": None
        }
    except ValidationError as e:
        return {
            "status": "error",
            "message": f"Validation error: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating resource: {str(e)}",
            "data": None
        }


async def archive_resource(
    resource_id: int,
    archived_by_user_id: int = 1,  # Default to admin user
    reason: str = "Archived via MCP server"
) -> Dict[str, Any]:
    """Archive (soft delete) a resource from the Community Resource Directory.
    
    This function performs a soft delete on a resource, marking it as archived
    rather than permanently deleting it. Archived resources are hidden from
    public searches but can be restored if needed. This preserves data
    integrity and maintains audit trails.
    
    Args:
        resource_id (int): The unique identifier of the resource to archive.
        archived_by_user_id (int): ID of the user performing the archive action.
                                 Defaults to 1 (admin user).
        reason (str): Reason for archiving the resource. This is logged in
                     the audit trail for compliance and tracking purposes.
                     Defaults to "Archived via MCP server".
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains archive confirmation including:
                - id (int): Resource ID
                - name (str): Resource name
                - archived_at (str): ISO timestamp of archive action
                - reason (str): Reason for archiving
              None if error
    
    Raises:
        DoesNotExist: If resource_id does not exist
    """
    try:
        resource = await sync_to_async(Resource.objects.get)(id=resource_id)
        
        if resource.is_deleted:
            return {
                "status": "error",
                "message": f"Resource '{resource.name}' is already archived",
                "data": None
            }
        
        # Archive the resource
        resource.is_deleted = True
        resource.updated_by_id = archived_by_user_id
        await sync_to_async(resource.save)()
        
        # Create audit log entry
        from django.contrib.auth.models import User
        try:
            user = await sync_to_async(User.objects.get)(id=archived_by_user_id)
        except User.DoesNotExist:
            user = await sync_to_async(User.objects.first)()  # Fallback to first user
        
        await sync_to_async(AuditLog.objects.create)(
            actor=user,
            action="archive_resource",
            target_table="resource",
            target_id=str(resource.id),
            metadata_json=json.dumps({
                "resource_name": resource.name,
                "field_name": "is_deleted",
                "old_value": "False",
                "new_value": "True",
                "notes": reason
            })
        )
        
        return {
            "status": "success",
            "message": f"Resource '{resource.name}' archived successfully",
            "data": {
                "id": resource.id,
                "name": resource.name,
                "archived_at": resource.updated_at.isoformat(),
                "reason": reason
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
            "message": f"Error archiving resource: {str(e)}",
            "data": None
        }


async def list_resources(
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    service_type_id: Optional[int] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    is_emergency_service: Optional[bool] = None,
    is_24_hour_service: Optional[bool] = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List resources with optional filtering and pagination.
    
    This function retrieves a paginated list of resources with optional filtering
    capabilities. It's useful for browsing resources, administrative tasks,
    and getting overviews of the resource directory contents.
    
    Args:
        status (Optional[str]): Filter by resource status. Valid values:
                              "draft", "needs_review", "published"
        category_id (Optional[int]): Filter by taxonomy category ID.
                                   Use list_categories to get category IDs.
        service_type_id (Optional[int]): Filter by service type ID.
                                       Use list_service_types to get service type IDs.
        city (Optional[str]): Filter by city name (case-insensitive partial match).
        state (Optional[str]): Filter by state abbreviation (exact match, e.g., "KY").
        is_emergency_service (Optional[bool]): Filter by emergency service flag.
        is_24_hour_service (Optional[bool]): Filter by 24-hour service flag.
        include_archived (bool): Whether to include archived resources in results.
                               Defaults to False (excludes archived resources).
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - resources (list): List of resource objects with summary information
                - pagination (dict): Pagination information including total_count,
                                   limit, offset, has_more
              None if error
    """
    try:
        # Start with base queryset
        if include_archived:
            queryset = Resource.objects.all_including_archived()
        else:
            queryset = Resource.objects.all()
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if service_type_id:
            queryset = queryset.filter(service_types__id=service_type_id)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if state:
            queryset = queryset.filter(state__iexact=state)
        if is_emergency_service is not None:
            queryset = queryset.filter(is_emergency_service=is_emergency_service)
        if is_24_hour_service is not None:
            queryset = queryset.filter(is_24_hour_service=is_24_hour_service)
        
        # Get total count
        total_count = await sync_to_async(queryset.count)()
        
        # Apply pagination
        limit = min(limit, 100)  # Cap at 100
        resources = await sync_to_async(list)(
            queryset.select_related('category').prefetch_related('service_types')[
                offset:offset + limit
            ]
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
                    "is_24_hour_service": resource.is_24_hour_service
                },
                "created_at": resource.created_at.isoformat(),
                "updated_at": resource.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "message": f"Retrieved {len(resource_list)} resources",
            "data": {
                "resources": resource_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing resources: {str(e)}",
            "data": None
        }


async def list_resources_needing_verification(
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List resources that need verification based on their verification status.
    
    This function identifies resources that require verification based on their
    verification status and frequency settings. It includes:
    - Resources that have never been verified (last_verified_at is None)
    - Resources that are overdue for verification based on their verification_frequency_days
    - Resources that don't have a verification frequency set
    
    Args:
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - resources (list): List of resources needing verification with
                                 verification status details
                - pagination (dict): Pagination information
                - verification_summary (dict): Summary counts by verification status:
                    - never_verified (int): Count of resources never verified
                    - overdue (int): Count of resources overdue for verification
                    - no_frequency_set (int): Count with no verification frequency
              None if error
    """
    try:
        now = timezone.now()
        
        # Get all non-deleted resources
        queryset = Resource.objects.all()
        
        # Get all resources and filter in Python to find those needing verification
        def get_all_resources():
            return list(
                queryset.select_related('category').prefetch_related('service_types')
                .order_by('last_verified_at', 'created_at')  # Never verified first, then by creation date
            )
        
        all_resources = await sync_to_async(get_all_resources)()
        
        # Filter resources that need verification
        resources_needing_verification = []
        for resource in all_resources:
            verification_status = "never_verified"
            days_overdue = None
            days_until_due = None
            
            if resource.last_verified_at:
                # Resource has been verified before
                if resource.verification_frequency_days:
                    next_verification_due = resource.last_verified_at + timedelta(days=resource.verification_frequency_days)
                    if now > next_verification_due:
                        verification_status = "overdue"
                        days_overdue = (now - next_verification_due).days
                    else:
                        # Resource is not yet due for verification - skip it
                        continue
                else:
                    verification_status = "no_frequency_set"
            else:
                # Resource has never been verified
                verification_status = "never_verified"
            
            # Only include resources that actually need verification
            if verification_status in ["never_verified", "overdue", "no_frequency_set"]:
                resources_needing_verification.append({
                    "resource": resource,
                    "verification_status": verification_status,
                    "days_overdue": days_overdue,
                    "days_until_due": days_until_due
                })
        
        # Apply pagination to the filtered results
        limit = min(limit, 100)  # Cap at 100
        total_count = len(resources_needing_verification)
        paginated_resources = resources_needing_verification[offset:offset + limit]
        
        # Format results
        resource_list = []
        for item in paginated_resources:
            resource = item["resource"]
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
                    "county": resource.county
                },
                "contact": {
                    "phone": resource.phone,
                    "email": resource.email,
                    "website": resource.website
                },
                "verification": {
                    "status": item["verification_status"],
                    "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                    "verification_frequency_days": resource.verification_frequency_days,
                    "days_overdue": item["days_overdue"],
                    "days_until_due": item["days_until_due"]
                },
                "created_at": resource.created_at.isoformat(),
                "updated_at": resource.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "message": f"Retrieved {len(resource_list)} resources needing verification",
            "data": {
                "resources": resource_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "verification_summary": {
                    "never_verified": len([r for r in resources_needing_verification if r["verification_status"] == "never_verified"]),
                    "overdue": len([r for r in resources_needing_verification if r["verification_status"] == "overdue"]),
                    "no_frequency_set": len([r for r in resources_needing_verification if r["verification_status"] == "no_frequency_set"])
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing resources needing verification: {str(e)}",
            "data": None
        }
