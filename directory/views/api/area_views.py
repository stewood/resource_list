"""
Area Search API Views

This module contains API views for searching and managing coverage areas.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import json
from typing import Dict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import CoverageArea
from .base import BaseAPIView, format_coverage_area_response


@method_decorator(csrf_exempt, name='dispatch')
class AreaSearchView(BaseAPIView):
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
                return JsonResponse({'error': 'Page number must be greater than 0'}, status=400)
            if page_size < 1 or page_size > 100:
                return JsonResponse({'error': 'Page size must be between 1 and 100'}, status=400)
            
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
                return JsonResponse({'error': f'Invalid page number: {str(e)}'}, status=400)
            
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
            return JsonResponse({'error': f'Invalid parameter value: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

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
                return JsonResponse({'error': f'Coverage area with ID {area_id} not found'}, status=404)
            
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
                    return self.create_error_response(f'Error processing geometry: {str(e)}', 500)
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
            
            return self.create_success_response(preview_data)
            
        except Exception as e:
            return self.create_error_response(f'Internal server error: {str(e)}', 500)

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
                return self.create_error_response(f'Coverage area with ID {area_id} not found', 404)
            
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
                    return self.create_error_response(f'Error processing geometry: {str(e)}', 500)
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
            
            return self.create_success_response(area_data)
            
        except Exception as e:
            return self.create_error_response(f'Internal server error: {str(e)}', 500)

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
            data = self.validate_json_request(request)
            if data is None:
                return self.create_error_response('Invalid JSON in request body', 400)
            
            # Extract and validate common parameters
            area_type = data.get('type', 'radius').lower()
            name = data.get('name', '').strip()
            
            # Validate required parameters
            if not name:
                return self.create_error_response('name is required', 400)
            
            # Validate area type
            if area_type not in ['radius', 'polygon']:
                return self.create_error_response('type must be either "radius" or "polygon"', 400)
            
            # Handle radius-based area creation
            if area_type == 'radius':
                return self._create_radius_area(data, name)
            # Handle polygon-based area creation
            elif area_type == 'polygon':
                return self._create_polygon_area(data, name)
            
        except Exception as e:
            return self.create_error_response(f'Internal server error: {str(e)}', 500)
    
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
                return self.create_error_response('center must be a list with [latitude, longitude]', 400)
            
            if not radius_miles or not isinstance(radius_miles, (int, float)):
                return self.create_error_response('radius_miles must be a number', 400)
            
            # Extract coordinates
            lat, lon = center
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return self.create_error_response(
                    'Invalid coordinates: latitude must be -90 to 90, longitude must be -180 to 180',
                    400
                )
            
            # Validate radius
            if radius_miles < 0.5 or radius_miles > 100:
                return self.create_error_response('radius_miles must be between 0.5 and 100 miles', 400)
            
            # Check if GIS is enabled
            if not getattr(settings, 'GIS_ENABLED', False):
                return self.create_error_response('GIS functionality is not enabled', 503)
            
            # Create radius-based coverage area
            try:
                # Create center point
                center_point = Point(lon, lat, srid=4326)
                
                # Convert radius to meters
                radius_meters = radius_miles * 1609.34
                
                # Create buffer polygon
                buffer_polygon = center_point.buffer(radius_meters / 111320.0)  # Approximate degrees
                
                # Convert to MultiPolygon if needed
                if buffer_polygon.geom_type == 'Polygon':
                    buffer_polygon = MultiPolygon([buffer_polygon])
                
                # Get or create default user for API operations
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
                
                return self.create_success_response(response_data, 201)
                
            except ImportError:
                return self.create_error_response('GIS libraries not available', 503)
            except Exception as e:
                return self.create_error_response(f'Error creating coverage area: {str(e)}', 500)
                
        except Exception as e:
            return self.create_error_response(f'Error creating radius area: {str(e)}', 500)
    
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
                return self.create_error_response('geometry is required for polygon areas', 400)
            
            # Check if GIS is enabled
            if not getattr(settings, 'GIS_ENABLED', False):
                return self.create_error_response('GIS functionality is not enabled', 503)
            
            # Create polygon-based coverage area
            try:
                # Parse GeoJSON geometry
                if isinstance(geometry_data, str):
                    # If geometry is a string, parse it as GeoJSON
                    geojson_str = geometry_data
                elif isinstance(geometry_data, dict):
                    # If geometry is a dict, convert to GeoJSON string
                    geojson_str = json.dumps(geometry_data)
                else:
                    return self.create_error_response('geometry must be a GeoJSON string or object', 400)
                
                # Create GEOS geometry from GeoJSON
                try:
                    geos_geometry = GEOSGeometry(geojson_str)
                except Exception as e:
                    return self.create_error_response(f'Invalid GeoJSON geometry: {str(e)}', 400)
                
                # Validate geometry type
                if geos_geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                    return self.create_error_response(
                        f'Geometry must be Polygon or MultiPolygon, got {geos_geometry.geom_type}',
                        400
                    )
                
                # Validate geometry
                if not geos_geometry.valid:
                    return self.create_error_response('Invalid geometry: self-intersecting or malformed polygon', 400)
                
                # Ensure SRID is 4326 (WGS84)
                if geos_geometry.srid != 4326:
                    geos_geometry.srid = 4326
                
                # Convert to MultiPolygon if needed
                if geos_geometry.geom_type == 'Polygon':
                    geos_geometry = MultiPolygon([geos_geometry])
                
                # Calculate center point
                center_point = geos_geometry.centroid
                
                # Get or create default user for API operations
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
                
                return self.create_success_response(response_data, 201)
                
            except ImportError:
                return self.create_error_response('GIS libraries not available', 503)
            except Exception as e:
                return self.create_error_response(f'Error creating coverage area: {str(e)}', 500)
                
        except Exception as e:
            return self.create_error_response(f'Error creating polygon area: {str(e)}', 500)
