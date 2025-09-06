"""
AI Dashboard Views - AI-Powered Resource Verification Interface

This module contains Django views for the AI Dashboard functionality, which provides
a modern interface for AI-assisted resource verification.

Key Views:
    - ai_dashboard: Modern dashboard interface for AI verification
    - ai_dashboard_api: API endpoint for dashboard functionality

Features:
    - Modern dashboard interface for AI verification
    - Real-time AI verification status
    - Permission-based access control
    - Audit trail for AI verification actions

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - django.views.generic for class-based views
    - directory.models for data access
    - directory.permissions for access control

Usage:
    from directory.views.ai_dashboard_views import AIDashboardView

    # URL patterns typically map to this view
    # GET /resources/<pk>/ai-dashboard/ -> AIDashboardView
"""

from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import DetailView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

from directory.models import Resource
from directory.services.ai.core.review_service import AIReviewService

import json
import logging

logger = logging.getLogger(__name__)


class AIDashboardView(LoginRequiredMixin, TemplateView):
    """New AI Dashboard view with better UX for reviewing AI suggestions"""
    template_name = 'directory/ai_dashboard_standalone.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource_id = self.kwargs.get('pk')
        resource = get_object_or_404(Resource, pk=resource_id)
        
        # Initialize AI service for potential pre-loading
        ai_service = AIReviewService()
        
        context['resource'] = resource
        context['ai_service'] = ai_service
        
        # Get resource data for display
        context['resource_data'] = {
            'basic_info': {
                'name': resource.name,
                'description': resource.description,
                'category': resource.category.name if resource.category else None,
            },
            'contact_info': {
                'phone': resource.phone,
                'email': resource.email,
                'website': resource.website,
            },
            'location_info': {
                'address1': resource.address1,
                'address2': resource.address2,
                'city': resource.city,
                'state': resource.state,
                'postal_code': resource.postal_code,
                'county': resource.county,
            },
            'service_info': {
                'hours_of_operation': resource.hours_of_operation,
                'eligibility_requirements': resource.eligibility_requirements,
                'populations_served': resource.populations_served,
                'cost_information': resource.cost_information,
                'languages_available': resource.languages_available,
                'service_types': [st.name for st in resource.service_types.all()],
                'is_emergency_service': resource.is_emergency_service,
                'is_24_hour_service': resource.is_24_hour_service,
            }
        }
        
        return context


class AIDashboardAPIView(LoginRequiredMixin, View):
    """API endpoint for AI Dashboard functionality"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle AI verification requests from the dashboard"""
        try:
            resource_id = self.kwargs.get('pk')
            resource = get_object_or_404(Resource, pk=resource_id)
            
            # Get the action from the request
            action = request.POST.get('action')
            
            if action == 'verify':
                # Run AI verification
                ai_service = AIReviewService()
                result = ai_service.verify_resource_data(resource)
                
                return JsonResponse({
                    'status': 'success',
                    'result': result
                })
            
            elif action == 'apply_changes':
                # Apply AI-suggested changes
                changes = json.loads(request.POST.get('changes', '{}'))
                
                with transaction.atomic():
                    # Apply changes to resource
                    for field, value in changes.items():
                        if hasattr(resource, field):
                            setattr(resource, field, value)
                    
                    resource.save()
                    
                    # Create audit log entry
                    from audit.models import AuditManager
                    AuditManager.log_action(
                        user=request.user,
                        action="AI changes applied via dashboard",
                        target=resource,
                        metadata_json={
                            'changes_applied': changes,
                            'source': 'ai_dashboard'
                        }
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Changes applied successfully'
                })
            
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid action'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error in AI Dashboard API: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
