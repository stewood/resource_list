"""
Core Models Package - Essential Resource Directory Models

This package contains the core models for the resource directory application:
- Resource: The main resource model
- TaxonomyCategory: Resource classification categories
- ServiceType: Types of services offered by resources

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0
"""

from .resource import Resource
from .taxonomy import TaxonomyCategory, ServiceType

__all__ = [
    "Resource",
    "TaxonomyCategory", 
    "ServiceType",
]
