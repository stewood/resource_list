"""
Location Search API Views

This module contains API views for location-based resource search functionality.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import logging
from typing import Dict, List

from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import Resource
from .base import BaseAPIView

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class LocationSearchView(BaseAPIView):
    """API view for location-based resource search.
    
    This view provides a RESTful endpoint for finding resources by location
    using address geocoding or coordinates. It integrates with the spatial
    query logic and geocoding service.
    
    Endpoint: GET /api/search/by-location/
    
    Query Parameters:
        - address: Address string to geocode and search
        - lat: Latitude coordinate (optional if address provided)
        - lon: Longitude coordinate (optional if address provided)
        - radius_miles: Search radius in miles (default: 10)
        - page: Page number for pagination
        - page_size: Number of results per page (default: 20)
        
    Response Format:
        {
            "location": {
                "address": "London, KY",
                "coordinates": [37.1283, -84.0836],
                "geocoded": true
            },
            "results": [
                {
                    "id": 1,
                    "name": "Crisis Intervention Center",
                    "description": "24/7 crisis intervention services",
                    "city": "London",
                    "state": "KY",
                    "coverage_areas": ["Kentucky", "Laurel County"],
                    "distance_miles": 0.5
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_count": 1,
                "total_pages": 1
            }
        }
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Handle GET requests for location-based search.
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: JSON response with search results and location info
        """
        try:
            # Get query parameters
            address = request.GET.get('address', '').strip()
            lat = request.GET.get('lat')
            lon = request.GET.get('lon')
            radius_miles = float(request.GET.get('radius_miles', 10))
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Validate parameters
            if not address and (not lat or not lon):
                return JsonResponse(
                    {'error': 'Either address or lat/lon coordinates must be provided'},
                    status=400
                )
            
            if radius_miles < 0.1 or radius_miles > 100:
                return JsonResponse(
                    {'error': 'Radius must be between 0.1 and 100 miles'},
                    status=400
                )
            
            # Determine search location
            if address:
                # Use address geocoding
                from ...services.geocoding import get_geocoding_service
                service = get_geocoding_service()
                geocode_result = service.geocode(address)
                
                if not geocode_result:
                    return JsonResponse(
                        {'error': f'Could not geocode address: {address}'},
                        status=400
                    )
                
                lat = geocode_result.latitude
                lon = geocode_result.longitude
                geocoded_address = geocode_result.address
                geocoded = True
            else:
                # Use provided coordinates
                lat = float(lat)
                lon = float(lon)
                geocoded_address = address or f"{lat}, {lon}"
                geocoded = False
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return JsonResponse({'error': 'Invalid coordinates provided'}, status=400)
            
            # Find resources by location
            resources = Resource.objects.find_resources_by_location(
                location=(lat, lon),
                radius_miles=radius_miles
            )
            
            # Apply pagination
            paginator = Paginator(resources, page_size)
            try:
                page_obj = paginator.page(page)
            except:
                return JsonResponse({'error': f'Invalid page number: {page}'}, status=400)
            
            # Build response data
            results = []
            for resource in page_obj:
                # Get coverage areas for this resource
                coverage_areas = []
                for area in resource.coverage_areas.all():
                    coverage_areas.append(area.name)
                
                # Calculate distance if available
                distance_miles = None
                if hasattr(resource, 'distance_miles'):
                    distance_miles = resource.distance_miles
                
                result_data = {
                    'id': resource.id,
                    'name': resource.name,
                    'description': resource.description,
                    'city': resource.city,
                    'state': resource.state,
                    'coverage_areas': coverage_areas,
                    'distance_miles': distance_miles,
                    'status': resource.status
                }
                results.append(result_data)
            
            # Build response
            response_data = {
                'location': {
                    'address': geocoded_address,
                    'coordinates': [lat, lon],
                    'geocoded': geocoded
                },
                'results': results,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': paginator.count,
                    'total_pages': paginator.num_pages
                }
            }

            # Add suggestions if requested
            if request.GET.get('suggestions') == 'true' and address:
                suggestions = self.get_address_suggestions(address)
                response_data['suggestions'] = suggestions
            
            return JsonResponse(response_data)
            
        except ValueError as e:
            return JsonResponse({'error': f'Invalid parameter value: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

    def get_address_suggestions(self, query: str) -> List[Dict[str, str]]:
        """Get address suggestions for autocomplete.
        
        Args:
            query: The address query string
            
        Returns:
            List of suggestion dictionaries with address and type
        """
        suggestions = []
        
        try:
            # Get popular cities from the database
            cities = Resource.objects.filter(
                city__icontains=query
            ).values_list('city', 'state').distinct()[:5]
            
            for city, state in cities:
                if city and state:
                    suggestions.append({
                        'address': f"{city}, {state}",
                        'type': 'City'
                    })
            
            # Add common Kentucky cities if query matches
            kentucky_cities = [
                'London', 'Lexington', 'Louisville', 'Bowling Green', 
                'Owensboro', 'Covington', 'Richmond', 'Georgetown'
            ]
            
            for city in kentucky_cities:
                if query.lower() in city.lower():
                    suggestions.append({
                        'address': f"{city}, KY",
                        'type': 'City'
                    })
            
            # Add state suggestions
            states = ['Kentucky', 'Tennessee', 'Ohio', 'Indiana', 'West Virginia', 'Virginia']
            for state in states:
                if query.lower() in state.lower():
                    suggestions.append({
                        'address': state,
                        'type': 'State'
                    })
            
            # Remove duplicates while preserving order
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion['address'] not in seen:
                    seen.add(suggestion['address'])
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:8]  # Limit to 8 suggestions
            
        except Exception as e:
            logger.error(f"Error getting address suggestions: {e}")
            return []
