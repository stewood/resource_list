"""
Directory Models Package - Resource Directory Data Models

This package contains all the data models for the resource directory application,
organized into logical modules for better maintainability and code organization.

Models are organized as follows:
    - resource.py: Core Resource model and related functionality
    - taxonomy.py: TaxonomyCategory and ServiceType models for classification
    - audit.py: ResourceVersion and AuditLog models for audit trails
    - managers.py: Custom model managers for advanced querying

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
    from directory.models.resource import Resource
    from directory.models.taxonomy import TaxonomyCategory, ServiceType
    from directory.models.audit import ResourceVersion, AuditLog
    from directory.models.managers import ResourceManager
"""

# Import all models for backward compatibility
from .audit import AuditLog, ResourceVersion
from .resource import Resource
from .taxonomy import ServiceType, TaxonomyCategory
from .coverage_area import CoverageArea
from .resource_coverage import ResourceCoverage
from .geocoding_cache import GeocodingCache
from .search_analytics import LocationSearchLog, SearchAnalytics

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
