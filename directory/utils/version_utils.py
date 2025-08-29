"""
Version Utilities - Version Comparison and Diff Generation Functions

This module contains utility functions for comparing resource versions and
generating diffs between different snapshots. These functions support the
audit trail and version history features of the resource directory.

Functions:
    - compare_versions: Compare two resource snapshots
    - generate_diff_html: Generate HTML diff between text strings

Features:
    - Complete field-by-field comparison
    - Diff type classification (added, removed, changed)
    - Preservation of original data types
    - HTML diff generation for display
    - Handling of missing fields in either snapshot
    - Safe HTML escaping to prevent XSS

Version Comparison:
    - Side-by-side snapshot comparison
    - Diff type classification (added, removed, changed)
    - HTML diff generation with syntax highlighting
    - Safe HTML escaping for content display

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.utils.version_utils import compare_versions, generate_diff_html

    # Compare versions
    differences = compare_versions(snapshot1, snapshot2)

    # Generate HTML diff
    diff_html = generate_diff_html("old text", "new text")
"""

import difflib
from typing import Any, Dict

from .formatting_utils import escape_html


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
