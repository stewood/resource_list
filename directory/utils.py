"""
Resource Directory Utils - Utility Functions for Data Processing and Export

This module contains utility functions for the resource directory application,
providing data export capabilities, version comparison, diff generation, and
field formatting utilities. These functions support the core functionality
of resource management and data presentation.

Key Features:
    - CSV export functionality with comprehensive field mapping
    - Version comparison and diff generation
    - HTML diff highlighting for version changes
    - Field formatting and display value generation
    - HTML escaping for safe content display
    - Timestamp formatting and user-friendly display

Utility Functions:
    - export_resources_to_csv: Export resources to CSV format
    - compare_versions: Compare two resource snapshots
    - generate_diff_html: Generate HTML diff between text strings
    - escape_html: Escape HTML special characters
    - format_field_name: Format field names for display
    - get_field_display_value: Get formatted display values

Export Features:
    - Complete field mapping for all resource attributes
    - Special handling for related fields (category, service types)
    - User-friendly formatting for boolean and date fields
    - Timestamp-based filename generation
    - Proper CSV encoding and HTTP response handling

Version Comparison:
    - Side-by-side snapshot comparison
    - Diff type classification (added, removed, changed)
    - HTML diff generation with syntax highlighting
    - Safe HTML escaping for content display

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-08-15
Version: 1.0.0

Dependencies:
    - Python standard library: csv, difflib, io
    - Django: django.http.HttpResponse, django.utils.timezone
    - Typing: typing.Any, typing.Dict, typing.List

Usage:
    from directory.utils import export_resources_to_csv, compare_versions
    
    # Export resources to CSV
    response = export_resources_to_csv(Resource.objects.all())
    
    # Compare versions
    differences = compare_versions(snapshot1, snapshot2)

Examples:
    # Export filtered resources
    queryset = Resource.objects.filter(status='published')
    response = export_resources_to_csv(queryset, include_header=True)
    
    # Generate version diff
    diff_html = generate_diff_html("old text", "new text")
    
    # Format field name
    formatted = format_field_name("last_verified_at")  # "Last Verified At"
"""

import csv
import difflib
from io import StringIO
from typing import Any, Dict, List

from django.db import models
from django.http import HttpResponse
from django.utils import timezone


def export_resources_to_csv(queryset: models.QuerySet, include_header: bool = True) -> HttpResponse:
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
        'id': 'ID',
        # Basic information
        'name': 'Name',
        'category': 'Category',
        'description': 'Description',
        'status': 'Status',
        'source': 'Source',
        'notes': 'Notes',
        
        # Contact information
        'phone': 'Phone',
        'email': 'Email',
        'website': 'Website',
        
        # Location
        'address1': 'Address Line 1',
        'address2': 'Address Line 2',
        'city': 'City',
        'state': 'State',
        'county': 'County',
        'postal_code': 'Postal Code',
        
        # Operational fields
        'hours_of_operation': 'Hours of Operation',
        'is_emergency_service': 'Emergency Service',
        'is_24_hour_service': '24 Hour Service',
        'eligibility_requirements': 'Eligibility Requirements',
        'populations_served': 'Populations Served',
        'insurance_accepted': 'Insurance Accepted',
        'cost_information': 'Cost Information',
        'languages_available': 'Languages Available',
        'capacity': 'Capacity',
        
        # Verification
        'last_verified_at': 'Last Verified At',
        'last_verified_by': 'Last Verified By',
        
        # Metadata
        'created_at': 'Created At',
        'updated_at': 'Updated At',
        'created_by': 'Created By',
        'updated_by': 'Updated By',
        
        # Archive information
        'is_archived': 'Is Archived',
        'archived_at': 'Archived At',
        'archived_by': 'Archived By',
        'archive_reason': 'Archive Reason',
    }
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="resources_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header if requested
    if include_header:
        header = list(field_mapping.values()) + ['Service Types']
        writer.writerow(header)
    
    # Write data rows
    for resource in queryset:
        row = []
        for field_name in field_mapping.keys():
            value = getattr(resource, field_name, None)
            
            # Handle special cases
            if field_name == 'category' and value:
                value = value.name
            elif field_name == 'last_verified_by' and value:
                value = value.username
            elif field_name == 'created_by' and value:
                value = value.username
            elif field_name == 'updated_by' and value:
                value = value.username
            elif field_name == 'archived_by' and value:
                value = value.username
            elif field_name in ['last_verified_at', 'created_at', 'updated_at', 'archived_at'] and value:
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif field_name in ['is_emergency_service', 'is_24_hour_service', 'is_archived']:
                value = 'Yes' if value else 'No'
            
            # Convert to string, handling None values
            row.append(str(value) if value is not None else '')
        
        # Add service types as a separate column
        service_types = ', '.join([st.name for st in resource.service_types.all()])
        row.append(service_types)
        
        writer.writerow(row)
    
    return response


def compare_versions(
    snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Compare two resource snapshots and return detailed differences.
    
    This function performs a comprehensive comparison between two resource
    snapshots, identifying added, removed, and changed fields. It preserves
    original data types while providing both raw values and HTML-formatted
    diffs for display purposes.
    
    Features:
        - Complete field-by-field comparison
        - Diff type classification (added, removed, changed)
        - Preservation of original data types
        - HTML diff generation for display
        - Handling of missing fields in either snapshot
        
    Diff Types:
        - "added": Field exists in snapshot2 but not in snapshot1
        - "removed": Field exists in snapshot1 but not in snapshot2
        - "changed": Field exists in both but with different values
        
    Return Structure:
        {
            "field_name": {
                "old_value": original_value,
                "new_value": new_value,
                "diff_type": "added|removed|changed",
                "diff_html": HTML-formatted diff string
            }
        }
        
    Args:
        snapshot1: Dictionary containing the first version's field values
        snapshot2: Dictionary containing the second version's field values
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping field names to their differences,
                                  including old/new values, diff type, and HTML diff
                                  
    Example:
        >>> snapshot1 = {"name": "Old Name", "status": "draft"}
        >>> snapshot2 = {"name": "New Name", "status": "published", "city": "London"}
        >>> differences = compare_versions(snapshot1, snapshot2)
        >>> # Returns:
        >>> # {
        >>> #     "name": {"old_value": "Old Name", "new_value": "New Name", 
        >>> #              "diff_type": "changed", "diff_html": "..."},
        >>> #     "status": {"old_value": "draft", "new_value": "published", 
        >>> #                "diff_type": "changed", "diff_html": "..."},
        >>> #     "city": {"old_value": None, "new_value": "London", 
        >>> #             "diff_type": "added", "diff_html": "..."}
        >>> # }
    """
    differences = {}

    # Get all unique keys from both snapshots
    all_keys = set(snapshot1.keys()) | set(snapshot2.keys())

    for key in all_keys:
        value1 = snapshot1.get(key)
        value2 = snapshot2.get(key)

        # Compare values directly (preserve types)
        if value1 != value2:
            diff_type = "changed"
            if key not in snapshot1:
                diff_type = "added"
            elif key not in snapshot2:
                diff_type = "removed"

            # Convert to strings for diff_html generation
            str_value1 = str(value1) if value1 is not None else ""
            str_value2 = str(value2) if value2 is not None else ""

            differences[key] = {
                "old_value": value1,  # Preserve original type
                "new_value": value2,  # Preserve original type
                "diff_type": diff_type,
                "diff_html": generate_diff_html(str_value1, str_value2),
            }

    return differences


def generate_diff_html(old_text: str, new_text: str) -> str:
    """Generate HTML diff between two text strings with syntax highlighting.
    
    This function creates an HTML-formatted diff between two text strings using
    Python's difflib module. It provides visual highlighting for additions,
    deletions, and context lines, making it easy to see changes between versions.
    
    Features:
        - Unified diff format with line-by-line comparison
        - HTML highlighting for additions (green) and deletions (red)
        - Context preservation for better understanding
        - Safe HTML escaping to prevent XSS
        - Fallback for identical text
        - Bootstrap-compatible CSS classes
        
    CSS Classes Used:
        - diff-header: For diff metadata lines (@@ lines)
        - diff-added: For added lines (green highlighting)
        - diff-removed: For removed lines (red highlighting)
        - diff-context: For unchanged context lines
        - text-muted: For identical text or no diff available
        
    Args:
        old_text: Original text string to compare
        new_text: New text string to compare against
        
    Returns:
        str: HTML string with diff highlighting and proper escaping
        
    Example:
        >>> old_text = "Hello\nWorld"
        >>> new_text = "Hello\nBeautiful\nWorld"
        >>> html_diff = generate_diff_html(old_text, new_text)
        >>> # Returns HTML like:
        >>> # '<div class="diff-header">@@ -1,2 +1,3 @@</div>'
        >>> # '<div class="diff-context"> Hello</div>'
        >>> # '<div class="diff-added">+ Beautiful</div>'
        >>> # '<div class="diff-context"> World</div>'
    """
    if old_text == new_text:
        return f'<span class="text-muted">{escape_html(old_text)}</span>'

    # Split into lines for better diff
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    # Generate diff
    diff = difflib.unified_diff(
        old_lines, new_lines, fromfile="old", tofile="new", lineterm=""
    )

    # Convert diff to HTML
    html_lines = []
    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("@@"):
            html_lines.append(f'<div class="diff-header">{escape_html(line)}</div>')
        elif line.startswith("+"):
            html_lines.append(
                f'<div class="diff-added">+ {escape_html(line[1:])}</div>'
            )
        elif line.startswith("-"):
            html_lines.append(
                f'<div class="diff-removed">- {escape_html(line[1:])}</div>'
            )
        else:
            html_lines.append(f'<div class="diff-context"> {escape_html(line)}</div>')

    return (
        "\n".join(html_lines)
        if html_lines
        else '<span class="text-muted">No diff available</span>'
    )


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS attacks.
    
    This function converts HTML special characters to their corresponding
    HTML entities, making text safe for display in HTML contexts. It
    prevents cross-site scripting (XSS) attacks by ensuring that user
    input cannot be interpreted as HTML markup.
    
    Characters Escaped:
        - & -> &amp; (ampersand)
        - < -> &lt; (less than)
        - > -> &gt; (greater than)
        - " -> &quot; (double quote)
        - ' -> &#39; (single quote/apostrophe)
        
    Args:
        text: Text string to escape for HTML display
        
    Returns:
        str: HTML-escaped string safe for display
        
    Example:
        >>> text = '<script>alert("Hello")</script>'
        >>> escaped = escape_html(text)
        >>> print(escaped)
        '&lt;script&gt;alert(&quot;Hello&quot;)&lt;/script&gt;'
        
    Note:
        This function provides basic HTML escaping. For more complex
        scenarios, consider using Django's built-in template escaping
        or the html module from the standard library.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def format_field_name(field_name: str) -> str:
    """Format field name for user-friendly display.
    
    This function converts snake_case field names to Title Case for display
    purposes. It replaces underscores with spaces and capitalizes each word,
    making field names more readable in user interfaces.
    
    Features:
        - Converts snake_case to Title Case
        - Replaces underscores with spaces
        - Capitalizes each word
        - Preserves original string if no underscores found
        
    Args:
        field_name: Raw field name in snake_case format
        
    Returns:
        str: Formatted field name in Title Case
        
    Example:
        >>> format_field_name("last_verified_at")
        'Last Verified At'
        >>> format_field_name("is_emergency_service")
        'Is Emergency Service'
        >>> format_field_name("name")
        'Name'
        
    Note:
        This function is designed for simple snake_case to Title Case
        conversion. For more complex field name formatting, consider
        using Django's built-in field verbose_name attributes.
    """
    # Convert snake_case to Title Case
    return field_name.replace("_", " ").title()


def get_field_display_value(value: Any, field_name: str) -> str:
    """Get formatted display value for a field with special handling.
    
    This function provides user-friendly display values for field data,
    handling special cases like empty values, status fields, and other
    data types that benefit from custom formatting.
    
    Features:
        - Handles None and empty string values
        - Special formatting for status fields
        - User-friendly empty value display
        - Safe string conversion for other values
        - Bootstrap-compatible HTML classes
        
    Special Cases:
        - None/empty values: Display as "(empty)" with muted styling
        - Status field: Maps status values to user-friendly labels
        - Other fields: Convert to string representation
        
    Args:
        value: Field value to format for display
        field_name: Name of the field for special case handling
        
    Returns:
        str: Formatted display value, potentially with HTML markup
        
    Example:
        >>> get_field_display_value(None, "description")
        '<em class="text-muted">(empty)</em>'
        >>> get_field_display_value("draft", "status")
        'Draft'
        >>> get_field_display_value("Some text", "name")
        'Some text'
        
    Note:
        This function returns HTML markup for empty values to provide
        visual styling. When using in templates, ensure the output
        is marked as safe with the |safe filter.
    """
    if value is None or value == "":
        return '<em class="text-muted">(empty)</em>'

    # Special formatting for certain fields
    if field_name == "status":
        status_map = {
            "draft": "Draft",
            "needs_review": "Needs Review",
            "published": "Published",
        }
        return status_map.get(value, value)

    return str(value)
