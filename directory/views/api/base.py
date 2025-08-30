"""
Base API Views and Utilities

This module contains common utilities, base classes, and shared functionality
for all API views in the refactored structure.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import CoverageArea, Resource
from ...services.geocoding import GeocodingResult


@method_decorator(csrf_exempt, name='dispatch')
class BaseAPIView(View):
    """Base class for all API views with common functionality.
    
    Provides common methods and utilities used across all API views
    including error handling, response formatting, and pagination.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_page_size = 20
        self.max_page_size = 100
    
    def create_error_response(self, message: str, status_code: int = 400, 
                            details: Optional[Dict] = None) -> JsonResponse:
        """Create a standardized error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
            
        Returns:
            JsonResponse with error information
        """
        response_data = {
            'error': True,
            'message': message,
            'status_code': status_code
        }
        
        if details:
            response_data['details'] = details
            
        return JsonResponse(response_data, status=status_code)
    
    def create_success_response(self, data: Any, status_code: int = 200) -> JsonResponse:
        """Create a standardized success response.
        
        Args:
            data: Response data
            status_code: HTTP status code
            
        Returns:
            JsonResponse with success data
        """
        return JsonResponse({
            'error': False,
            'data': data
        }, status=status_code)
    
    def paginate_results(self, queryset, request: HttpRequest, 
                        page_size: Optional[int] = None) -> Dict:
        """Paginate query results.
        
        Args:
            queryset: Django queryset to paginate
            request: HTTP request object
            page_size: Number of items per page
            
        Returns:
            Dictionary with paginated results and pagination info
        """
        if page_size is None:
            page_size = self.default_page_size
            
        page_size = min(page_size, self.max_page_size)
        page_number = request.GET.get('page', 1)
        
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1
            
        paginator = Paginator(queryset, page_size)
        
        try:
            page = paginator.page(page_number)
        except:
            page = paginator.page(1)
            
        return {
            'results': list(page.object_list),
            'pagination': {
                'page': page.number,
                'page_size': page_size,
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': page.has_next(),
                'has_previous': page.has_previous()
            }
        }
    
    def validate_json_request(self, request: HttpRequest) -> Optional[Dict]:
        """Validate and parse JSON request body.
        
        Args:
            request: HTTP request object
            
        Returns:
            Parsed JSON data or None if invalid
        """
        if not request.body:
            return None
            
        try:
            return json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return None
    
    def get_coverage_area_bounds(self, coverage_area: CoverageArea) -> Dict:
        """Get coverage area bounds in standardized format.
        
        Args:
            coverage_area: CoverageArea instance
            
        Returns:
            Dictionary with bounds information
        """
        if not coverage_area.geometry:
            return {}
            
        bounds = coverage_area.geometry.extent
        return {
            'north': bounds[3],
            'south': bounds[1], 
            'east': bounds[2],
            'west': bounds[0]
        }


def format_coverage_area_response(coverage_area: CoverageArea) -> Dict:
    """Format coverage area for API response.
    
    Args:
        coverage_area: CoverageArea instance
        
    Returns:
        Formatted dictionary for API response
    """
    return {
        'id': coverage_area.id,
        'name': coverage_area.name,
        'kind': coverage_area.kind,
        'ext_ids': coverage_area.ext_ids or {},
        'bounds': format_coverage_area_bounds(coverage_area),
        'created_at': coverage_area.created_at.isoformat() if coverage_area.created_at else None,
        'updated_at': coverage_area.updated_at.isoformat() if coverage_area.updated_at else None
    }


def format_coverage_area_bounds(coverage_area: CoverageArea) -> Dict:
    """Format coverage area bounds for API response.
    
    Args:
        coverage_area: CoverageArea instance
        
    Returns:
        Dictionary with bounds information
    """
    if not coverage_area.geometry:
        return {}
        
    bounds = coverage_area.geometry.extent
    return {
        'north': bounds[3],
        'south': bounds[1],
        'east': bounds[2], 
        'west': bounds[0]
    }
