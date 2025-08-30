"""
Resource Eligibility API Views

This module contains API views for checking resource eligibility for specific locations.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import Resource
from .base import BaseAPIView


@method_decorator(csrf_exempt, name='dispatch')
class ResourceEligibilityView(BaseAPIView):
    """API view for checking resource eligibility for a specific location.
    
    This view provides a RESTful endpoint for checking whether a specific
    resource serves a given location, including distance calculations and
    coverage area information.
    
    Endpoint: GET /api/resources/{id}/eligibility/
    
    Query Parameters:
        - lat: Latitude coordinate (required)
        - lon: Longitude coordinate (required)
        - address: Address string (optional, for display purposes)
        
    Response Format:
        {
            "resource_id": 123,
            "resource_name": "Crisis Intervention Center",
            "serves_location": true,
            "distance_miles": 2.5,
            "eligibility_reason": "Location is within Laurel County (COUNTY)",
            "coverage_areas": [
                {
                    "id": 156,
                    "name": "Laurel County",
                    "kind": "COUNTY",
                    "distance_miles": 0.0,
                    "contains_location": true
                }
            ]
        }
    """
    
    def get(self, request: HttpRequest, resource_id: int) -> JsonResponse:
        """Handle GET requests for resource eligibility checking.
        
        Args:
            request: HTTP request object
            resource_id: ID of the resource to check eligibility for
            
        Returns:
            JsonResponse: JSON response with eligibility information
        """
        try:
            # Get query parameters
            lat = request.GET.get('lat')
            lon = request.GET.get('lon')
            address = request.GET.get('address', '').strip()
            
            # Validate required parameters
            if not lat or not lon:
                return JsonResponse(
                    {'error': 'Both lat and lon parameters are required'},
                    status=400
                )
            
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return JsonResponse(
                    {'error': 'lat and lon must be valid numbers'},
                    status=400
                )
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return JsonResponse({'error': 'Invalid coordinates provided'}, status=400)
            
            # Check if resource exists
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return JsonResponse(
                    {'error': f'Resource with ID {resource_id} not found'},
                    status=404
                )
            
            # Calculate eligibility information
            eligibility_info = Resource.objects.calculate_resource_distance(
                resource_id, lat, lon
            )
            
            # Add address information if provided
            if address:
                eligibility_info['query_address'] = address
            
            return JsonResponse(eligibility_info)
            
        except ValueError as e:
            return JsonResponse({'error': f'Invalid parameter value: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
