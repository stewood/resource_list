"""
Export Utilities - Data Export and CSV Generation Functions

This module contains utility functions for exporting data from the resource
directory application, primarily focused on CSV export functionality with
comprehensive field mapping and formatting.

Functions:
    - export_resources_to_csv: Export resources to CSV format

Features:
    - Complete field mapping for all resource attributes
    - Special handling for related fields (category, service types, users)
    - User-friendly formatting for boolean and date fields
    - Timestamp-based filename generation
    - Proper CSV encoding and HTTP response handling
    - Optional header row inclusion

Export Features:
    - Complete field mapping for all resource attributes
    - Special handling for related fields (category, service types)
    - User-friendly formatting for boolean and date fields
    - Timestamp-based filename generation
    - Proper CSV encoding and HTTP response handling

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.utils.export_utils import export_resources_to_csv

    # Export resources to CSV
    response = export_resources_to_csv(Resource.objects.all())
"""

import csv
from typing import Any

from django.db import models
from django.http import HttpResponse
from django.utils import timezone


def export_resources_to_csv(
    queryset: models.QuerySet, include_header: bool = True
) -> HttpResponse:
    """Export resources to CSV format with comprehensive field mapping and formatting.

    This function exports a queryset of resources to CSV format with complete
    field coverage including basic information, contact details, location data,
    operational fields, verification metadata, and archive information. It handles
    special cases for related fields and provides user-friendly formatting.

    Features:
        - Complete field mapping for all resource attributes
        - Special handling for related fields (category, service types, users)
        - User-friendly formatting for boolean and date fields
        - Timestamp-based filename generation
        - Proper CSV encoding and HTTP response handling
        - Optional header row inclusion

    Field Mapping:
        - Basic Info: ID, name, category, description, status, source, notes
        - Contact: phone, email, website
        - Location: address1, address2, city, state, county, postal_code
        - Operational: hours, emergency, 24-hour, eligibility, populations, insurance, cost, languages, capacity
        - Verification: last_verified_at, last_verified_by
        - Metadata: created_at, updated_at, created_by, updated_by
        - Archive: is_archived, archived_at, archived_by, archive_reason
        - Service Types: comma-separated list of service type names

    Special Handling:
        - Category: Display category name instead of ID
        - Service Types: Comma-separated list in separate column
        - User Fields: Display username instead of ID
        - Date Fields: Formatted as YYYY-MM-DD HH:MM:SS
        - Boolean Fields: Display as "Yes"/"No"
        - None Values: Display as empty string

    Args:
        queryset: QuerySet of Resource objects to export
        include_header: Whether to include header row with field names (default: True)

    Returns:
        HttpResponse: CSV file response with proper content type and filename

    Raises:
        AttributeError: If queryset contains objects without expected attributes

    Example:
        >>> from directory.models import Resource
        >>> queryset = Resource.objects.filter(status='published')
        >>> response = export_resources_to_csv(queryset)
        >>> # Returns HttpResponse with CSV content and filename like:
        >>> # "resources_export_20240815_143022.csv"
    """
    # Define all fields to export (excluding history/version fields)
    field_mapping = {
        # ID
        "id": "ID",
        # Basic information
        "name": "Name",
        "category": "Category",
        "description": "Description",
        "status": "Status",
        "source": "Source",
        "notes": "Notes",
        # Contact information
        "phone": "Phone",
        "email": "Email",
        "website": "Website",
        # Location
        "address1": "Address Line 1",
        "address2": "Address Line 2",
        "city": "City",
        "state": "State",
        "county": "County",
        "postal_code": "Postal Code",
        # Operational fields
        "hours_of_operation": "Hours of Operation",
        "is_emergency_service": "Emergency Service",
        "is_24_hour_service": "24 Hour Service",
        "eligibility_requirements": "Eligibility Requirements",
        "populations_served": "Populations Served",
        "insurance_accepted": "Insurance Accepted",
        "cost_information": "Cost Information",
        "languages_available": "Languages Available",
        "capacity": "Capacity",
        # Verification
        "last_verified_at": "Last Verified At",
        "last_verified_by": "Last Verified By",
        # Metadata
        "created_at": "Created At",
        "updated_at": "Updated At",
        "created_by": "Created By",
        "updated_by": "Updated By",
        # Archive information
        "is_archived": "Is Archived",
        "archived_at": "Archived At",
        "archived_by": "Archived By",
        "archive_reason": "Archive Reason",
    }

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="resources_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )

    # Create CSV writer
    writer = csv.writer(response)

    # Write header if requested
    if include_header:
        header = list(field_mapping.values()) + ["Service Types"]
        writer.writerow(header)

    # Write data rows
    for resource in queryset:
        row = []
        for field_name in field_mapping.keys():
            value = getattr(resource, field_name, None)

            # Handle special cases
            if field_name == "category" and value:
                value = value.name
            elif field_name == "last_verified_by" and value:
                value = value.username
            elif field_name == "created_by" and value:
                value = value.username
            elif field_name == "updated_by" and value:
                value = value.username
            elif field_name == "archived_by" and value:
                value = value.username
            elif (
                field_name
                in ["last_verified_at", "created_at", "updated_at", "archived_at"]
                and value
            ):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif field_name in [
                "is_emergency_service",
                "is_24_hour_service",
                "is_archived",
            ]:
                value = "Yes" if value else "No"

            # Convert to string, handling None values
            row.append(str(value) if value is not None else "")

        # Add service types as a separate column
        service_types = ", ".join([st.name for st in resource.service_types.all()])
        row.append(service_types)

        writer.writerow(row)

    return response
