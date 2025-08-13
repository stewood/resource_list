"""
Utility functions for the resource directory application.
"""

import difflib
from typing import Any, Dict, List, Tuple


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
        value1 = snapshot1.get(key, "")
        value2 = snapshot2.get(key, "")

        # Convert to strings for comparison
        str_value1 = str(value1) if value1 is not None else ""
        str_value2 = str(value2) if value2 is not None else ""

        if str_value1 != str_value2:
            diff_type = "changed"
            if key not in snapshot1:
                diff_type = "added"
            elif key not in snapshot2:
                diff_type = "removed"

            differences[key] = {
                "old_value": str_value1,
                "new_value": str_value2,
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
        else f'<span class="text-muted">No diff available</span>'
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
