"""
AI Review Views - AI-Powered Resource Verification Interface

This module contains Django views for the AI Review functionality, which allows
users to review and verify resource information using AI assistance.

Key Views:
    - ai_review: Display current resource data alongside fields for AI-verified data
    - ai_verify_resource: Process AI verification and update resource data

Features:
    - Side-by-side comparison of current vs verified data
    - Field-by-field verification interface
    - AI-powered data validation and suggestions
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
    from directory.views.ai_review_views import AIReviewView

    # URL patterns typically map to this view
    # GET /resources/<pk>/ai-review/ -> AIReviewView
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


class AIReviewView(LoginRequiredMixin, TemplateView):
    """Legacy 3-column AI review view - keeping for reference but will be replaced"""
    template_name = 'directory/ai_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource_id = self.kwargs.get('pk')
        resource = get_object_or_404(Resource, pk=resource_id)
        
        context['resource'] = resource
        return context


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
            }
        }
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class AIDashboardAPIView(LoginRequiredMixin, View):
    """API endpoint for AI dashboard operations"""
    
    def post(self, request, *args, **kwargs):
        """Handle AI verification requests"""
        try:
            resource_id = self.kwargs.get('resource_id')
            resource = get_object_or_404(Resource, pk=resource_id)
            
            # Initialize AI service
            ai_service = AIReviewService()
            
            # Convert resource to dictionary for AI service
            resource_data = {
                'name': resource.name,
                'description': resource.description,
                'category': resource.category.name if resource.category else None,
                'phone': resource.phone,
                'email': resource.email,
                'website': resource.website,
                'address1': resource.address1,
                'address2': resource.address2,
                'city': resource.city,
                'state': resource.state,
                'postal_code': resource.postal_code,
                'county': resource.county,
                'hours_of_operation': resource.hours_of_operation,
                'eligibility_requirements': resource.eligibility_requirements,
                'populations_served': resource.populations_served,
                'cost_information': resource.cost_information,
                'languages_available': resource.languages_available,
            }
            
            # Run AI verification
            result = ai_service.verify_resource_data(resource_data)
            
            if result and result.get('verified_data'):
                # Organize data for dashboard display
                dashboard_data = self._organize_for_dashboard(result, resource)
                
                # Add enhanced description if available
                verification_notes = result.get('verification_notes', {})
                if 'enhanced_description' in verification_notes:
                    dashboard_data['enhanced_description'] = verification_notes['enhanced_description']
                
                # Add Markdown report if available
                markdown_report = result.get('markdown_report', '')
                
                return JsonResponse({
                    'status': 'success',
                    'dashboard_data': dashboard_data,
                    'markdown_report': markdown_report,
                    'summary': {
                        'total_changes': len(dashboard_data['changes']),
                        'total_verified': len(dashboard_data['verified_fields']),
                        'high_confidence': len([c for c in dashboard_data['changes'] if c['confidence'] == 'high']),
                        'medium_confidence': len([c for c in dashboard_data['changes'] if c['confidence'] == 'medium']),
                        'low_confidence': len([c for c in dashboard_data['changes'] if c['confidence'] == 'low']),
                        'verified_high': len([c for c in dashboard_data['verified_fields'] if c['confidence'] == 'high']),
                        'verified_medium': len([c for c in dashboard_data['verified_fields'] if c['confidence'] == 'medium']),
                        'verified_low': len([c for c in dashboard_data['verified_fields'] if c['confidence'] == 'low']),
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': result.get('error', 'AI verification failed')
                })
                
        except Exception as e:
            logger.error(f"AI Dashboard API error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            })
    
    def _organize_for_dashboard(self, ai_result, resource):
        """Organize AI results into dashboard-friendly format with all verified fields"""
        verified_data = ai_result.get('verified_data', {})
        change_notes = ai_result.get('change_notes', {})
        confidence_levels = ai_result.get('confidence_levels', {})
        
        # Define field categories
        categories = {
            'basic_info': ['name', 'description', 'category'],
            'contact_info': ['phone', 'email', 'website'],
            'location_info': ['address1', 'address2', 'city', 'state', 'postal_code', 'county'],
            'service_info': ['hours_of_operation', 'eligibility_requirements', 'populations_served', 'cost_information', 'languages_available', 'service_types']
        }
        
        changes = []
        verified_fields = []
        category_summaries = {}
        
        for category, fields in categories.items():
            category_changes = []
            category_verified = []
            
            for field in fields:
                try:
                    current_value = getattr(resource, field, None)
                    if hasattr(current_value, 'name'):  # For foreign keys
                        current_value = current_value.name
                    elif hasattr(current_value, 'all'):  # For many-to-many fields
                        current_value = [item.name for item in current_value.all()]
                except AttributeError:
                    current_value = None
                
                suggested_value = verified_data.get(field)
                change_note = change_notes.get(field, '')
                confidence = confidence_levels.get(field, 'medium')
                
                # For description field, use enhanced description as suggested value if available
                if field == 'description' and 'enhanced_description' in ai_result.get('verification_notes', {}):
                    enhanced_desc = ai_result['verification_notes']['enhanced_description']
                    enhanced_value = enhanced_desc.get('suggested_improvement', '')
                    if enhanced_value and enhanced_value != current_value:
                        suggested_value = enhanced_value
                
                # Determine if there's a meaningful change
                has_change = False
                if suggested_value is not None:
                    if isinstance(current_value, list) and isinstance(suggested_value, list):
                        # For lists (like service_types), check if content is different
                        has_change = set(current_value) != set(suggested_value)
                    elif isinstance(current_value, str) and isinstance(suggested_value, str):
                        # For strings, check if content is meaningfully different (ignore whitespace differences)
                        current_clean = current_value.strip() if current_value else ""
                        suggested_clean = suggested_value.strip() if suggested_value else ""
                        has_change = current_clean != suggested_clean
                    else:
                        # For other types, direct comparison
                        has_change = current_value != suggested_value
                
                # Create field data for all verified fields
                field_data = {
                    'field': field,
                    'field_display': field.replace('_', ' ').title(),
                    'category': category,
                    'current_value': current_value,
                    'suggested_value': suggested_value,
                    'change_note': change_note,
                    'confidence': confidence,
                    'verified': change_note and len(change_note.strip()) > 0,  # Consider verified if there's a change note
                    'has_change': has_change,
                    'approved': False,  # Default to not approved
                    'reasoning': self._extract_reasoning(change_note)
                }
                
                # Add enhanced description if available for description field
                if field == 'description' and 'enhanced_description' in ai_result.get('verification_notes', {}):
                    enhanced_desc = ai_result['verification_notes']['enhanced_description']
                    field_data['enhanced_description'] = enhanced_desc.get('suggested_improvement', '')
                
                # Add category suggestions if available
                if field == 'category' and 'category_suggestions' in ai_result.get('verification_notes', {}):
                    category_suggestions = ai_result['verification_notes']['category_suggestions']
                    field_data['category_suggestions'] = category_suggestions
                
                # Add to appropriate lists
                if field_data['has_change']:
                    changes.append(field_data)
                    category_changes.append(field_data)
                elif field_data['verified']:
                    verified_fields.append(field_data)
                    category_verified.append(field_data)
                else:
                    # Field was not verified by AI
                    field_data['reasoning'] = "Field not verified by AI - no data found"
                    verified_fields.append(field_data)
                    category_verified.append(field_data)
            
            # Create category summary
            if category_changes or category_verified:
                category_summaries[category] = {
                    'name': category.replace('_', ' ').title(),
                    'change_count': len(category_changes),
                    'verified_count': len(category_verified),
                    'high_confidence': len([c for c in category_changes if c['confidence'] == 'high']),
                    'medium_confidence': len([c for c in category_changes if c['confidence'] == 'medium']),
                    'low_confidence': len([c for c in category_changes if c['confidence'] == 'low']),
                    'verified_high': len([c for c in category_verified if c['confidence'] == 'high']),
                    'verified_medium': len([c for c in category_verified if c['confidence'] == 'medium']),
                    'verified_low': len([c for c in category_verified if c['confidence'] == 'low']),
                }
        
        return {
            'changes': changes,
            'verified_fields': verified_fields,
            'category_summaries': category_summaries,
            'total_changes': len(changes),
            'total_verified': len(verified_fields)
        }
    
    def _extract_reasoning(self, change_note):
        """Extract key reasoning from change note"""
        if not change_note:
            return "No specific reasoning provided"
        
        # Look for key phrases that indicate reasoning
        reasoning_keywords = [
            'verified with', 'found on website', 'corrected from', 
            'updated based on', 'confirmed by', 'standardized'
        ]
        
        for keyword in reasoning_keywords:
            if keyword in change_note.lower():
                return change_note
        
        # Don't truncate - show full reasoning
        return change_note

