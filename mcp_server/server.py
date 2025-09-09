"""
Community Resource Directory MCP Server

This module provides the main MCP server for the Community Resource Directory,
enabling AI/LLM access to resource management functionality.

The server provides:
- CRUD operations for resources
- Advanced search with FTS5 integration  
- Taxonomy management (categories and service types)
- Static and dynamic resources
- Audit trail preservation

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

# Add the Django project root to the Python path
django_root = Path(__file__).parent.parent
sys.path.insert(0, str(django_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resource_directory.settings")

import django
django.setup()

from fastmcp import FastMCP

# Import Django models
from directory.models import Resource, TaxonomyCategory, ServiceType

# Import MCP tools
try:
    # Try relative imports first (when run as module)
    from .tools.resource_tools import (
        create_resource, get_resource, update_resource, 
        archive_resource, list_resources, list_resources_needing_verification
    )
    from .tools.search_tools import (
        search_resources, search_emergency_services, search_by_location
    )
    from .tools.taxonomy_tools import (
        list_categories, get_category, list_service_types, 
        get_service_type, get_taxonomy_summary
    )
    from .tools.gis_tools import (
        list_coverage_areas, get_coverage_area, search_resources_by_coverage_area,
        assign_coverage_area_to_resource, remove_coverage_area_from_resource,
        get_resource_coverage_areas, search_resources_by_point
    )
    from .resources.static_resources import (
        get_categories_resource, get_service_types_resource, 
        get_taxonomy_overview_resource
    )
    from .resources.dynamic_resources import get_resource_template
except ImportError:
    # Fall back to absolute imports (when run directly)
    from tools.resource_tools import (
        create_resource, get_resource, update_resource, 
        archive_resource, list_resources, list_resources_needing_verification
    )
    from tools.search_tools import (
        search_resources, search_emergency_services, search_by_location
    )
    from tools.taxonomy_tools import (
        list_categories, get_category, list_service_types, 
        get_service_type, get_taxonomy_summary
    )
    from tools.gis_tools import (
        list_coverage_areas, get_coverage_area, search_resources_by_coverage_area,
        assign_coverage_area_to_resource, remove_coverage_area_from_resource,
        get_resource_coverage_areas, search_resources_by_point
    )
    from resources.static_resources import (
        get_categories_resource, get_service_types_resource, 
        get_taxonomy_overview_resource
    )
    from resources.dynamic_resources import get_resource_template

# Create the MCP server instance
mcp = FastMCP(
    name="Community Resource Directory",
    instructions="""
    This MCP server provides access to the Community Resource Directory database.
    
    Available functionality:
    - Resource CRUD operations (create, read, update, archive, list)
    - Advanced search with full-text search capabilities
    - Taxonomy management (categories and service types)
    - Geographic/GIS functionality for service area management
    - Static resources for read-only data access
    - Dynamic resource templates for individual resources
    
    Geographic Features:
    - Coverage areas: cities, counties, states, nationwide, radius-based
    - Resource coverage assignments (assign/remove service areas)
    - Spatial search: find resources by geographic area or point
    - Service area management for London, KY based application
    
    All operations preserve audit trails and maintain data integrity.
    The server integrates with the existing Django models and validation.
    """
)

# Basic test tool to verify server functionality
@mcp.tool()
async def test_connection() -> dict:
    """Test the MCP server connection and Django integration.
    
    This tool verifies that the MCP server is running correctly and can
    successfully connect to the Django database. It returns basic statistics
    about the database contents including resource counts, category counts,
    and service type counts.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains resource_count, category_count, service_type_count
                          if successful, None if error
    """
    try:
        from asgiref.sync import sync_to_async
        
        # Test Django model access
        resource_count = await sync_to_async(Resource.objects.count)()
        category_count = await sync_to_async(TaxonomyCategory.objects.count)()
        service_type_count = await sync_to_async(ServiceType.objects.count)()
        
        return {
            "status": "success",
            "message": "MCP server is running and Django integration is working",
            "data": {
                "resource_count": resource_count,
                "category_count": category_count,
                "service_type_count": service_type_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Django integration error: {str(e)}",
            "data": None
        }

# Resource CRUD Tools
@mcp.tool()
async def create_resource_tool(
    name: str,
    description: str = "",
    category_id: int = None,
    service_type_ids: list = None,
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
    created_by_user_id: int = 1
) -> dict:
    """Create a new resource in the Community Resource Directory.
    
    This tool creates a new resource entry in the directory with comprehensive
    information including contact details, location, operational information,
    and service characteristics. The resource is created in "draft" status
    and requires review before being published.
    
    Args:
        name (str): The name of the resource (required). This is the primary
                   identifier and should be descriptive and unique.
        description (str): Detailed description of the resource and its services.
                          This is visible to the public and should be comprehensive.
        category_id (int, optional): ID of the taxonomy category this resource
                                   belongs to. Use list_categories_tool to get
                                   available categories.
        service_type_ids (list, optional): List of service type IDs that this
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
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains created resource details including ID,
                          name, status, created_at timestamp, category name,
                          and service type names if successful, None if error
    
    Raises:
        ValidationError: If required fields are missing or data format is invalid
        DoesNotExist: If category_id or service_type_ids reference non-existent records
    """
    from asgiref.sync import sync_to_async
    return await sync_to_async(create_resource)(
        name=name, description=description, category_id=category_id,
        service_type_ids=service_type_ids, phone=phone, email=email,
        website=website, address1=address1, address2=address2,
        city=city, state=state, county=county, postal_code=postal_code,
        hours_of_operation=hours_of_operation, is_emergency_service=is_emergency_service,
        is_24_hour_service=is_24_hour_service, eligibility_requirements=eligibility_requirements,
        populations_served=populations_served, insurance_accepted=insurance_accepted,
        cost_information=cost_information, languages_available=languages_available,
        capacity=capacity, notes=notes, created_by_user_id=created_by_user_id
    )

@mcp.tool()
async def get_resource_tool(resource_id: int) -> dict:
    """Get detailed information about a specific resource.
    
    This tool retrieves comprehensive information about a single resource
    including all contact details, location information, operational details,
    service types, category, and metadata. This is useful for getting
    complete resource information for display or editing purposes.
    
    Args:
        resource_id (int): The unique identifier of the resource to retrieve.
                          Use list_resources_tool or search_resources_tool
                          to find resource IDs.
    
    Returns:
        dict: A dictionary containing:
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
    from asgiref.sync import sync_to_async
    return await sync_to_async(get_resource)(resource_id)

@mcp.tool()
async def update_resource_tool(
    resource_id: int,
    name: str = None,
    description: str = None,
    category_id: int = None,
    service_type_ids: list = None,
    phone: str = None,
    email: str = None,
    website: str = None,
    address1: str = None,
    address2: str = None,
    city: str = None,
    state: str = None,
    county: str = None,
    postal_code: str = None,
    hours_of_operation: str = None,
    is_emergency_service: bool = None,
    is_24_hour_service: bool = None,
    eligibility_requirements: str = None,
    populations_served: str = None,
    insurance_accepted: str = None,
    cost_information: str = None,
    languages_available: str = None,
    capacity: str = None,
    notes: str = None,
    status: str = None,
    last_verified_at: str = None,
    last_verified_by: int = None,
    verification_frequency_days: int = None,
    updated_by_user_id: int = 1
) -> dict:
    """Update an existing resource in the Community Resource Directory.
    
    This tool allows you to update any field of an existing resource. Only
    the fields you provide will be updated - all other fields remain unchanged.
    All changes are tracked in the audit trail for compliance and history.
    
    Args:
        resource_id (int): The unique identifier of the resource to update.
        name (str, optional): New resource name.
        description (str, optional): New resource description.
        category_id (int, optional): New category ID. Set to 0 to clear category.
        service_type_ids (list, optional): New list of service type IDs.
        phone (str, optional): New phone number.
        email (str, optional): New email address.
        website (str, optional): New website URL.
        address1 (str, optional): New primary address.
        address2 (str, optional): New secondary address.
        city (str, optional): New city name.
        state (str, optional): New state abbreviation (2 characters).
        county (str, optional): New county name.
        postal_code (str, optional): New postal code.
        hours_of_operation (str, optional): New hours of operation.
        is_emergency_service (bool, optional): New emergency service flag.
        is_24_hour_service (bool, optional): New 24-hour service flag.
        eligibility_requirements (str, optional): New eligibility requirements.
        populations_served (str, optional): New populations served.
        insurance_accepted (str, optional): New insurance accepted.
        cost_information (str, optional): New cost information.
        languages_available (str, optional): New languages available.
        capacity (str, optional): New capacity information.
        notes (str, optional): New internal notes.
        status (str, optional): New status. Valid values: "draft", "needs_review", "published".
        updated_by_user_id (int): ID of the user making the update. Defaults to 1.
    
    Returns:
        dict: A dictionary containing:
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
    from asgiref.sync import sync_to_async
    return await sync_to_async(update_resource)(
        resource_id=resource_id, name=name, description=description,
        category_id=category_id, service_type_ids=service_type_ids,
        phone=phone, email=email, website=website, address1=address1,
        address2=address2, city=city, state=state, county=county,
        postal_code=postal_code, hours_of_operation=hours_of_operation,
        is_emergency_service=is_emergency_service, is_24_hour_service=is_24_hour_service,
        eligibility_requirements=eligibility_requirements, populations_served=populations_served,
        insurance_accepted=insurance_accepted, cost_information=cost_information,
        languages_available=languages_available, capacity=capacity, notes=notes,
        status=status, last_verified_at=last_verified_at, last_verified_by=last_verified_by,
        verification_frequency_days=verification_frequency_days, updated_by_user_id=updated_by_user_id
    )

@mcp.tool()
async def archive_resource_tool(
    resource_id: int,
    archived_by_user_id: int = 1,
    reason: str = "Archived via MCP server"
) -> dict:
    """Archive (soft delete) a resource from the Community Resource Directory.
    
    This tool performs a soft delete on a resource, marking it as archived
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
        dict: A dictionary containing:
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
    from asgiref.sync import sync_to_async
    return await sync_to_async(archive_resource)(resource_id, archived_by_user_id, reason)

@mcp.tool()
async def list_resources_tool(
    status: str = None,
    category_id: int = None,
    service_type_id: int = None,
    city: str = None,
    state: str = None,
    is_emergency_service: bool = None,
    is_24_hour_service: bool = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """List resources with optional filtering and pagination.
    
    This tool retrieves a paginated list of resources with optional filtering
    capabilities. It's useful for browsing resources, administrative tasks,
    and getting overviews of the resource directory contents.
    
    Args:
        status (str, optional): Filter by resource status. Valid values:
                              "draft", "needs_review", "published"
        category_id (int, optional): Filter by taxonomy category ID.
                                   Use list_categories_tool to get category IDs.
        service_type_id (int, optional): Filter by service type ID.
                                       Use list_service_types_tool to get service type IDs.
        city (str, optional): Filter by city name (case-insensitive partial match).
        state (str, optional): Filter by state abbreviation (exact match, e.g., "KY").
        is_emergency_service (bool, optional): Filter by emergency service flag.
        is_24_hour_service (bool, optional): Filter by 24-hour service flag.
        include_archived (bool): Whether to include archived resources in results.
                               Defaults to False (excludes archived resources).
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - resources (list): List of resource objects with summary information
                - pagination (dict): Pagination information including total_count,
                                   limit, offset, has_more
              None if error
    """
    from asgiref.sync import sync_to_async
    return await sync_to_async(list_resources)(
        status=status, category_id=category_id, service_type_id=service_type_id,
        city=city, state=state, is_emergency_service=is_emergency_service,
        is_24_hour_service=is_24_hour_service, include_archived=include_archived,
        limit=limit, offset=offset
    )

@mcp.tool()
async def list_unverified_resources_tool(
    limit: int = 50,
    offset: int = 0
) -> dict:
    """List resources that need verification (never verified or due for verification).
    
    This tool identifies resources that require verification based on their
    verification status and frequency settings. It includes resources that have
    never been verified, are overdue for verification, or don't have a
    verification frequency set.
    
    Note: Resources with status "needs_review" are excluded as they are already
    in the review queue and don't need additional verification.
    
    Args:
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
    
    Returns:
        dict: A dictionary containing:
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
    from asgiref.sync import sync_to_async
    return await sync_to_async(list_resources_needing_verification)(limit=limit, offset=offset)

# Search Tools
@mcp.tool()
async def search_resources_tool(
    query: str,
    search_type: str = "combined",
    category_id: int = None,
    service_type_id: int = None,
    city: str = None,
    state: str = None,
    county: str = None,
    is_emergency_service: bool = None,
    is_24_hour_service: bool = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """Search resources using advanced search capabilities with FTS5 integration.
    
    This tool provides powerful search functionality using full-text search (FTS5)
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
        category_id (int, optional): Filter results by taxonomy category ID.
        service_type_id (int, optional): Filter results by service type ID.
        city (str, optional): Filter by city name (case-insensitive partial match).
        state (str, optional): Filter by state abbreviation (exact match).
        county (str, optional): Filter by county name (case-insensitive partial match).
        is_emergency_service (bool, optional): Filter by emergency service flag.
        is_24_hour_service (bool, optional): Filter by 24-hour service flag.
        status (str, optional): Filter by resource status ("draft", "needs_review", "published").
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
    
    Returns:
        dict: A dictionary containing:
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
    return await search_resources(
        query=query, search_type=search_type, category_id=category_id,
        service_type_id=service_type_id, city=city, state=state, county=county,
        is_emergency_service=is_emergency_service, is_24_hour_service=is_24_hour_service,
        status=status, limit=limit, offset=offset
    )

@mcp.tool()
async def search_emergency_services_tool(
    city: str = None,
    state: str = None,
    county: str = None,
    limit: int = 50
) -> dict:
    """Search for emergency and crisis services by location.
    
    This specialized tool finds emergency and crisis services that are marked
    as emergency services and are published. It's designed for urgent situations
    where immediate access to crisis resources is needed.
    
    Args:
        city (str, optional): Filter by city name (case-insensitive partial match).
        state (str, optional): Filter by state abbreviation (exact match, e.g., "KY").
        county (str, optional): Filter by county name (case-insensitive partial match).
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - emergency_services (list): List of emergency services with
                                           detailed operational information
                - total_count (int): Total number of emergency services found
                - location_filter (dict): Summary of location filters applied
              None if error
    """
    return await search_emergency_services(city=city, state=state, county=county, limit=limit)

@mcp.tool()
async def search_by_location_tool(
    city: str = None,
    state: str = None,
    county: str = None,
    category_id: int = None,
    service_type_id: int = None,
    limit: int = 50
) -> dict:
    """Search resources by geographic location with optional service filtering.
    
    This tool finds published resources within specific geographic areas and
    optionally filters by service category or type. It's useful for finding
    all available services in a particular location or region.
    
    Args:
        city (str, optional): Filter by city name (case-insensitive partial match).
        state (str, optional): Filter by state abbreviation (exact match, e.g., "KY").
        county (str, optional): Filter by county name (case-insensitive partial match).
        category_id (int, optional): Filter by taxonomy category ID.
                                   Use list_categories_tool to get category IDs.
        service_type_id (int, optional): Filter by service type ID.
                                       Use list_service_types_tool to get service type IDs.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
    
    Returns:
        dict: A dictionary containing:
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
    return await search_by_location(
        city=city, state=state, county=county,
        category_id=category_id, service_type_id=service_type_id, limit=limit
    )

# Taxonomy Tools
@mcp.tool()
async def list_categories_tool(
    include_resource_count: bool = True,
    published_only: bool = True
) -> dict:
    """List all taxonomy categories with optional resource counts.
    
    This tool retrieves all available taxonomy categories in the system,
    optionally including the count of resources in each category. Categories
    are the top-level classification system for organizing resources.
    
    Args:
        include_resource_count (bool): Whether to include the number of resources
                                     in each category. Defaults to True.
        published_only (bool): Whether to count only published resources when
                             calculating resource counts. Defaults to True.
    
    Returns:
        dict: A dictionary containing:
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
    return await list_categories(include_resource_count=include_resource_count, published_only=published_only)

@mcp.tool()
async def get_category_tool(category_id: int, include_resources: bool = False) -> dict:
    """Get detailed information about a specific category.
    
    This tool retrieves comprehensive information about a single taxonomy
    category, optionally including all resources that belong to that category.
    
    Args:
        category_id (int): The unique identifier of the category to retrieve.
        include_resources (bool): Whether to include a list of all resources
                                in this category. Defaults to False.
    
    Returns:
        dict: A dictionary containing:
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
    return await get_category(category_id, include_resources)

@mcp.tool()
async def list_service_types_tool(
    category_id: int = None,
    include_resource_count: bool = True,
    published_only: bool = True
) -> dict:
    """List service types with optional filtering and resource counts.
    
    This tool retrieves service types, which are the specific types of services
    that resources can provide. Service types are more granular than categories
    and can be filtered by category to show only relevant service types.
    
    Args:
        category_id (int, optional): Filter service types to only those that
                                   are used by resources in this category.
        include_resource_count (bool): Whether to include the number of resources
                                     that provide each service type. Defaults to True.
        published_only (bool): Whether to count only published resources when
                             calculating resource counts. Defaults to True.
    
    Returns:
        dict: A dictionary containing:
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
    return await list_service_types(
        category_id=category_id, include_resource_count=include_resource_count,
        published_only=published_only
    )

@mcp.tool()
async def get_service_type_tool(service_type_id: int, include_resources: bool = False) -> dict:
    """Get detailed information about a specific service type.
    
    This tool retrieves comprehensive information about a single service type,
    optionally including all resources that provide this type of service.
    
    Args:
        service_type_id (int): The unique identifier of the service type to retrieve.
        include_resources (bool): Whether to include a list of all resources
                                that provide this service type. Defaults to False.
    
    Returns:
        dict: A dictionary containing:
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
    return await get_service_type(service_type_id, include_resources)

@mcp.tool()
async def get_taxonomy_summary_tool() -> dict:
    """Get a comprehensive summary of the taxonomy system.
    
    This tool provides an overview of the entire taxonomy system including
    counts of categories, service types, and resources, plus the top
    categories and service types by resource count.
    
    Returns:
        dict: A dictionary containing:
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
    return await get_taxonomy_summary()

# GIS Tools
@mcp.tool()
async def list_coverage_areas_tool(
    kind: str = None,
    state: str = None,
    state_fips: str = None,
    county_fips: str = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """List coverage areas with optional filtering.
    
    This tool retrieves geographic coverage areas that define service territories
    for resources. Coverage areas can be cities, counties, states, custom polygons,
    or radius-based areas around specific points.
    
    Args:
        kind (str, optional): Filter by coverage area type. Valid values:
                            - "CITY": City-level coverage areas
                            - "COUNTY": County-level coverage areas
                            - "STATE": State-level coverage areas
                            - "RADIUS": Radius-based coverage areas
                            - "POLYGON": Custom polygon coverage areas
        state (str, optional): Filter by state for administrative areas (cities/counties).
                             Use two-letter state abbreviation (e.g., "KY" for Kentucky).
                             This will be automatically converted to the appropriate FIPS code.
        state_fips (str, optional): Filter by state FIPS code (2-digit string, e.g., "21").
                                   Kentucky's state FIPS code is "21".
        county_fips (str, optional): Filter by county FIPS code (3-digit string, e.g., "125").
                                    Laurel County, KY's FIPS code is "125".
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
    
    Examples:
        # Find all Kentucky counties using state abbreviation
        list_coverage_areas_tool(kind="COUNTY", state="KY")
        
        # Find all Kentucky counties using state FIPS code
        list_coverage_areas_tool(kind="COUNTY", state_fips="21")
        
        # Find Laurel County specifically
        list_coverage_areas_tool(kind="COUNTY", county_fips="125")
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - coverage_areas (list): List of coverage area objects with id, kind,
                                       name, display_name, fips_codes, and geometry info
                - pagination (dict): Pagination information
                - filters_applied (dict): Summary of filters applied
              None if error
    """
    return await list_coverage_areas(
        kind=kind, 
        state=state, 
        state_fips=state_fips, 
        county_fips=county_fips, 
        limit=limit, 
        offset=offset
    )

@mcp.tool()
async def get_coverage_area_tool(coverage_area_id: int) -> dict:
    """Get detailed information about a specific coverage area.
    
    This tool retrieves comprehensive information about a single coverage area
    including its geographic boundaries, resource count, and type-specific
    information such as radius for radius-based areas or FIPS codes for
    administrative areas.
    
    Args:
        coverage_area_id (int): The unique identifier of the coverage area to retrieve.
    
    Returns:
        dict: A dictionary containing:
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
    return await get_coverage_area(coverage_area_id)

@mcp.tool()
async def search_by_coverage_area_tool(
    coverage_area_id: int,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """Search for resources that cover a specific geographic area.
    
    This tool finds all resources that have been assigned to cover a specific
    coverage area. This is useful for finding all services available in a
    particular geographic region.
    
    Args:
        coverage_area_id (int): The unique identifier of the coverage area to search within.
        limit (int): Maximum number of results to return. Defaults to 50, max 100.
        offset (int): Number of results to skip for pagination. Defaults to 0.
    
    Returns:
        dict: A dictionary containing:
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
    return await search_resources_by_coverage_area(coverage_area_id, limit=limit, offset=offset)

@mcp.tool()
async def assign_coverage_area_to_resource_tool(
    resource_id: int,
    coverage_area_id: int,
    assigned_by_user_id: int = 1
) -> dict:
    """Assign a coverage area to a resource.
    
    This tool creates a relationship between a resource and a coverage area,
    indicating that the resource provides services within that geographic area.
    Resources can be assigned to multiple coverage areas.
    
    Args:
        resource_id (int): The unique identifier of the resource to assign.
        coverage_area_id (int): The unique identifier of the coverage area to assign.
        assigned_by_user_id (int): ID of the user making the assignment. Defaults to 1.
    
    Returns:
        dict: A dictionary containing:
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
    return await assign_coverage_area_to_resource(resource_id, coverage_area_id, assigned_by_user_id)

@mcp.tool()
async def remove_coverage_area_tool(
    resource_id: int,
    coverage_area_id: int,
    removed_by_user_id: int = 1
) -> dict:
    """Remove a coverage area assignment from a resource.
    
    This tool removes the relationship between a resource and a coverage area,
    indicating that the resource no longer provides services within that
    geographic area.
    
    Args:
        resource_id (int): The unique identifier of the resource.
        coverage_area_id (int): The unique identifier of the coverage area to remove.
        removed_by_user_id (int): ID of the user making the removal. Defaults to 1.
    
    Returns:
        dict: A dictionary containing:
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
    return await remove_coverage_area_from_resource(resource_id, coverage_area_id, removed_by_user_id)

@mcp.tool()
async def get_resource_coverage_areas_tool(resource_id: int) -> dict:
    """Get all coverage areas assigned to a resource.
    
    This tool retrieves all coverage areas that have been assigned to a specific
    resource, showing the complete geographic service area for that resource.
    
    Args:
        resource_id (int): The unique identifier of the resource.
    
    Returns:
        dict: A dictionary containing:
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
    return await get_resource_coverage_areas(resource_id)

@mcp.tool()
async def search_resources_by_point_tool(
    latitude: float,
    longitude: float,
    radius_miles: float = 25.0,
    limit: int = 50
) -> dict:
    """Search for resources within a radius of a specific geographic point.
    
    This tool performs spatial search to find resources within a specified radius
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
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable status message
            - data (dict): Contains:
                - search_point (dict): Search parameters (latitude, longitude, radius_miles)
                - resources (list): List of resources within the search radius
                - total_count (int): Total number of resources found
                - coverage_areas_searched (int): Number of coverage areas searched
              None if error
    
    Note:
        This tool uses a simplified distance calculation for radius-based areas.
        For production use with complex geometries, a full GIS implementation
        would be recommended.
    """
    return await search_resources_by_point(latitude, longitude, radius_miles, limit)

# Static Resources
@mcp.resource("resource://categories")
def categories_resource() -> dict:
    """Static resource providing all taxonomy categories.
    
    This static resource provides read-only access to all taxonomy categories
    in the system with their resource counts. This data is cached and updated
    when the resource is accessed.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - categories (list): List of all categories with id, name, slug,
                                   description, resource_count, created_at
                - total_count (int): Total number of categories
                - last_updated (str): ISO timestamp of last update
    """
    return get_categories_resource()

@mcp.resource("resource://service-types")
def service_types_resource() -> dict:
    """Static resource providing all service types.
    
    This static resource provides read-only access to all service types
    in the system with their resource counts. This data is cached and updated
    when the resource is accessed.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - service_types (list): List of all service types with id, name, slug,
                                      description, resource_count, created_at
                - total_count (int): Total number of service types
                - last_updated (str): ISO timestamp of last update
    """
    return get_service_types_resource()

@mcp.resource("resource://taxonomy-overview")
def taxonomy_overview_resource() -> dict:
    """Static resource providing taxonomy overview.
    
    This static resource provides a comprehensive overview of the taxonomy system
    including summary statistics and top categories and service types by resource count.
    
    Returns:
        dict: A dictionary containing:
            - status (str): "success" or "error"
            - data (dict): Contains:
                - summary (dict): Overall statistics including total_categories,
                                total_service_types, total_published_resources
                - top_categories (list): Top 10 categories by resource count
                - top_service_types (list): Top 10 service types by resource count
    """
    return get_taxonomy_overview_resource()

# Dynamic Resources
@mcp.resource("resource://resource/{resource_id}")
def resource_template(resource_id: int) -> dict:
    """Dynamic resource template for individual resources.
    
    This dynamic resource provides real-time access to a specific resource's
    complete information. The data is fetched fresh each time the resource
    is accessed, ensuring it's always up-to-date.
    
    Args:
        resource_id (int): The unique identifier of the resource to retrieve.
    
    Returns:
        dict: A dictionary containing:
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
    return get_resource_template(resource_id)

if __name__ == "__main__":
    # Run the server with stdio transport (default)
    mcp.run()
