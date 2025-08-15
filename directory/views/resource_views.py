"""
Resource Views - Core Resource Detail Operations

This module contains the ResourceDetailView for displaying individual resources
with version history and permission-based content visibility.

Features:
    - Complete resource information display
    - Recent version history (last 5 versions)
    - Permission-based notes field visibility
    - Support for archived resource viewing
    - Role-based access control for sensitive data

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - django.views.generic for class-based views
    - directory.models for data access
    - directory.permissions for access control

Usage:
    from directory.views.resource_views import ResourceDetailView
    
    # URL patterns typically map to this view
    # /resources/<pk>/ -> ResourceDetailView
"""

from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import DetailView

from ..models import Resource, ResourceVersion
from ..permissions import user_has_role


class ResourceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual resources with version history and permissions.
    
    This view displays comprehensive information about a single resource including
    all its fields, recent version history, and permission-based content visibility.
    It supports viewing both active and archived resources, with appropriate
    permission checks for sensitive fields like notes.
    
    Features:
        - Complete resource information display
        - Recent version history (last 5 versions)
        - Permission-based notes field visibility
        - Support for archived resource viewing
        - Role-based access control for sensitive data
        
    Template Context:
        - resource: The resource object being displayed
        - versions: Recent version history (last 5 versions)
        - can_view_notes: Boolean indicating if user can view notes field
        
    URL Parameters:
        - pk: Primary key of the resource to display
        
    Example:
        GET /resources/123/ -> Displays resource with ID 123
    """

    model = Resource
    template_name = "directory/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self) -> models.QuerySet:
        """Filter out deleted resources but include archived ones.
        
        This method ensures that deleted resources are not accessible while
        allowing archived resources to be viewed for historical purposes.
        
        Returns:
            models.QuerySet: Queryset including active and archived resources,
                            excluding deleted ones
        """
        return Resource.objects.all_including_archived()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context beyond the resource object,
        including version history and permission-based visibility flags.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - resource: The resource object (from parent)
                - versions: Recent version history (last 5 versions)
                - can_view_notes: Boolean indicating if user can view notes field
                
        Note:
            The can_view_notes flag controls visibility of the notes field
            based on user roles (Editor, Reviewer, or Admin required).
        """
        context = super().get_context_data(**kwargs)
        
        # Add permission context for notes field
        context['can_view_notes'] = user_has_role(self.request.user, "Editor") or user_has_role(self.request.user, "Reviewer") or user_has_role(self.request.user, "Admin")
        
        # Get recent versions
        context["versions"] = ResourceVersion.objects.filter(
            resource=self.object
        ).order_by("-changed_at")[:5]
        
        return context


# Import other resource views from their respective modules
from .resource_list_view import ResourceListView
from .resource_crud_views import ResourceCreateView, ResourceUpdateView

__all__ = [
    "ResourceDetailView",
    "ResourceListView", 
    "ResourceCreateView",
    "ResourceUpdateView",
]
