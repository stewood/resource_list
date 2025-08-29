"""Utility modules for the directory application.

This package contains utility functions and classes for various
directory operations including geometry processing, data validation,
export utilities, version comparison, formatting, and other helper functions.

Modules:
    - geometry: Geometry processing utilities for coverage areas
    - export_utils: Data export and CSV generation functions
    - version_utils: Version comparison and diff generation functions
    - formatting_utils: Text formatting and display value functions
    - duplicate_utils: Duplicate detection and resolution utilities
"""

from django.conf import settings

# Only import geometry functions if GIS is enabled
if getattr(settings, "GIS_ENABLED", False):
    from .geometry import (
        GeometryProcessor,
        simplify_geometry,
        normalize_multipolygon,
        validate_coverage_geometry,
        optimize_for_display,
    )
else:
    # Create dummy functions for when GIS is disabled
    class GeometryProcessor:
        pass

    def simplify_geometry(*args, **kwargs):
        return None

    def normalize_multipolygon(*args, **kwargs):
        return None

    def validate_coverage_geometry(*args, **kwargs):
        return True

    def optimize_for_display(*args, **kwargs):
        return None


from .export_utils import export_resources_to_csv
from .version_utils import compare_versions, generate_diff_html
from .formatting_utils import escape_html, format_field_name, get_field_display_value
from .data_quality import (
    DataQualityChecker,
    validate_fips_codes,
    check_duplicate_coverage_areas,
    validate_name_consistency,
    comprehensive_quality_check,
)

__all__ = [
    "GeometryProcessor",
    "simplify_geometry",
    "normalize_multipolygon",
    "validate_coverage_geometry",
    "optimize_for_display",
    "export_resources_to_csv",
    "compare_versions",
    "generate_diff_html",
    "escape_html",
    "format_field_name",
    "get_field_display_value",
    "DataQualityChecker",
    "validate_fips_codes",
    "check_duplicate_coverage_areas",
    "validate_name_consistency",
    "comprehensive_quality_check",
]
