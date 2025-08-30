"""
Directory Models Package - Resource Directory Data Models

This package contains all the data models for the resource directory application,
organized into logical modules for better maintainability and code organization.

Models are organized as follows:
    - core/: Core Resource and Taxonomy models
    - geographic/: Geographic and coverage area models
    - analytics/: Search analytics and audit models
    - managers/: Custom model managers for advanced querying

This __init__.py file maintains backward compatibility by importing all models
at the package level, so existing code can continue to use:
    from directory.models import Resource, TaxonomyCategory, ServiceType

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    # Backward compatible imports (recommended for existing code)
    from directory.models import Resource, TaxonomyCategory, ServiceType

    # Direct module imports (for new code)
    from directory.models.core import Resource
    from directory.models.core import TaxonomyCategory, ServiceType
    from directory.models.analytics import ResourceVersion, AuditLog
    from directory.models.managers import ResourceManager
"""

# Import all models for backward compatibility
from .analytics import AuditLog, ResourceVersion
from .core import Resource
from .core import ServiceType, TaxonomyCategory
from .geographic import CoverageArea
from .geographic import ResourceCoverage
from .geographic import GeocodingCache
from .analytics import LocationSearchLog, SearchAnalytics

# Import managers for direct access
from .managers import ResourceManager

# Define __all__ for explicit exports
__all__ = [
    "Resource",
    "TaxonomyCategory",
    "ServiceType",
    "ResourceVersion",
    "AuditLog",
    "CoverageArea",
    "ResourceCoverage",
    "GeocodingCache",
    "ResourceManager",
    "LocationSearchLog",
    "SearchAnalytics",
]
