"""
AI API Views for Resource Directory

This module contains API views for AI-powered functionality.
Enhanced version with better response handling and confidence levels.
"""

import json
from typing import Any, Dict
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ..models import Resource
from ..services.ai.core.review_service import AIReviewService


class AIVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Comprehensive API view for AI-powered resource data verification.
    
    This view accepts a resource ID and returns AI-verified data for all 23 fields,
    including confidence scores, verification statuses, missing field recommendations,
    and comprehensive verification metadata.
    """
    
    def post(self, request, resource_id: int) -> Response:
        """
        Process comprehensive AI verification for a resource.
        
        Args:
            request: The HTTP request
            resource_id: The ID of the resource to verify
            
        Returns:
            JSON response with comprehensive verification data including:
            - All 23 fields verified data
            - Confidence scores for each field
            - Verification statuses (VERIFIED, UPDATED, CONFLICTING, NOT_FOUND)
            - Missing field recommendations
            - Sources used and reasoning
            - Summary statistics
        """
        try:
            # Get the resource
            resource = get_object_or_404(Resource, pk=resource_id)
            
            # Initialize enhanced AI service
            ai_service = AIReviewService()
            
            # Check if AI service is available
            if not ai_service.is_available():
                return Response(
                    {
                        "error": "AI service not available. Please check your OpenRouter API key configuration.",
                        "status": "unavailable",
                        "details": "Make sure OPENROUTER_API_KEY is set in your environment variables"
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Prepare current data for AI verification
            current_data = self._prepare_resource_data(resource)
            
            # Get enhanced AI verification
            result = ai_service.verify_resource_data(current_data)
            
            # Prepare enhanced response with new comprehensive format
            response_data = {
                "status": "success",
                "resource_id": resource_id,
                "resource_name": result.get("resource_name", resource.name),
                "verification_timestamp": result.get("verification_timestamp"),
                "ai_model_used": result.get("ai_model_used"),
                
                # Core verification data
                "verified_data": result.get("verified_data", {}),
                "confidence_scores": result.get("confidence_scores", {}),
                "verification_statuses": result.get("verification_statuses", {}),
                
                # Change tracking
                "change_notes": result.get("change_notes", {}),
                "missing_field_recommendations": result.get("missing_field_recommendations", {}),
                
                # Sources and reasoning
                "sources_used": result.get("sources_used", []),
                "field_sources": result.get("field_sources", {}),
                "field_reasoning": result.get("field_reasoning", {}),
                
                # Summary statistics
                "total_fields_processed": result.get("total_fields_processed", 0),
                "verified_fields_count": result.get("verified_fields_count", 0),
                "updated_fields_count": result.get("updated_fields_count", 0),
                "conflicting_fields_count": result.get("conflicting_fields_count", 0),
                "not_found_fields_count": result.get("not_found_fields_count", 0),
                "average_confidence_score": result.get("average_confidence_score", 0.0),
                "overall_verification_status": result.get("overall_verification_status", "NOT_FOUND"),
                
                # General notes
                "verification_notes": result.get("verification_notes", ""),
                
                # Field coverage information
                "verification_focus": "comprehensive_all_fields",
                "fields_verified": list(result.get("verified_data", {}).keys()),
                "fields_with_recommendations": list(result.get("missing_field_recommendations", {}).keys()),
                
                # Service area information
                "service_areas": result.get("verified_data", {}).get("service_areas", {})
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Resource.DoesNotExist:
            return Response(
                {
                    "error": "Resource not found",
                    "resource_id": resource_id,
                    "status": "not_found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            return Response(
                {
                    "error": "Resource not found",
                    "resource_id": resource_id,
                    "status": "not_found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "error": f"An error occurred during AI verification: {str(e)}",
                    "status": "error",
                    "resource_id": resource_id
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _prepare_resource_data(self, resource: Resource) -> Dict[str, Any]:
        """
        Prepare comprehensive resource data for AI verification.
        Includes all 23 fields for complete verification plus current service areas.
        
        Args:
            resource: The Resource instance
            
        Returns:
            Dictionary containing formatted resource data for comprehensive verification
        """
        # Get current service areas through the ResourceCoverage through model
        from ..models import ResourceCoverage
        
        current_service_areas = []
        if hasattr(resource, 'coverage_areas'):
            resource_coverage_associations = ResourceCoverage.objects.filter(
                resource=resource
            ).select_related('coverage_area', 'created_by')
            
            current_service_areas = [
                {
                    "area_name": association.coverage_area.name,
                    "area_type": association.coverage_area.kind,
                    "validation_status": "VALID",  # Assume existing areas are valid
                    "confidence_score": 100.0,
                    "geographic_scope": "in_scope",
                    "source": "existing_database",
                    "validation_message": f"Existing service area: {association.coverage_area.name} ({association.coverage_area.kind})",
                    "attached_at": association.created_at.isoformat() if association.created_at else None,
                    "attached_by": association.created_by.username if association.created_by else None
                }
                for association in resource_coverage_associations
            ]
        
        return {
            # Basic information (4 fields)
            "name": resource.name,
            "description": resource.description,
            "category": resource.category.name if resource.category else None,
            "service_types": [st.name for st in resource.service_types.all()] if resource.service_types.exists() else [],
            
            # Contact information (3 fields)
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            
            # Location information (6 fields)
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            
            # Operational information (8 fields)
            "hours_of_operation": getattr(resource, 'hours_of_operation', None),
            "is_emergency_service": getattr(resource, 'is_emergency_service', None),
            "is_24_hour_service": getattr(resource, 'is_24_hour_service', None),
            "eligibility_requirements": getattr(resource, 'eligibility_requirements', None),
            "populations_served": getattr(resource, 'populations_served', None),
            "insurance_accepted": getattr(resource, 'insurance_accepted', None),
            "cost_information": getattr(resource, 'cost_information', None),
            "languages_available": getattr(resource, 'languages_available', None),
            "capacity": getattr(resource, 'capacity', None),
            
            # Source information (2 fields)
            "source": resource.source,
            "notes": resource.notes,
            
            # Service areas information
            "current_service_areas": current_service_areas,
        }
