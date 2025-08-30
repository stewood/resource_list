"""
AI API Views for Resource Directory

This module contains API views for AI-powered functionality.
Enhanced version with better response handling and confidence levels.
"""

import json
from typing import Any, Dict
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Resource
from ..services.ai.core.review_service import AIReviewService


class AIVerificationView(LoginRequiredMixin, APIView):
    """
    Enhanced API view for AI-powered resource data verification.
    
    This view accepts a resource ID and returns AI-verified data, change notes, and confidence levels.
    Focuses on basic information verification with authoritative web searches.
    """
    
    def post(self, request, resource_id: int) -> Response:
        """
        Process enhanced AI verification for a resource.
        
        Args:
            request: The HTTP request
            resource_id: The ID of the resource to verify
            
        Returns:
            JSON response with verified data, change notes, and confidence levels
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
            
            # Prepare enhanced response
            response_data = {
                "status": "success",
                "verified_data": result.get("verified_data", {}),
                "change_notes": result.get("change_notes", {}),
                "confidence_levels": result.get("confidence_levels", {}),
                "verification_notes": result.get("verification_notes", {}),
                "resource_id": resource_id,
                "verification_focus": "basic_information",
                "fields_verified": [
                    "name", "address1", "address2", "city", "state", "postal_code", 
                    "phone", "email", "website"
                ]
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
        Prepare resource data for enhanced AI verification.
        Focuses on basic information fields.
        
        Args:
            resource: The Resource instance
            
        Returns:
            Dictionary containing formatted resource data for basic information verification
        """
        return {
            # Basic information (primary focus)
            "name": resource.name,
            "description": resource.description,
            
            # Contact information
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            
            # Address information
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            
            # Additional context (for verification purposes)
            "category": resource.category.name if resource.category else None,
            "service_types": [st.name for st in resource.service_types.all()] if resource.service_types.exists() else [],
            "source": resource.source,
            "notes": resource.notes,
        }
