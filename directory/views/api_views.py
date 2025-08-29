"""
API Views - Coverage Area Management and Search APIs

This module contains Django REST Framework views for coverage area management
and location-based search functionality. These views provide RESTful API
endpoints for area search, radius creation, polygon creation, and resource
coverage association.

Key Views:
    - AreaSearchView: Search coverage areas by kind and name
    - RadiusCreationView: Create radius-based coverage areas
    - PolygonCreationView: Create custom polygon coverage areas
    - ResourceAreaManagementView: Manage resource-coverage associations

Features:
    - RESTful API design with proper HTTP methods
    - JSON request/response format
    - Pagination for large result sets
    - Authentication and permission controls
    - Input validation and error handling
    - Integration with spatial query logic

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django REST Framework
    - django.contrib.gis for spatial operations
    - directory.models for data access
    - directory.services.geocoding for geocoding functionality

Usage:
    from directory.views.api_views import AreaSearchView
    
    # URL patterns typically map to these views
    # GET /api/areas/search/ -> AreaSearchView
    # POST /api/areas/radius/ -> RadiusCreationView
    # POST /api/areas/polygon/ -> PolygonCreationView
    # POST /api/resources/{id}/areas/ -> ResourceAreaManagementView
"""

import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from ..models import CoverageArea, Resource
from ..services.geocoding import GeocodingResult


@method_decorator(csrf_exempt, name='dispatch')
class AreaSearchView(View):
    """API view for searching coverage areas.
    
    This view provides a RESTful endpoint for searching coverage areas by
    kind (STATE, COUNTY, CITY, etc.) and name. It supports pagination and
    returns JSON responses with coverage area details.
    
    Endpoint: GET /api/areas/search/
    
    Query Parameters:
        - kind: Coverage area kind (STATE, COUNTY, CITY, POLYGON, RADIUS)
        - q: Search query for area names
        - page: Page number for pagination
        - page_size: Number of results per page (default: 20)
        
    Response Format:
        {
            "results": [
                {
                    "id": 1,
                    "name": "Kentucky",
                    "kind": "STATE",
                    "ext_ids": {"state_fips": "21", "state_name": "Kentucky"},
                    "bounds": {"north": 39.1, "south": 36.5, "east": -81.9, "west": -89.6}
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
    
    def get(self, request: HttpRequest, area_id: int = None) -> JsonResponse:
        """Handle GET requests for area search and preview.
        
        Args:
            request: HTTP request object
            area_id: Optional area ID from URL pattern
            
        Returns:
            JsonResponse: JSON response with search results and pagination
        """
        try:
            # Check if this is a request for specific area geometry or preview
            area_id = area_id or request.GET.get('id')
            if area_id:
                # Check if this is a preview request (either by URL or parameter)
                is_preview = (
                    request.GET.get('preview', 'false').lower() == 'true' or
                    'preview' in request.path
                )
                if is_preview:
                    return self._get_area_preview(str(area_id))
                else:
                    return self._get_area_geometry(str(area_id))
            
            # Get query parameters
            kind = request.GET.get('kind', '').upper()
            search_query = request.GET.get('q', '').strip()
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Validate parameters
            if page < 1:
                return JsonResponse(
                    {'error': 'Page number must be greater than 0'}, 
                    status=400
                )
            if page_size < 1 or page_size > 100:
                return JsonResponse(
                    {'error': 'Page size must be between 1 and 100'}, 
                    status=400
                )
            
            # Build queryset
            queryset = CoverageArea.objects.all()
            
            # Filter by kind if specified
            if kind:
                if kind not in dict(CoverageArea.KIND_CHOICES):
                    return JsonResponse(
                        {'error': f'Invalid kind: {kind}. Valid kinds: {list(dict(CoverageArea.KIND_CHOICES).keys())}'}, 
                        status=400
                    )
                queryset = queryset.filter(kind=kind)
            
            # Filter by search query if specified
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(ext_ids__state_name__icontains=search_query) |
                    Q(ext_ids__county_name__icontains=search_query)
                )
            
            # Order by name
            queryset = queryset.order_by('name')
            
            # Paginate results
            paginator = Paginator(queryset, page_size)
            try:
                page_obj = paginator.page(page)
            except Exception as e:
                return JsonResponse(
                    {'error': f'Invalid page number: {str(e)}'}, 
                    status=400
                )
            
            # Build response data
            results = []
            for area in page_obj:
                area_data = {
                    'id': area.id,
                    'name': area.name,
                    'kind': area.kind,
                    'ext_ids': area.ext_ids or {},
                }
                
                # Add bounds if geometry is available
                if area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                    try:
                        bounds = area.geom.extent
                        area_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                    except Exception:
                        # If bounds calculation fails, omit bounds
                        pass
                
                results.append(area_data)
            
            # Build pagination info
            pagination = {
                'page': page,
                'page_size': page_size,
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
            
            response_data = {
                'results': results,
                'pagination': pagination
            }
            
            return JsonResponse(response_data)
            
        except ValueError as e:
            return JsonResponse(
                {'error': f'Invalid parameter value: {str(e)}'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )

    def _get_area_preview(self, area_id: str) -> JsonResponse:
        """Get simplified preview data for a coverage area.
        
        This endpoint returns optimized data for map display including:
        - Simplified geometry for performance
        - Bounds for map fitting
        - Center point for map positioning
        - Basic area information
        
        Args:
            area_id: ID of the coverage area
            
        Returns:
            JsonResponse: JSON response with preview data
        """
        try:
            # Get the coverage area
            try:
                area = CoverageArea.objects.get(id=area_id)
            except CoverageArea.DoesNotExist:
                return JsonResponse(
                    {'error': f'Coverage area with ID {area_id} not found'}, 
                    status=404
                )
            
            # Build preview data
            preview_data = {
                'id': area.id,
                'name': area.name,
                'kind': area.kind,
                'type': area.kind.lower(),  # For frontend compatibility
            }
            
            # Handle national coverage areas specially
            if area.name in ['National (Lower 48 States)', 'United States (All States and Territories)']:
                # Provide appropriate bounds and center for United States
                preview_data['bounds'] = {
                    'west': -125.0,  # West coast
                    'south': 24.0,   # Southern border
                    'east': -66.0,   # East coast
                    'north': 49.0    # Northern border
                }
                preview_data['center'] = [39.8283, -98.5795]  # Center of continental US
                preview_data['is_national'] = True
                preview_data['description'] = 'National coverage area - serves entire United States'
                
            # Add geometry and spatial data if available
            elif area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                try:
                    # Get simplified geometry
                    simplified_geom = self._get_simplified_geometry(area.geom)
                    preview_data['geometry'] = simplified_geom
                    
                    # Add bounds for map fitting
                    bounds = area.geom.extent
                    preview_data['bounds'] = {
                        'west': bounds[0],
                        'south': bounds[1],
                        'east': bounds[2],
                        'north': bounds[3]
                    }
                    
                    # Add center point for map positioning
                    center = area.geom.centroid
                    preview_data['center'] = [center.y, center.x]  # lat, lng
                    
                    # Add area statistics
                    preview_data['area_sq_miles'] = self._calculate_area_sq_miles(area.geom)
                    
                except Exception as e:
                    return JsonResponse(
                        {'error': f'Error processing geometry: {str(e)}'}, 
                        status=500
                    )
            else:
                # Fallback to center point if no geometry
                if area.center:
                    try:
                        # Handle case where center might be stored as string
                        if hasattr(area.center, 'y') and hasattr(area.center, 'x'):
                            preview_data['center'] = [area.center.y, area.center.x]  # lat, lng
                    except Exception:
                        # Skip center if there's any error accessing it
                        pass
                
                # Add bounds if available
                if area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                    try:
                        bounds = area.geom.extent
                        preview_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                    except Exception:
                        pass
            
            return JsonResponse(preview_data)
            
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )

    def _calculate_area_sq_miles(self, geometry) -> float:
        """Calculate area in square miles.
        
        Args:
            geometry: Django GEOS geometry object
            
        Returns:
            float: Area in square miles
        """
        try:
            # Calculate area in square meters
            area_sq_meters = geometry.area
            
            # Convert to square miles (1 sq mile = 2,589,988.11 sq meters)
            area_sq_miles = area_sq_meters / 2589988.11
            
            return round(area_sq_miles, 2)
        except Exception:
            return 0.0
    
    def _get_area_geometry(self, area_id: str) -> JsonResponse:
        """Get the geometry for a specific coverage area.
        
        Args:
            area_id: ID of the coverage area
            
        Returns:
            JsonResponse: JSON response with area geometry
        """
        try:
            # Get the coverage area
            try:
                area = CoverageArea.objects.get(id=area_id)
            except CoverageArea.DoesNotExist:
                return JsonResponse(
                    {'error': f'Coverage area with ID {area_id} not found'}, 
                    status=404
                )
            
            # Check if this is a preview request
            is_preview = request.GET.get('preview', 'false').lower() == 'true'
            
            # Build response data
            area_data = {
                'id': area.id,
                'name': area.name,
                'kind': area.kind,
                'ext_ids': area.ext_ids or {},
            }
            
            # Add geometry if available
            if area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                try:
                    if is_preview:
                        # Return simplified geometry for preview
                        simplified_geom = self._get_simplified_geometry(area.geom)
                        area_data['geometry'] = simplified_geom
                    else:
                        # Return full geometry
                        geojson = area.geom.json
                        area_data['geometry'] = json.loads(geojson)
                    
                    # Add bounds
                    bounds = area.geom.extent
                    area_data['bounds'] = {
                        'west': bounds[0],
                        'south': bounds[1],
                        'east': bounds[2],
                        'north': bounds[3]
                    }
                    
                    # Add center point for map fitting
                    center = area.geom.centroid
                    area_data['center'] = [center.y, center.x]  # lat, lng
                    
                except Exception as e:
                    return JsonResponse(
                        {'error': f'Error processing geometry: {str(e)}'}, 
                        status=500
                    )
            else:
                # Fallback to center point if no geometry
                if area.center:
                    try:
                        # Handle case where center might be stored as string
                        if hasattr(area.center, 'y') and hasattr(area.center, 'x'):
                            area_data['center'] = [area.center.y, area.center.x]  # lat, lng
                    except Exception:
                        # Skip center if there's any error accessing it
                        pass
                
                # Add bounds if available
                if area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                    try:
                        bounds = area.geom.extent
                        area_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                    except Exception:
                        pass
            
            return JsonResponse(area_data)
            
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )

    def _get_simplified_geometry(self, geometry) -> dict:
        """Get simplified geometry for preview display.
        
        This method simplifies complex geometries to improve performance
        for map display while maintaining visual accuracy.
        
        Args:
            geometry: Django GEOS geometry object
            
        Returns:
            dict: Simplified GeoJSON geometry
        """
        try:
            # Simplify geometry based on complexity
            if geometry.num_coords > 100:
                # Use tolerance-based simplification for complex geometries
                tolerance = 0.001  # Adjust based on coordinate system
                simplified = geometry.simplify(tolerance, preserve_topology=True)
            else:
                # Keep original geometry for simple shapes
                simplified = geometry
            
            # Convert to GeoJSON
            geojson = simplified.json
            return json.loads(geojson)
            
        except Exception:
            # Fallback to original geometry if simplification fails
            geojson = geometry.json
            return json.loads(geojson)
    
    def post(self, request: HttpRequest) -> JsonResponse:
        """Handle POST requests for coverage area creation.
        
        This method creates new coverage areas from either:
        1. Radius-based areas: center point and radius
        2. Polygon-based areas: GeoJSON Feature with polygon geometry
        
        Request Body for Radius:
            {
                "type": "radius",
                "center": [latitude, longitude],
                "radius_miles": 10.0,
                "name": "Custom Service Area"
            }
            
        Request Body for Polygon:
            {
                "type": "polygon",
                "name": "Custom Polygon Area",
                "geometry": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
                    }
                }
            }
            
        Response Format:
            {
                "id": 1,
                "name": "Custom Service Area",
                "kind": "RADIUS" or "POLYGON",
                "center": [37.1283, -84.0836],
                "radius_miles": 10.0,  # Only for radius
                "ext_ids": {},
                "bounds": {"north": 37.2, "south": 37.0, "east": -84.0, "west": -84.2}
            }
        """
        try:
            # Parse JSON request body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Invalid JSON in request body'}, 
                    status=400
                )
            
            # Extract and validate common parameters
            area_type = data.get('type', 'radius').lower()
            name = data.get('name', '').strip()
            
            # Validate required parameters
            if not name:
                return JsonResponse(
                    {'error': 'name is required'}, 
                    status=400
                )
            
            # Validate area type
            if area_type not in ['radius', 'polygon']:
                return JsonResponse(
                    {'error': 'type must be either "radius" or "polygon"'}, 
                    status=400
                )
            
            # Handle radius-based area creation
            if area_type == 'radius':
                return self._create_radius_area(data, name)
            # Handle polygon-based area creation
            elif area_type == 'polygon':
                return self._create_polygon_area(data, name)
            
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )
    
    def _create_radius_area(self, data: Dict, name: str) -> JsonResponse:
        """Create a radius-based coverage area.
        
        Args:
            data: Request data containing center and radius
            name: Area name
            
        Returns:
            JsonResponse: Created area data or error
        """
        try:
            # Extract radius-specific parameters
            center = data.get('center')
            radius_miles = data.get('radius_miles')
            
            # Validate required parameters
            if not center or not isinstance(center, list) or len(center) != 2:
                return JsonResponse(
                    {'error': 'center must be a list with [latitude, longitude]'}, 
                    status=400
                )
            
            if not radius_miles or not isinstance(radius_miles, (int, float)):
                return JsonResponse(
                    {'error': 'radius_miles must be a number'}, 
                    status=400
                )
            
            # Extract coordinates
            lat, lon = center
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return JsonResponse(
                    {'error': 'Invalid coordinates: latitude must be -90 to 90, longitude must be -180 to 180'}, 
                    status=400
                )
            
            # Validate radius
            if radius_miles < 0.5 or radius_miles > 100:
                return JsonResponse(
                    {'error': 'radius_miles must be between 0.5 and 100 miles'}, 
                    status=400
                )
            
            # Check if GIS is enabled
            if not getattr(settings, 'GIS_ENABLED', False):
                return JsonResponse(
                    {'error': 'GIS functionality is not enabled'}, 
                    status=503
                )
            
            # Create radius-based coverage area
            try:
                from django.contrib.gis.geos import Point
                from django.contrib.gis.geos import GEOSGeometry
                
                # Create center point
                center_point = Point(lon, lat, srid=4326)
                
                # Convert radius to meters
                radius_meters = radius_miles * 1609.34
                
                # Create buffer polygon
                buffer_polygon = center_point.buffer(radius_meters / 111320.0)  # Approximate degrees
                
                # Convert to MultiPolygon if needed
                if buffer_polygon.geom_type == 'Polygon':
                    from django.contrib.gis.geos import MultiPolygon
                    buffer_polygon = MultiPolygon([buffer_polygon])
                
                # Get or create default user for API operations
                from django.contrib.auth.models import User
                default_user, created = User.objects.get_or_create(
                    username="api_user",
                    defaults={
                        "email": "api@example.com",
                        "first_name": "API",
                        "last_name": "User",
                    }
                )
                
                # Create CoverageArea record
                coverage_area = CoverageArea.objects.create(
                    kind="RADIUS",
                    name=name,
                    geom=buffer_polygon,
                    center=center_point,
                    radius_m=radius_meters,
                    ext_ids={
                        "center_lat": lat,
                        "center_lon": lon,
                        "radius_miles": radius_miles,
                        "created_via": "api"
                    },
                    created_by=default_user,
                    updated_by=default_user,
                )
                
                # Build response data
                response_data = {
                    'id': coverage_area.id,
                    'name': coverage_area.name,
                    'kind': coverage_area.kind,
                    'center': [lat, lon],
                    'radius_miles': radius_miles,
                    'ext_ids': coverage_area.ext_ids,
                }
                
                # Add bounds if geometry is available
                if coverage_area.geom:
                    try:
                        bounds = coverage_area.geom.extent
                        response_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                    except Exception:
                        # If bounds calculation fails, omit bounds
                        pass
                
                return JsonResponse(response_data, status=201)
                
            except ImportError:
                return JsonResponse(
                    {'error': 'GIS libraries not available'}, 
                    status=503
                )
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error creating coverage area: {str(e)}'}, 
                    status=500
                )
                
        except Exception as e:
            return JsonResponse(
                {'error': f'Error creating radius area: {str(e)}'}, 
                status=500
            )
    
    def _create_polygon_area(self, data: Dict, name: str) -> JsonResponse:
        """Create a polygon-based coverage area.
        
        Args:
            data: Request data containing GeoJSON geometry
            name: Area name
            
        Returns:
            JsonResponse: Created area data or error
        """
        try:
            # Extract polygon-specific parameters
            geometry_data = data.get('geometry')
            
            # Validate required parameters
            if not geometry_data:
                return JsonResponse(
                    {'error': 'geometry is required for polygon areas'}, 
                    status=400
                )
            
            # Check if GIS is enabled
            if not getattr(settings, 'GIS_ENABLED', False):
                return JsonResponse(
                    {'error': 'GIS functionality is not enabled'}, 
                    status=503
                )
            
            # Create polygon-based coverage area
            try:
                from django.contrib.gis.geos import GEOSGeometry, Point
                
                # Parse GeoJSON geometry
                if isinstance(geometry_data, str):
                    # If geometry is a string, parse it as GeoJSON
                    geojson_str = geometry_data
                elif isinstance(geometry_data, dict):
                    # If geometry is a dict, convert to GeoJSON string
                    import json
                    geojson_str = json.dumps(geometry_data)
                else:
                    return JsonResponse(
                        {'error': 'geometry must be a GeoJSON string or object'}, 
                        status=400
                    )
                
                # Create GEOS geometry from GeoJSON
                try:
                    geos_geometry = GEOSGeometry(geojson_str)
                except Exception as e:
                    return JsonResponse(
                        {'error': f'Invalid GeoJSON geometry: {str(e)}'}, 
                        status=400
                    )
                
                # Validate geometry type
                if geos_geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                    return JsonResponse(
                        {'error': f'Geometry must be Polygon or MultiPolygon, got {geos_geometry.geom_type}'}, 
                        status=400
                    )
                
                # Validate geometry
                if not geos_geometry.valid:
                    return JsonResponse(
                        {'error': 'Invalid geometry: self-intersecting or malformed polygon'}, 
                        status=400
                    )
                
                # Ensure SRID is 4326 (WGS84)
                if geos_geometry.srid != 4326:
                    geos_geometry.srid = 4326
                
                # Convert to MultiPolygon if needed
                if geos_geometry.geom_type == 'Polygon':
                    from django.contrib.gis.geos import MultiPolygon
                    geos_geometry = MultiPolygon([geos_geometry])
                
                # Calculate center point
                center_point = geos_geometry.centroid
                
                # Get or create default user for API operations
                from django.contrib.auth.models import User
                default_user, created = User.objects.get_or_create(
                    username="api_user",
                    defaults={
                        "email": "api@example.com",
                        "first_name": "API",
                        "last_name": "User",
                    }
                )
                
                # Create CoverageArea record
                coverage_area = CoverageArea.objects.create(
                    kind="POLYGON",
                    name=name,
                    geom=geos_geometry,
                    center=center_point,
                    ext_ids={
                        "created_via": "api",
                        "geometry_type": geos_geometry.geom_type,
                        "vertex_count": len(geos_geometry.coords[0]) if geos_geometry.geom_type == 'Polygon' else sum(len(poly.coords[0]) for poly in geos_geometry)
                    },
                    created_by=default_user,
                    updated_by=default_user,
                )
                
                # Build response data
                response_data = {
                    'id': coverage_area.id,
                    'name': coverage_area.name,
                    'kind': coverage_area.kind,
                    'center': [center_point.y, center_point.x],  # lat, lon
                    'ext_ids': coverage_area.ext_ids,
                }
                
                # Add bounds if geometry is available
                if coverage_area.geom:
                    try:
                        bounds = coverage_area.geom.extent
                        response_data['bounds'] = {
                            'west': bounds[0],
                            'south': bounds[1],
                            'east': bounds[2],
                            'north': bounds[3]
                        }
                    except Exception:
                        # If bounds calculation fails, omit bounds
                        pass
                
                return JsonResponse(response_data, status=201)
                
            except ImportError:
                return JsonResponse(
                    {'error': 'GIS libraries not available'}, 
                    status=503
                )
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error creating coverage area: {str(e)}'}, 
                    status=500
                )
                
        except Exception as e:
            return JsonResponse(
                {'error': f'Error creating polygon area: {str(e)}'}, 
                status=500
            )


@method_decorator(csrf_exempt, name='dispatch')
class LocationSearchView(View):
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
                from ..services.geocoding import get_geocoding_service
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
                return JsonResponse(
                    {'error': 'Invalid coordinates provided'}, 
                    status=400
                )
            
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
                return JsonResponse(
                    {'error': f'Invalid page number: {page}'}, 
                    status=400
                )
            
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
            return JsonResponse(
                {'error': f'Invalid parameter value: {str(e)}'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )

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
            from ..models import Resource
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


@method_decorator(csrf_exempt, name='dispatch')
class ResourceAreaManagementView(View):
    """API view for managing resource-coverage area associations.
    
    This view provides a RESTful endpoint for attaching and detaching coverage
    areas to/from resources. It includes proper validation, audit trail, and
    permission controls.
    
    Endpoint: POST /api/resources/{id}/areas/ (requires authentication)
    Endpoint: GET /api/resources/{id}/areas/ (public read access)
    
    Request Body:
        {
            "action": "attach" | "detach",
            "coverage_area_ids": [1, 2, 3],
            "notes": "Optional notes about the association"
        }
        
    Response Format:
        {
            "success": true,
            "message": "Areas attached successfully",
            "attached_count": 2,
            "detached_count": 1,
            "errors": []
        }
    """
    
    def post(self, request: HttpRequest, resource_id: int) -> JsonResponse:
        """Handle POST requests for resource area management.
        
        Args:
            request: HTTP request object
            resource_id: ID of the resource to manage areas for
            
        Returns:
            JsonResponse: JSON response with operation results
        """
        # Check authentication for POST operations
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required for this operation'}, 
                status=401
            )
        
        try:
            # Get the resource
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return JsonResponse(
                    {'error': f'Resource with ID {resource_id} not found'}, 
                    status=404
                )
            
            # Parse request data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Invalid JSON in request body'}, 
                    status=400
                )
            
            action = data.get('action', '').lower()
            coverage_area_ids = data.get('coverage_area_ids', [])
            notes = data.get('notes', '')
            
            # Validate action
            if action not in ['attach', 'detach', 'replace']:
                return JsonResponse(
                    {'error': 'Action must be "attach", "detach", or "replace"'}, 
                    status=400
                )
            
            # Validate coverage area IDs
            if not isinstance(coverage_area_ids, list):
                return JsonResponse(
                    {'error': 'coverage_area_ids must be a list'}, 
                    status=400
                )
            
            # Allow empty list for 'replace' action (to clear all associations)
            if not coverage_area_ids and action != 'replace':
                return JsonResponse(
                    {'error': 'coverage_area_ids cannot be empty for attach/detach actions'}, 
                    status=400
                )
            
            # Get coverage areas (skip for replace with empty list)
            coverage_areas = []
            if coverage_area_ids:
                try:
                    coverage_areas = CoverageArea.objects.filter(id__in=coverage_area_ids)
                    found_ids = set(coverage_areas.values_list('id', flat=True))
                    missing_ids = set(coverage_area_ids) - found_ids
                    
                    if missing_ids:
                        return JsonResponse(
                            {'error': f'Coverage areas not found: {list(missing_ids)}'}, 
                            status=404
                        )
                except Exception as e:
                    return JsonResponse(
                        {'error': f'Error fetching coverage areas: {str(e)}'}, 
                        status=400
                    )
            
            # Perform the action
            attached_count = 0
            detached_count = 0
            errors = []
            
            if action == 'attach':
                for coverage_area in coverage_areas:
                    try:
                        # Check if association already exists
                        if not resource.coverage_areas.filter(id=coverage_area.id).exists():
                            # Create the association
                            from ..models import ResourceCoverage
                            ResourceCoverage.objects.create(
                                resource=resource,
                                coverage_area=coverage_area,
                                created_by=request.user,
                                notes=notes
                            )
                            attached_count += 1
                        else:
                            errors.append(f'Area {coverage_area.name} is already attached')
                    except Exception as e:
                        errors.append(f'Error attaching {coverage_area.name}: {str(e)}')
            
            elif action == 'detach':
                for coverage_area in coverage_areas:
                    try:
                        # Remove the association
                        from ..models import ResourceCoverage
                        deleted_count, _ = ResourceCoverage.objects.filter(
                            resource=resource,
                            coverage_area=coverage_area
                        ).delete()
                        
                        if deleted_count > 0:
                            detached_count += 1
                        else:
                            errors.append(f'Area {coverage_area.name} was not attached')
                    except Exception as e:
                        errors.append(f'Error detaching {coverage_area.name}: {str(e)}')
            
            elif action == 'replace':
                try:
                    # Clear all existing associations
                    from ..models import ResourceCoverage
                    deleted_count, _ = ResourceCoverage.objects.filter(resource=resource).delete()
                    detached_count = deleted_count
                    
                    # Add new associations if any
                    for coverage_area in coverage_areas:
                        try:
                            ResourceCoverage.objects.create(
                                resource=resource,
                                coverage_area=coverage_area,
                                created_by=request.user,
                                notes=notes
                            )
                            attached_count += 1
                        except Exception as e:
                            errors.append(f'Error attaching {coverage_area.name}: {str(e)}')
                except Exception as e:
                    errors.append(f'Error replacing associations: {str(e)}')
            
            # Build response
            response_data = {
                'success': len(errors) == 0,
                'message': f'{action.capitalize()} operation completed',
                'attached_count': attached_count,
                'detached_count': detached_count,
                'errors': errors
            }
            
            if errors:
                return JsonResponse(response_data, status=400)
            else:
                return JsonResponse(response_data)
                
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )
    
    def get(self, request: HttpRequest, resource_id: int) -> JsonResponse:
        """Handle GET requests to retrieve resource coverage areas.
        
        Args:
            request: HTTP request object
            resource_id: ID of the resource to get areas for
            
        Returns:
            JsonResponse: JSON response with resource coverage areas
        """
        try:
            # Get the resource
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return JsonResponse(
                    {'error': f'Resource with ID {resource_id} not found'}, 
                    status=404
                )
            
            # Get coverage areas with association details
            coverage_areas = []
            for coverage_area in resource.coverage_areas.all():
                # Get the association details
                from ..models import ResourceCoverage
                try:
                    association = ResourceCoverage.objects.get(
                        resource=resource,
                        coverage_area=coverage_area
                    )
                    area_data = {
                        'id': coverage_area.id,
                        'name': coverage_area.name,
                        'kind': coverage_area.kind,
                        'ext_ids': coverage_area.ext_ids or {},
                        'attached_at': association.created_at.isoformat(),
                        'attached_by': association.created_by.username,
                        'notes': association.notes or ''
                    }
                    
                    # Add bounds and center if available
                    if coverage_area.geom and hasattr(settings, 'GIS_ENABLED') and settings.GIS_ENABLED:
                        try:
                            bounds = coverage_area.geom.extent
                            area_data['bounds'] = {
                                'west': bounds[0],
                                'south': bounds[1],
                                'east': bounds[2],
                                'north': bounds[3]
                            }
                            
                            # Add center coordinates for map positioning
                            center = coverage_area.geom.centroid
                            area_data['center'] = {
                                'lat': center.y,
                                'lon': center.x
                            }
                        except Exception:
                            pass
                    elif coverage_area.center:
                        # Use stored center point if available
                        try:
                            # Handle case where center might be stored as string
                            if hasattr(coverage_area.center, 'y') and hasattr(coverage_area.center, 'x'):
                                area_data['center'] = {
                                    'lat': coverage_area.center.y,
                                    'lon': coverage_area.center.x
                                }
                            else:
                                # Skip center if it's not a proper Point object
                                pass
                        except Exception:
                            # Skip center if there's any error accessing it
                            pass
                    
                    coverage_areas.append(area_data)
                except ResourceCoverage.DoesNotExist:
                    # This shouldn't happen, but handle gracefully
                    continue
            
            return JsonResponse({
                'resource_id': resource_id,
                'resource_name': resource.name,
                'coverage_areas': coverage_areas,
                'total_count': len(coverage_areas)
            })
            
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )


@method_decorator(csrf_exempt, name='dispatch')
class ResourceEligibilityView(View):
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
                return JsonResponse(
                    {'error': 'Invalid coordinates provided'}, 
                    status=400
                )
            
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
            return JsonResponse(
                {'error': f'Invalid parameter value: {str(e)}'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )


@method_decorator(csrf_exempt, name='dispatch')
class ReverseGeocodingView(View):
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
                return JsonResponse(
                    {'error': 'Invalid coordinates provided'}, 
                    status=400
                )
            
            # Use geocoding service for reverse geocoding
            from ..services.geocoding import get_geocoding_service
            
            service = get_geocoding_service()
            result = service.reverse_geocode(lat, lon)
            
            if result:
                return JsonResponse({
                    'success': True,
                    'result': {
                        'address': result.address,
                        'latitude': result.latitude,
                        'longitude': result.longitude,
                        'confidence': result.confidence,
                        'provider': result.provider
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Could not reverse geocode the provided coordinates'
                }, status=404)
                
        except ValueError as e:
            return JsonResponse(
                {'error': f'Invalid parameter value: {str(e)}'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=500
            )


@method_decorator(csrf_exempt, name='dispatch')
class StateCountyView(View):
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
            from ..models import CoverageArea
            
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
                'success': True,
                'states': list(states),
                'counties': list(counties)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=500)
