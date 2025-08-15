"""
Directory Utils Package - Resource Directory Utility Functions

This package contains all the utility functions for the resource directory application,
organized into logical modules for better maintainability and code organization.

Utils are organized as follows:
    - export_utils.py: CSV export functionality
    - version_utils.py: Version comparison and diff generation
    - formatting_utils.py: Text formatting and display value functions
    - duplicate_utils.py: Duplicate detection logic
    - duplicate_resolution.py: Duplicate resolution and merging logic

This __init__.py file maintains backward compatibility by importing all utility functions
at the package level, so existing code can continue to use:
    from directory.utils import export_resources_to_csv, compare_versions

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    # Backward compatible imports (recommended for existing code)
    from directory.utils import export_resources_to_csv, compare_versions
    
    # Direct module imports (for new code)
    from directory.utils.export_utils import export_resources_to_csv
    from directory.utils.version_utils import compare_versions, generate_diff_html
    from directory.utils.formatting_utils import escape_html, format_field_name
    from directory.utils.duplicate_utils import DuplicateDetector
    from directory.utils.duplicate_resolution import DuplicateResolver
"""

# Import all utility functions for backward compatibility
from .export_utils import export_resources_to_csv
from .formatting_utils import escape_html, format_field_name, get_field_display_value
from .version_utils import compare_versions, generate_diff_html
from .duplicate_utils import DuplicateDetector
from .duplicate_resolution import DuplicateResolver

# Define __all__ for explicit exports
__all__ = [
    "export_resources_to_csv",
    "compare_versions",
    "generate_diff_html",
    "escape_html",
    "format_field_name",
    "get_field_display_value",
    "DuplicateDetector",
    "DuplicateResolver",
]
