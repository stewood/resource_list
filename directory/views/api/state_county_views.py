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
        - has_counties: Filter to only states that have county data (optional)

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
        """Handle GET requests for states, counties, and cities data.

        Args:
            request: HTTP request object

        Returns:
            JsonResponse: JSON response with states, counties, and cities data
        """
        try:
            # Check query parameters
            has_counties = request.GET.get('has_counties', '').lower() == 'true'
            has_cities = request.GET.get('has_cities', '').lower() == 'true'
            state_fips = request.GET.get('state_fips')

            # Get all states
            states_query = CoverageArea.objects.filter(kind='STATE')
            
            if has_counties:
                # Filter to only states that have county data
                states_with_counties = CoverageArea.objects.filter(
                    kind='COUNTY'
                ).values_list('ext_ids__state_fips', flat=True).distinct()
                
                states_query = states_query.filter(
                    ext_ids__state_fips__in=states_with_counties
                )
            elif has_cities:
                # Filter to only states that have city data
                states_with_cities = CoverageArea.objects.filter(
                    kind='CITY'
                ).values_list('ext_ids__state_fips', flat=True).distinct()

                states_query = states_query.filter(
                    ext_ids__state_fips__in=states_with_cities
                )

            states = states_query.order_by('name').values('id', 'name', 'ext_ids')
            
            # Get counties and cities for a specific state if state_fips provided
            counties = []
            cities = []

            if state_fips:
                counties = CoverageArea.objects.filter(
                    kind='COUNTY',
                    ext_ids__state_fips=state_fips
                ).order_by('name').values('id', 'name', 'ext_ids')

                cities = CoverageArea.objects.filter(
                    kind='CITY',
                    ext_ids__state_fips=state_fips
                ).order_by('name').values('id', 'name', 'ext_ids')

            return JsonResponse({
                'success': True,
                'states': list(states),
                'counties': list(counties),
                'cities': list(cities)
            })

        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
