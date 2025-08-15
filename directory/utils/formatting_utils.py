"""
Formatting Utilities - Text Formatting and Display Value Functions

This module contains utility functions for formatting text, field names, and
display values for the resource directory application. These functions provide
user-friendly formatting and safe HTML handling.

Functions:
    - escape_html: Escape HTML special characters
    - format_field_name: Format field names for display
    - get_field_display_value: Get formatted display values

Features:
    - HTML escaping to prevent XSS attacks
    - Field name formatting for user interfaces
    - Display value formatting with special case handling
    - Bootstrap-compatible HTML classes
    - Safe string conversion and handling

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.utils.formatting_utils import escape_html, format_field_name, get_field_display_value
    
    # Escape HTML
    safe_text = escape_html("<script>alert('xss')</script>")
    
    # Format field name
    formatted = format_field_name("last_verified_at")  # "Last Verified At"
    
    # Get display value
    display = get_field_display_value("draft", "status")  # "Draft"
"""

from typing import Any


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
