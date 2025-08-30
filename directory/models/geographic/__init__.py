"""
Geographic Models Package - Location and Coverage Models

This package contains models related to geographic data and coverage areas:
- CoverageArea: Geographic areas for resource coverage
- GeocodingCache: Cached geocoding results
- ResourceCoverage: Relationship between resources and coverage areas

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0
"""

from .coverage_area import CoverageArea
from .geocoding_cache import GeocodingCache
from .resource_coverage import ResourceCoverage

__all__ = [
    "CoverageArea",
    "GeocodingCache",
    "ResourceCoverage",
]
