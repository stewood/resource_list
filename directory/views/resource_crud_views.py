"""
Resource CRUD Views - Create and Update Operations

This module contains the Create and Update views for resources, providing
comprehensive CRUD functionality with permission checks and user tracking.

Features:
    - Permission-based access control (Editor, Reviewer, or Admin required)
    - Automatic user assignment for created_by and updated_by fields
    - Form validation with user context
    - Support for editing both active and archived resources

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.views.resource_crud_views import ResourceCreateView, ResourceUpdateView
    
    # URL patterns typically map to these views
    # /resources/create/ -> ResourceCreateView
    # /resources/<pk>/edit/ -> ResourceUpdateView
"""

from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from ..forms import ResourceForm
from ..models import Resource
from ..permissions import user_can_submit_for_review


class ResourceCreateView(LoginRequiredMixin, CreateView):
    """Create view for new resources with permission checks and user assignment.
    
    This view handles the creation of new resources with comprehensive permission
    validation and automatic user assignment. It ensures that only authorized users
    can create resources and automatically sets the creator and updater fields.
    
    Features:
        - Permission-based access control (Editor, Reviewer, or Admin required)
        - Automatic user assignment for created_by and updated_by fields
        - Form validation with user context
        - Redirect to resource list on successful creation
        
    Template Context:
        - form: ResourceForm instance for resource creation
        - action: String indicating the action ("Create")
        
    URL Parameters:
        None (form-based creation)
        
    Example:
        GET /resources/create/ -> Display creation form
        POST /resources/create/ -> Process form and create resource
    """

    model = Resource
    form_class = ResourceForm
    template_name = "directory/resource_form.html"
    success_url = reverse_lazy("directory:resource_list")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check permissions before processing the request.
        
        This method validates that the user has permission to create resources
        before allowing access to the view. It checks for Editor, Reviewer, or
        Admin role and raises PermissionDenied if the user lacks appropriate
        permissions.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The response from the parent dispatch method
            
        Raises:
            PermissionDenied: If user lacks permission to create resources
        """
        if not user_can_submit_for_review(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Access denied. Requires Editor, Reviewer, or Admin role.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Pass user to form for validation.
        
        This method adds the current user to the form's keyword arguments,
        allowing the form to perform user-specific validation and permission
        checks during form processing.
        
        Returns:
            Dict[str, Any]: Form keyword arguments including the user
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: ResourceForm) -> HttpResponse:
        """Set the user who created the resource.
        
        This method is called when the form is valid and ready to save.
        It automatically sets the created_by and updated_by fields to the
        current user before saving the resource.
        
        Args:
            form: The validated ResourceForm instance
            
        Returns:
            HttpResponse: Redirect response to the success URL
        """
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context data to support the template's
        display and form handling, including an action indicator and service areas data.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - form: The ResourceForm instance
                - action: String indicating the action ("Create")
                - service_areas_data: JSON string of existing service areas (empty for new resources)
        """
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        context["service_areas_data"] = "[]"  # Empty for new resources
        return context


class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for existing resources with permission checks and user tracking.
    
    This view handles the editing of existing resources with comprehensive permission
    validation and automatic user tracking. It ensures that only authorized users
    can edit resources and automatically updates the updated_by field on changes.
    
    Features:
        - Permission-based access control (Editor, Reviewer, or Admin required)
        - Automatic user assignment for updated_by field
        - Form validation with user context
        - Support for editing both active and archived resources
        - Redirect to resource detail page on successful update
        
    Template Context:
        - form: ResourceForm instance for resource editing
        - resource: The resource object being edited
        - is_edit: Boolean flag indicating edit mode (True)
        
    URL Parameters:
        - pk: Primary key of the resource to edit
        
    Example:
        GET /resources/123/edit/ -> Display edit form for resource 123
        POST /resources/123/edit/ -> Process form and update resource 123
    """

    model = Resource
    form_class = ResourceForm
    template_name = "directory/resource_form.html"
    context_object_name = "resource"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check permissions before processing the request.
        
        This method validates that the user has permission to edit resources
        before allowing access to the view. It checks for Editor, Reviewer, or
        Admin role and raises PermissionDenied if the user lacks appropriate
        permissions.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The response from the parent dispatch method
            
        Raises:
            PermissionDenied: If user lacks permission to edit resources
        """
        if not user_can_submit_for_review(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Access denied. Requires Editor, Reviewer, or Admin role.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> models.QuerySet:
        """Filter out deleted resources but include archived ones.
        
        This method ensures that deleted resources are not accessible while
        allowing both active and archived resources to be edited.
        
        Returns:
            models.QuerySet: Queryset including active and archived resources,
                            excluding deleted ones
        """
        return Resource.objects.all_including_archived()

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Pass user to form for validation.
        
        This method adds the current user to the form's keyword arguments,
        allowing the form to perform user-specific validation and permission
        checks during form processing.
        
        Returns:
            Dict[str, Any]: Form keyword arguments including the user
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context data to support the template's
        display and form handling, including an edit mode indicator and service areas data.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - form: The ResourceForm instance
                - resource: The resource object being edited
                - is_edit: Boolean flag indicating edit mode (True)
                - service_areas_data: JSON string of existing service areas
        """
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        
        # Add existing service areas data
        import json
        service_areas = []
        if self.object and hasattr(self.object, 'coverage_areas'):
            service_areas = [
                {
                    'id': area.id,
                    'name': area.name,
                    'type': area.kind.lower(),
                    'source': 'existing',
                    'attached_at': area.created_at.isoformat() if area.created_at else None,
                    'attached_by': area.created_by.username if area.created_by else None
                }
                for area in self.object.coverage_areas.all()
            ]
        context["service_areas_data"] = json.dumps(service_areas)
        
        return context

    def form_valid(self, form: ResourceForm) -> HttpResponse:
        """Handle form validation and update user tracking.
        
        This method is called when the form is valid and ready to save.
        It automatically sets the updated_by field to the current user
        and transitions published resources to needs_review status.
        
        Args:
            form: The validated ResourceForm instance
            
        Returns:
            HttpResponse: Redirect response to the success URL
        """
        # Capture original status before changes
        original_status = form.instance.status
        
        # Set the user who is making the change
        form.instance.updated_by = self.request.user
        
        # If resource was published and is being edited, move to needs_review
        if original_status == "published":
            form.instance.status = "needs_review"
            # Clear verification data since it needs re-verification
            form.instance.last_verified_at = None
            form.instance.last_verified_by = None
        
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Redirect to the resource detail page.
        
        This method determines where to redirect after a successful update.
        It redirects to the detail view of the updated resource.
        
        Returns:
            str: URL for the resource detail page
        """
        return reverse("directory:resource_detail", kwargs={"pk": self.object.pk})
