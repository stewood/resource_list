"""
Geographic Data Management Package

This package contains refactored geographic data management functionality
extracted from the original geo_manager.py file.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

# Import main manager for backward compatibility
from .manager import GeographicDataManager

__all__ = ['GeographicDataManager']
