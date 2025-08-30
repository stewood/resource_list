"""
Geocoding API Views

This module contains API views for geocoding functionality.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .base import BaseAPIView


@method_decorator(csrf_exempt, name='dispatch')
class ReverseGeocodingView(BaseAPIView):
    """API view for reverse geocoding coordinates to address.
    
    This view provides a RESTful endpoint for converting coordinates
    to human-readable addresses using the geocoding service.
    
    Endpoint: GET /api/geocode/reverse/
    
    Query Parameters:
        - lat: Latitude coordinate (required)
        - lon: Longitude coordinate (required)
        
    Response Format:
        {
            "success": true,
            "result": {
                "address": "London, Laurel County, Kentucky, United States",
                "latitude": 37.1283343,
                "longitude": -84.0835576,
                "confidence": 0.8,
                "provider": "nominatim"
            }
        }
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Handle GET requests for reverse geocoding.
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: JSON response with geocoding result
        """
        try:
            # Get query parameters
            lat = request.GET.get('lat')
            lon = request.GET.get('lon')
            
            # Validate required parameters
            if not lat or not lon:
                return self.create_error_response(
                    'Both lat and lon parameters are required',
                    400
                )
            
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return self.create_error_response(
                    'lat and lon must be valid numbers',
                    400
                )
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return self.create_error_response('Invalid coordinates provided', 400)
            
            # Use geocoding service for reverse geocoding
            from ...services.geocoding import get_geocoding_service
            
            service = get_geocoding_service()
            result = service.reverse_geocode(lat, lon)
            
            if result:
                return JsonResponse({
                    'result': {
                        'address': result.address,
                        'latitude': result.latitude,
                        'longitude': result.longitude,
                        'confidence': result.confidence,
                        'provider': result.provider
                    }
                })
            else:
                return JsonResponse(
                    {'error': 'Could not reverse geocode the provided coordinates'},
                    status=404
                )
                
        except ValueError as e:
            return JsonResponse({'error': f'Invalid parameter value: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
