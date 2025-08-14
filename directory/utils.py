"""
Utility functions for the resource directory application.
"""

import csv
import difflib
from io import StringIO
from typing import Any, Dict, List

from django.http import HttpResponse
from django.utils import timezone


def export_resources_to_csv(queryset, include_header=True):
    """
    Export resources to CSV format with all fields.
    
    Args:
        queryset: QuerySet of resources to export
        include_header: Whether to include header row
        
    Returns:
        HttpResponse with CSV content
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
    """
    Compare two resource snapshots and return differences.

    Args:
        snapshot1: First version snapshot
        snapshot2: Second version snapshot

    Returns:
        Dictionary of field differences with old/new values and diff type
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
    """
    Generate HTML diff between two text strings.

    Args:
        old_text: Original text
        new_text: New text

    Returns:
        HTML string with diff highlighting
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
    """
    Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        Escaped HTML string
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def format_field_name(field_name: str) -> str:
    """
    Format field name for display.

    Args:
        field_name: Raw field name

    Returns:
        Formatted field name
    """
    # Convert snake_case to Title Case
    return field_name.replace("_", " ").title()


def get_field_display_value(value: Any, field_name: str) -> str:
    """
    Get display value for a field.

    Args:
        value: Field value
        field_name: Field name

    Returns:
        Formatted display value
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
