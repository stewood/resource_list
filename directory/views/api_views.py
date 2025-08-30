"""
API Views - Legacy Import File

This file provides backward compatibility by importing all API views
from the refactored api package structure.

All views have been moved to individual modules in the api/ directory:
- area_views.py: AreaSearchView
- location_views.py: LocationSearchView  
- resource_views.py: ResourceAreaManagementView
- eligibility_views.py: ResourceEligibilityView
- geocoding_views.py: ReverseGeocodingView
- state_county_views.py: StateCountyView

This file maintains backward compatibility for existing imports.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

# Import all views from the new api package structure
from .api import (
    AreaSearchView,
    LocationSearchView,
    ResourceAreaManagementView,
    ResourceEligibilityView,
    ReverseGeocodingView,
    StateCountyView,
)

__all__ = [
    'AreaSearchView',
    'LocationSearchView',
    'ResourceAreaManagementView',
    'ResourceEligibilityView',
    'ReverseGeocodingView',
    'StateCountyView',
]
