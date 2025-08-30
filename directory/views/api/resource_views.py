"""
Resource Management API Views

This module contains API views for managing resource-coverage area associations.
Extracted from the original api_views.py file for better organization.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import json
from typing import Dict

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import CoverageArea, Resource, ResourceCoverage
from .base import BaseAPIView


@method_decorator(csrf_exempt, name='dispatch')
class ResourceAreaManagementView(BaseAPIView):
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
            data = self.validate_json_request(request)
            if data is None:
                return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
            
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
                return JsonResponse({'error': 'coverage_area_ids must be a list'}, status=400)
            
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
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    
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
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
