"""
AI Auto Verification Views - Automated AI Verification API

This module contains the API view for automated AI verification that applies
AI-suggested changes to resources and marks them for review using the existing
workflow system.

Key Features:
    - Automated application of AI-suggested changes
    - Integration with existing review workflow
    - Complete audit trail for AI actions
    - Leverages existing status transitions

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - rest_framework for API views
    - directory.models for data access
    - directory.services.ai for AI verification
    - audit.models for audit logging

Usage:
    POST /api/resources/{id}/ai-auto-verify/
    
    Request: None (just resource ID in URL)
    Response: JSON with verification results and status update
"""

import json
import logging
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Resource
from ..services.ai.core.review_service import AIReviewService
from audit.models import AuditManager

logger = logging.getLogger(__name__)


class AIAutoVerificationView(LoginRequiredMixin, APIView):
    """
    API view for automated AI verification and change application.
    
    This view automatically applies AI-suggested changes to a resource and
    marks it for review using the existing workflow system. It leverages
    the existing AIReviewService and audit system for complete tracking.
    
    Endpoint: POST /api/resources/{resource_id}/ai-auto-verify/
    
    Workflow:
        1. Retrieve resource by ID
        2. Call AIReviewService for verification
        3. Apply all AI-suggested changes to resource
        4. Create audit log entry for AI action
        5. Mark resource as "needs_review"
        6. Return verification results and status
    
    Authentication: Required (LoginRequiredMixin)
    Permissions: Uses existing permission system
    
    Example:
        POST /api/resources/123/ai-auto-verify/
        
        Response:
        {
            "status": "success",
            "message": "AI verification completed and resource marked for review",
            "resource_id": 123,
            "changes_applied": 5,
            "verification_report": "...",
            "new_status": "needs_review",
            "audit_log_id": 456
        }
    """
    
    def post(self, request, resource_id: int) -> Response:
        """
        Process automated AI verification for a resource.
        
        Args:
            request: The HTTP request object
            resource_id: The ID of the resource to verify
            
        Returns:
            JSON response with verification results and status update
            
        Raises:
            404: If resource not found
            503: If AI service unavailable
            500: If verification fails
        """
        try:
            # Get the resource
            resource = get_object_or_404(Resource, pk=resource_id, is_deleted=False)
            
            # Initialize AI service
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
            
            # Get the published version of the resource for AI verification
            published_data = self._get_published_resource_data(resource)
            
            # Get AI verification results using published data
            ai_result = ai_service.verify_resource_data(published_data)
            
            if not ai_result or not ai_result.get('verified_data'):
                return Response(
                    {
                        "error": "AI verification failed or returned no results",
                        "status": "error",
                        "resource_id": resource_id
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Apply AI changes to the resource
            changes_applied = self._apply_ai_changes(resource, ai_result['verified_data'], request.user)
            
            # Store the AI verification report in the resource notes
            self._store_ai_verification_report(resource, ai_result, published_data)
            
            # Create audit log entry for AI verification
            audit_log = self._create_ai_verification_audit(
                resource=resource,
                user=request.user,
                ai_result=ai_result,
                changes_applied=changes_applied
            )
            
            # Mark resource as needs_review
            resource.status = "needs_review"
            resource.save()
            
            # Prepare response
            response_data = {
                "status": "success",
                "message": "AI verification completed and resource marked for review",
                "resource_id": resource_id,
                "changes_applied": changes_applied,
                "verification_report": ai_result.get('report', ''),
                "ai_response": ai_result.get('ai_response', ''),
                "confidence_scores": ai_result.get('confidence_scores', {}),
                "new_status": "needs_review",
                "audit_log_id": audit_log.id if audit_log else None,
                "verification_timestamp": timezone.now().isoformat()
            }
            
            logger.info(f"AI auto-verification completed for resource {resource_id}. "
                       f"Applied {changes_applied} changes.")
            
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
            logger.error(f"Error in AI auto-verification for resource {resource_id}: {str(e)}")
            return Response(
                {
                    "error": f"An error occurred during AI verification: {str(e)}",
                    "status": "error",
                    "resource_id": resource_id
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_published_resource_data(self, resource: Resource) -> Dict[str, Any]:
        """
        Get the published version of resource data for AI verification.
        
        Args:
            resource: The Resource instance
            
        Returns:
            Dictionary containing published resource data for AI verification
        """
        from audit.models import ResourceVersion
        
        # Get the last published version
        import json
        last_published_version = None
        
        # Get all versions for this resource and find the last published one
        versions = ResourceVersion.objects.filter(resource=resource).order_by('-changed_at')
        for version in versions:
            try:
                snapshot_data = json.loads(version.snapshot_json)
                if snapshot_data.get('status') == 'published':
                    last_published_version = version
                    break
            except (json.JSONDecodeError, KeyError):
                continue
        
        if last_published_version:
            # Use the published snapshot data
            try:
                published_snapshot = json.loads(last_published_version.snapshot_json)
                logger.info(f"Using published version {last_published_version.id} for AI verification of resource {resource.id}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse snapshot JSON for version {last_published_version.id}")
                return self._prepare_resource_data(resource)
            
            return {
                # Basic information
                "name": published_snapshot.get('name', ''),
                "description": published_snapshot.get('description', ''),
                "category": published_snapshot.get('category', ''),
                
                # Contact information
                "phone": published_snapshot.get('phone', ''),
                "email": published_snapshot.get('email', ''),
                "website": published_snapshot.get('website', ''),
                
                # Address information
                "address1": published_snapshot.get('address1', ''),
                "address2": published_snapshot.get('address2', ''),
                "city": published_snapshot.get('city', ''),
                "state": published_snapshot.get('state', ''),
                "postal_code": published_snapshot.get('postal_code', ''),
                "county": published_snapshot.get('county', ''),
                
                # Service information
                "hours_of_operation": published_snapshot.get('hours_of_operation', ''),
                "eligibility_requirements": published_snapshot.get('eligibility_requirements', ''),
                "populations_served": published_snapshot.get('populations_served', ''),
                "cost_information": published_snapshot.get('cost_information', ''),
                "languages_available": published_snapshot.get('languages_available', ''),
                
                # Additional context
                "source": published_snapshot.get('source', ''),
                "notes": published_snapshot.get('notes', ''),
                "service_types": published_snapshot.get('service_types', []),
            }
        else:
            # Fallback to current resource data if no published version exists
            logger.warning(f"No published version found for resource {resource.id}, using current data")
            return self._prepare_resource_data(resource)
    
    def _prepare_resource_data(self, resource: Resource) -> Dict[str, Any]:
        """
        Prepare current resource data for AI verification.
        
        Args:
            resource: The Resource instance
            
        Returns:
            Dictionary containing formatted resource data for AI verification
        """
        return {
            # Basic information
            "name": resource.name,
            "description": resource.description,
            "category": resource.category.name if resource.category else None,
            
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
            
            # Service information
            "hours_of_operation": resource.hours_of_operation,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            
            # Additional context
            "source": resource.source,
            "notes": resource.notes,
            "service_types": [st.name for st in resource.service_types.all()] if resource.service_types.exists() else [],
        }
    
    def _apply_ai_changes(self, resource: Resource, verified_data: Dict[str, Any], user: Any) -> int:
        """
        Apply AI-suggested changes to the resource.
        
        Args:
            resource: The Resource instance to update
            verified_data: Dictionary containing AI-verified data
            user: The user performing the verification
            
        Returns:
            Number of changes applied
        """
        changes_applied = 0
        
        # Define field mappings (AI field names to Resource field names)
        field_mappings = {
            'name': 'name',
            'description': 'description',
            'phone': 'phone',
            'email': 'email',
            'website': 'website',
            'address1': 'address1',
            'address2': 'address2',
            'city': 'city',
            'state': 'state',
            'postal_code': 'postal_code',
            'county': 'county',
            'hours_of_operation': 'hours_of_operation',
            'eligibility_requirements': 'eligibility_requirements',
            'populations_served': 'populations_served',
            'cost_information': 'cost_information',
            'languages_available': 'languages_available',
        }
        
        # Apply changes for each field
        for ai_field, resource_field in field_mappings.items():
            if ai_field in verified_data and verified_data[ai_field]:
                current_value = getattr(resource, resource_field, None)
                new_value = verified_data[ai_field]
                
                # Check if the value has actually changed
                if current_value != new_value:
                    setattr(resource, resource_field, new_value)
                    changes_applied += 1
                    logger.debug(f"Applied AI change to {resource_field}: {current_value} -> {new_value}")
        
        # Handle service types (many-to-many field)
        if 'service_types' in verified_data and verified_data['service_types']:
            try:
                from directory.models import ServiceType
                
                # Get the suggested service type names
                suggested_service_types = verified_data['service_types']
                if isinstance(suggested_service_types, str):
                    # Split by comma if it's a string
                    suggested_service_types = [st.strip() for st in suggested_service_types.split(',') if st.strip()]
                
                # Get current service types
                current_service_types = set(resource.service_types.values_list('name', flat=True))
                
                # Find or create service types
                new_service_types = []
                for service_type_name in suggested_service_types:
                    service_type, created = ServiceType.objects.get_or_create(
                        name=service_type_name,
                        defaults={'description': f'Service type for {service_type_name}'}
                    )
                    new_service_types.append(service_type)
                
                # Check if there are any changes
                new_service_type_names = {st.name for st in new_service_types}
                if current_service_types != new_service_type_names:
                    # Clear existing service types and add new ones
                    resource.service_types.clear()
                    resource.service_types.add(*new_service_types)
                    changes_applied += 1
                    logger.info(f"Applied service types changes: {current_service_types} -> {new_service_type_names}")
                else:
                    logger.info("Service types unchanged, no update needed")
                    
            except Exception as e:
                logger.error(f"Failed to apply service types changes: {str(e)}")
                # Continue with other changes even if service types fail
        
        # Save the resource if any changes were made
        if changes_applied > 0:
            # Update verification fields for published resources
            if resource.status == 'published':
                from django.utils import timezone
                resource.last_verified_at = timezone.now()
                resource.last_verified_by = user
            
            resource.save()
            logger.info(f"Applied {changes_applied} AI changes to resource {resource.id}")
        
        return changes_applied
    
    def _create_ai_verification_audit(
        self, 
        resource: Resource, 
        user: Any, 
        ai_result: Dict[str, Any], 
        changes_applied: int
    ):
        """
        Create audit log entry for AI verification action.
        
        Args:
            resource: The Resource instance that was verified
            user: The user who initiated the AI verification
            ai_result: The AI verification results
            changes_applied: Number of changes applied
            
        Returns:
            AuditLog instance or None if creation fails
        """
        try:
            # Prepare metadata for audit log
            metadata = {
                "action_type": "ai_auto_verification",
                "changes_applied": changes_applied,
                "confidence_scores": ai_result.get('confidence_scores', {}),
                "verification_report": ai_result.get('report', ''),
                "ai_response": ai_result.get('ai_response', ''),
                "verification_timestamp": timezone.now().isoformat()
            }
            
            # Create audit log entry with summary
            action_text = f"AI auto-verification completed for resource {resource.id}. Changes applied: {changes_applied}."
            
            audit_log = AuditManager.log_action(
                actor=user,
                action=action_text,
                target_table="directory_resource",
                target_id=str(resource.id),
                metadata=metadata
            )
            
            logger.info(f"Created audit log entry {audit_log.id} for AI verification of resource {resource.id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log for AI verification: {str(e)}")
            return None
    
    def _store_ai_verification_report(self, resource: Resource, ai_result: Dict[str, Any], original_data: Dict[str, Any]):
        """
        Store the AI verification report in the resource notes field.
        
        Args:
            resource: The Resource instance to update
            ai_result: The AI verification results containing the report
            original_data: Original resource data before AI changes
        """
        try:
            # Get the verification report from AI result
            verification_report = ai_result.get('report', '')
            
            if verification_report:
                # Generate a new report using original data for accurate status comparison
                from directory.services.ai.core.review_service import AIReviewService
                ai_service = AIReviewService()
                
                # Generate report with original data for proper status comparison
                updated_report = ai_service._generate_verification_report(
                    current_data=original_data,
                    verified_data=ai_result.get('verified_data', {}),
                    change_notes=ai_result.get('change_notes', {}),
                    confidence_scores=ai_result.get('confidence_scores', {})
                )
                
                # Update the resource notes with the corrected AI verification report
                resource.notes = updated_report
                resource.save()
                logger.info(f"Stored corrected AI verification report in notes for resource {resource.id}")
            else:
                logger.warning(f"No verification report found in AI result for resource {resource.id}")
                
        except Exception as e:
            logger.error(f"Failed to store AI verification report in notes: {str(e)}")
