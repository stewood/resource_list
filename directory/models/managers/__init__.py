"""
Model Managers Package - Custom QuerySet Managers

This package contains custom Django model managers:
- ResourceManager: Advanced search and filtering for Resource model

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0
"""

from .resource_managers import ResourceManager

__all__ = [
    "ResourceManager",
]
