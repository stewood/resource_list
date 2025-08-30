"""
State and County API Views

This module contains API views for retrieving states and counties data.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import CoverageArea
from .base import BaseAPIView


@method_decorator(csrf_exempt, name='dispatch')
class StateCountyView(BaseAPIView):
    """API view for getting states and counties for dropdowns.
    
    This view provides a RESTful endpoint for retrieving states and counties
    for use in location selection dropdowns.
    
    Endpoint: GET /api/location/states-counties/
    
    Query Parameters:
        - state_fips: State FIPS code (optional, for getting counties)
        
    Response Format:
        {
            "success": true,
            "states": [
                {
                    "id": 123,
                    "name": "Kentucky",
                    "ext_ids": {"state_fips": "21"}
                }
            ],
            "counties": [
                {
                    "id": 456,
                    "name": "Laurel County",
                    "ext_ids": {"state_fips": "21", "county_fips": "125"}
                }
            ]
        }
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Handle GET requests for states and counties.
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: JSON response with states and counties data
        """
        try:
            # Get all states
            states = CoverageArea.objects.filter(kind='STATE').order_by('name').values(
                'id', 'name', 'ext_ids'
            )
            
            # Get counties for a specific state if state_fips provided
            state_fips = request.GET.get('state_fips')
            counties = []
            
            if state_fips:
                counties = CoverageArea.objects.filter(
                    kind='COUNTY',
                    ext_ids__state_fips=state_fips
                ).order_by('name').values('id', 'name', 'ext_ids')
            
            return JsonResponse({
                'states': list(states),
                'counties': list(counties)
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
