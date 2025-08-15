"""
Resource Directory Views - HTTP Request Handlers for Resource Management

This module contains all Django views for the resource directory application,
providing HTTP request handling for resource management, search, filtering,
and workflow operations. The views implement both class-based and function-based
patterns to handle various user interactions and data operations.

Key Features:
    - Resource CRUD operations (Create, Read, Update)
    - Advanced search and filtering with FTS5
    - Workflow management (Draft → Needs Review → Published)
    - Archive management for inactive resources
    - Role-based access control and permissions
    - Public views for non-authenticated users
    - Version comparison and history tracking
    - Dashboard with analytics and metrics

View Categories:
    - List Views: Resource listing with search and filters
    - Detail Views: Individual resource display with version history
    - Form Views: Resource creation and editing
    - Action Views: Workflow transitions and status changes
    - Archive Views: Management of archived resources
    - Public Views: Non-authenticated access to published resources
    - Dashboard Views: Analytics and system overview

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-08-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - django.views.generic for class-based views
    - directory.models for data access
    - directory.forms for form handling
    - directory.permissions for access control
    - directory.utils for utility functions

Usage:
    from directory.views import ResourceListView, ResourceDetailView
    
    # URL patterns typically map to these views
    # /resources/ -> ResourceListView
    # /resources/<pk>/ -> ResourceDetailView
    # /resources/create/ -> ResourceCreateView

Examples:
    # Accessing a list view with search
    GET /resources/?q=mental+health&category=1&status=published
    
    # Creating a new resource
    POST /resources/create/ with form data
    
    # Publishing a resource
    POST /resources/<pk>/publish/
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView

from .forms import ResourceForm
from .models import Resource, ResourceVersion, ServiceType, TaxonomyCategory
from .permissions import (
    require_admin,
    require_editor,
    require_reviewer,
    user_can_publish,
    user_can_submit_for_review,
    user_can_hard_delete,
    user_has_role,
)
from .utils import compare_versions


class ResourceListView(LoginRequiredMixin, ListView):
    """List view for resources with advanced filtering, search, and pagination.
    
    This view provides a comprehensive listing of resources with multiple filtering
    options, full-text search capabilities, and pagination. It supports filtering
    by status, category, service type, location, and operational characteristics.
    The view also handles archive status filtering and provides context data for
    the template including filter options and user permissions.
    
    Features:
        - Full-text search using SQLite FTS5 with fallback to basic search
        - Multiple filter options (status, category, service type, location)
        - Archive status filtering (active vs archived resources)
        - Sorting by various fields
        - Pagination with configurable page size
        - Permission-based context data
        
    Template Context:
        - resources: Paginated queryset of filtered resources
        - categories: All taxonomy categories for filter dropdown
        - service_types: All service types for filter dropdown
        - status_choices: Available status options
        - current_filters: Current filter state for form persistence
        - user_can_publish: Boolean indicating user's publish permission
        - user_can_submit_review: Boolean indicating user's review submission permission
        
    URL Parameters:
        - q: Search query string
        - status: Filter by resource status (draft, needs_review, published)
        - category: Filter by taxonomy category ID
        - service_type: Filter by service type ID
        - city: Filter by city name (case-insensitive)
        - state: Filter by state code (case-insensitive)
        - county: Filter by county name (case-insensitive)
        - emergency: Filter by emergency service status (true/false)
        - hour24: Filter by 24-hour service status (true/false)
        - archive: Filter by archive status (archived/active)
        - sort: Sort order (name, -name, city, -city, status, -status, updated_at, -updated_at)
        - show_archived: Show archived resources (true/false)
        - page: Page number for pagination
        
    Example:
        GET /resources/?q=mental+health&category=1&status=published&sort=name&page=2
    """

    model = Resource
    template_name = "directory/resource_list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self) -> models.QuerySet:
        """Filter queryset based on search and filter parameters.
        
        This method builds a filtered queryset based on URL parameters including
        search queries, status filters, category filters, location filters, and
        operational characteristics. It uses SQLite FTS5 for full-text search
        with fallback to basic field matching if FTS5 fails.
        
        The method handles archive status filtering and applies various filters
        in sequence to build the final queryset. It also supports sorting by
        multiple fields.
        
        Returns:
            models.QuerySet: Filtered queryset of resources matching the criteria
            
        Note:
            This method processes URL parameters in the following order:
            1. Archive status (show_archived parameter)
            2. Search query (FTS5 with fallback)
            3. Status, category, service type filters
            4. Location filters (city, state, county)
            5. Operational filters (emergency, 24-hour)
            6. Sorting
        """
        # Start with non-archived resources by default
        queryset = Resource.objects.all()

        # Check if user wants to see archived resources
        show_archived = self.request.GET.get("show_archived", "").lower() == "true"
        if show_archived:
            queryset = Resource.objects.all_including_archived()
        else:
            queryset = Resource.objects.all()  # This uses the manager's default filter

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                # Apply archive filter to search results
                if show_archived:
                    queryset = search_results.filter(is_deleted=False)
                else:
                    queryset = search_results
            else:
                # Fallback to basic search if FTS5 fails
                queryset = queryset.filter(
                    Q(name__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(city__icontains=search_query)
                    | Q(state__icontains=search_query)
                )

        # Filters
        status_filter = self.request.GET.get("status", "")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        category_filter = self.request.GET.get("category", "")
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        service_type_filter = self.request.GET.get("service_type", "")
        if service_type_filter:
            queryset = queryset.filter(service_types_id=service_type_filter)

        city_filter = self.request.GET.get("city", "")
        if city_filter:
            queryset = queryset.filter(city__icontains=city_filter)

        state_filter = self.request.GET.get("state", "")
        if state_filter:
            queryset = queryset.filter(state__icontains=state_filter)

        county_filter = self.request.GET.get("county", "")
        if county_filter:
            queryset = queryset.filter(county__icontains=county_filter)

        emergency_filter = self.request.GET.get("emergency", "")
        if emergency_filter == "true":
            queryset = queryset.filter(is_emergency_service=True)
        elif emergency_filter == "false":
            queryset = queryset.filter(is_emergency_service=False)

        hour24_filter = self.request.GET.get("hour24", "")
        if hour24_filter == "true":
            queryset = queryset.filter(is_24_hour_service=True)
        elif hour24_filter == "false":
            queryset = queryset.filter(is_24_hour_service=False)

        # Archive filter
        archive_filter = self.request.GET.get("archive", "")
        if archive_filter == "archived":
            queryset = Resource.objects.archived()
        elif archive_filter == "active":
            queryset = Resource.objects.all()  # Non-archived only

        # Sorting
        sort_by = self.request.GET.get("sort", "-updated_at")
        if sort_by in [
            "name",
            "-name",
            "city",
            "-city",
            "status",
            "-status",
            "updated_at",
            "-updated_at",
        ]:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context data beyond the default queryset
        to support the template's filtering, search, and permission-based features.
        It includes filter options, current filter state for form persistence,
        and user permission flags.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - categories: All taxonomy categories for filter dropdown
                - service_types: All service types for filter dropdown  
                - status_choices: Available resource status options
                - current_filters: Current filter state for form persistence
                - user_can_publish: Boolean indicating user's publish permission
                - user_can_submit_review: Boolean indicating user's review submission permission
                
        Note:
            The current_filters dictionary preserves the user's filter selections
            across page loads, allowing the form to maintain its state.
        """
        context = super().get_context_data(**kwargs)

        # Add filter options
        context["categories"] = TaxonomyCategory.objects.all().order_by("name")
        context["service_types"] = ServiceType.objects.all().order_by("name")
        context["status_choices"] = Resource.STATUS_CHOICES

        # Add current filters for form persistence
        context["current_filters"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "category": self.request.GET.get("category", ""),
            "service_type": self.request.GET.get("service_type", ""),
            "city": self.request.GET.get("city", ""),
            "state": self.request.GET.get("state", ""),
            "sort": self.request.GET.get("sort", "-updated_at"),
        }

        # Add permission context
        context["user_can_publish"] = user_can_publish(self.request.user)
        context["user_can_submit_review"] = user_can_submit_for_review(
            self.request.user
        )

        return context


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
        display and form handling, including an action indicator.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - form: The ResourceForm instance
                - action: String indicating the action ("Create")
        """
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
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
        display and form handling, including an edit mode indicator.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - form: The ResourceForm instance
                - resource: The resource object being edited
                - is_edit: Boolean flag indicating edit mode (True)
        """
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form: ResourceForm) -> HttpResponse:
        """Handle form validation and update user tracking.
        
        This method is called when the form is valid and ready to save.
        It automatically sets the updated_by field to the current user
        before saving the resource.
        
        Args:
            form: The validated ResourceForm instance
            
        Returns:
            HttpResponse: Redirect response to the success URL
        """
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Redirect to the resource detail page.
        
        This method determines where to redirect after a successful update.
        It redirects to the detail view of the updated resource.
        
        Returns:
            str: URL for the resource detail page
        """
        return reverse("directory:resource_detail", kwargs={"pk": self.object.pk})


class ArchiveListView(LoginRequiredMixin, ListView):
    """List view for archived resources with search, filtering, and statistics.
    
    This view provides a comprehensive listing of archived resources with search
    capabilities, filtering options, and archive statistics. It allows users to
    browse and search through resources that have been archived (marked as inactive
    but preserved for historical purposes).
    
    Features:
        - Full-text search using SQLite FTS5 with fallback to basic search
        - Multiple filter options (category, service type, location)
        - Sorting by various fields including archive-specific fields
        - Pagination with configurable page size
        - Archive statistics and category breakdowns
        
    Template Context:
        - resources: Paginated queryset of archived resources
        - categories: All taxonomy categories for filter dropdown
        - service_types: All service types for filter dropdown
        - total_archived: Total count of archived resources
        - archived_by_category: Dictionary of category names and their archived resource counts
        
    URL Parameters:
        - q: Search query string
        - category: Filter by taxonomy category ID
        - service_type: Filter by service type ID
        - city: Filter by city name (case-insensitive)
        - state: Filter by state code (case-insensitive)
        - county: Filter by county name (case-insensitive)
        - sort: Sort order (name, -name, city, -city, archived_at, -archived_at, archived_by, -archived_by)
        - page: Page number for pagination
        
    Example:
        GET /archive/?q=mental+health&category=1&sort=-archived_at&page=2
    """

    model = Resource
    template_name = "directory/archive_list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self) -> models.QuerySet:
        """Get only archived resources with search and filtering.
        
        This method builds a filtered queryset of archived resources based on
        URL parameters. It supports full-text search using SQLite FTS5 with
        fallback to basic field matching, and applies various filters for
        category, service type, and location.
        
        Returns:
            models.QuerySet: Filtered queryset of archived resources matching the criteria
            
        Note:
            This method processes URL parameters in the following order:
            1. Base archived resources queryset
            2. Search query (FTS5 with fallback)
            3. Category, service type, location filters
            4. Sorting
        """
        queryset = Resource.objects.archived()

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                queryset = search_results.filter(is_archived=True, is_deleted=False)
            else:
                # Fallback to basic search if FTS5 fails
                queryset = queryset.filter(
                    Q(name__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(city__icontains=search_query)
                    | Q(state__icontains=search_query)
                )

        # Filters
        category_filter = self.request.GET.get("category", "")
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        service_type_filter = self.request.GET.get("service_type", "")
        if service_type_filter:
            queryset = queryset.filter(service_types_id=service_type_filter)

        city_filter = self.request.GET.get("city", "")
        if city_filter:
            queryset = queryset.filter(city__icontains=city_filter)

        state_filter = self.request.GET.get("state", "")
        if state_filter:
            queryset = queryset.filter(state__icontains=state_filter)

        county_filter = self.request.GET.get("county", "")
        if county_filter:
            queryset = queryset.filter(county__icontains=county_filter)

        # Sorting
        sort_by = self.request.GET.get("sort", "-archived_at")
        if sort_by in [
            "name",
            "-name",
            "city",
            "-city",
            "archived_at",
            "-archived_at",
            "archived_by",
            "-archived_by",
        ]:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context data beyond the archived resources
        queryset, including filter options and archive statistics for the template.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - resources: Paginated queryset of archived resources
                - categories: All taxonomy categories for filter dropdown
                - service_types: All service types for filter dropdown
                - total_archived: Total count of archived resources
                - archived_by_category: Dictionary mapping category names to their archived resource counts
                
        Note:
            The archived_by_category dictionary only includes categories that have
            archived resources (count > 0) to avoid cluttering the interface.
        """
        context = super().get_context_data(**kwargs)
        
        # Get filter options
        context["categories"] = TaxonomyCategory.objects.all().order_by("name")
        context["service_types"] = ServiceType.objects.all().order_by("name")
        
        # Get archive statistics
        context["total_archived"] = Resource.objects.archived().count()
        context["archived_by_category"] = {}
        for category in TaxonomyCategory.objects.all():
            count = Resource.objects.archived().filter(category=category).count()
            if count > 0:
                context["archived_by_category"][category.name] = count

        return context


class ArchiveDetailView(LoginRequiredMixin, DetailView):
    """Detail view for archived resources with version history and permissions.
    
    This view displays comprehensive information about an archived resource including
    all its fields, complete version history, and permission-based content visibility.
    It provides access to historical data while maintaining appropriate permission
    checks for sensitive fields like notes.
    
    Features:
        - Complete archived resource information display
        - Full version history (up to 10 versions)
        - Permission-based notes field visibility
        - Role-based access control for sensitive data
        - Historical data preservation
        
    Template Context:
        - resource: The archived resource object being displayed
        - versions: Complete version history (up to 10 versions)
        - can_view_notes: Boolean indicating if user can view notes field
        
    URL Parameters:
        - pk: Primary key of the archived resource to display
        
    Example:
        GET /archive/123/ -> Displays archived resource with ID 123
    """

    model = Resource
    template_name = "directory/archive_detail.html"
    context_object_name = "resource"

    def get_queryset(self) -> models.QuerySet:
        """Get only archived resources.
        
        This method ensures that only archived resources are accessible through
        this view, maintaining the separation between active and archived data.
        
        Returns:
            models.QuerySet: Queryset containing only archived resources
        """
        return Resource.objects.archived()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data for the template.
        
        This method provides additional context beyond the archived resource object,
        including version history and permission-based visibility flags.
        
        Args:
            **kwargs: Additional keyword arguments passed to the parent method
            
        Returns:
            Dict[str, Any]: Context dictionary containing:
                - resource: The archived resource object (from parent)
                - versions: Complete version history (up to 10 versions)
                - can_view_notes: Boolean indicating if user can view notes field
                
        Note:
            The can_view_notes flag controls visibility of the notes field
            based on user roles (Editor, Reviewer, or Admin required).
            Version history is limited to 10 versions to prevent performance issues.
        """
        context = super().get_context_data(**kwargs)
        
        # Add permission context for notes field
        context['can_view_notes'] = user_has_role(self.request.user, "Editor") or user_has_role(self.request.user, "Reviewer") or user_has_role(self.request.user, "Admin")
        
        # Get version history
        context["versions"] = self.object.versions.all()[:10]
        
        return context


@login_required
@require_http_methods(["POST"])
def submit_for_review(request: HttpRequest, pk: int) -> HttpResponse:
    """Submit a resource for review with validation and permission checks.
    
    This view handles the workflow transition from draft to needs_review status.
    It validates that the user has permission to submit resources for review and
    ensures the resource meets all requirements for the needs_review status.
    
    Features:
        - Permission validation (Editor, Reviewer, or Admin required)
        - Resource validation for needs_review status requirements
        - Error handling with descriptive error messages
        - Status transition with automatic validation
        
    Args:
        request: The HTTP request object
        pk: Primary key of the resource to submit for review
        
    Returns:
        HttpResponse: Success message or error response with appropriate status code
        
    Raises:
        404: If the resource is not found or is deleted
        403: If the user lacks permission to submit for review
        400: If the resource fails validation for needs_review status
        
    Example:
        POST /resources/123/submit-for-review/ -> Submit resource 123 for review
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_submit_for_review(request.user):
        return HttpResponse("Permission denied", status=403)

    # Validate that the resource meets review requirements
    try:
        resource.status = "needs_review"
        resource.full_clean()
        resource.save()
        return HttpResponse("Resource submitted for review successfully")
    except Exception as e:
        return HttpResponse(f"Validation error: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def publish_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish a resource with verification and permission checks.
    
    This view handles the workflow transition from needs_review to published status.
    It validates that the user has permission to publish resources and ensures
    the resource meets all requirements for the published status. It also sets
    verification metadata including timestamp and verifier.
    
    Features:
        - Permission validation (Reviewer or Admin required)
        - Resource validation for published status requirements
        - Automatic verification metadata setting
        - Error handling with descriptive error messages
        - Status transition with automatic validation
        
    Args:
        request: The HTTP request object
        pk: Primary key of the resource to publish
        
    Returns:
        HttpResponse: Success message or error response with appropriate status code
        
    Raises:
        404: If the resource is not found or is deleted
        403: If the user lacks permission to publish resources
        400: If the resource fails validation for published status
        
    Example:
        POST /resources/123/publish/ -> Publish resource 123
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_publish(request.user):
        return HttpResponse("Permission denied", status=403)

    # Validate that the resource meets publish requirements
    try:
        from django.utils import timezone

        resource.status = "published"
        resource.last_verified_at = timezone.now()
        resource.last_verified_by = request.user
        resource.full_clean()
        resource.save()
        return HttpResponse("Resource published successfully")
    except Exception as e:
        return HttpResponse(f"Validation error: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def unpublish_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Unpublish a resource with permission checks and status reversion.
    
    This view handles the workflow transition from published back to needs_review status.
    It validates that the user has permission to unpublish resources and reverts
    the resource status while updating the user tracking information.
    
    Features:
        - Permission validation (Reviewer or Admin required)
        - Status reversion from published to needs_review
        - User tracking update
        - Error handling with descriptive error messages
        
    Args:
        request: The HTTP request object
        pk: Primary key of the resource to unpublish
        
    Returns:
        HttpResponse: Success message or error response with appropriate status code
        
    Raises:
        404: If the resource is not found or is deleted
        PermissionDenied: If the user lacks permission to unpublish resources
        
    Example:
        POST /resources/123/unpublish/ -> Unpublish resource 123
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)
    
    if not user_can_publish(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access denied. Requires Reviewer or Admin role.")

    resource.status = "needs_review"
    resource.updated_by = request.user
    resource.save()

    return HttpResponse("Resource unpublished successfully")


@login_required
@require_http_methods(["POST"])
def archive_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Archive a resource with reason tracking and permission validation.
    
    This view handles the archival of resources, moving them from active status
    to archived status while preserving all data for historical purposes. It
    requires a reason for archiving and validates user permissions.
    
    Features:
        - Permission validation (Admin role required)
        - Archive reason requirement and tracking
        - Automatic timestamp and user assignment
        - User tracking update
        - Error handling with descriptive error messages
        - Redirect to detail page for better UX
        
    Args:
        request: The HTTP request object containing POST data
        pk: Primary key of the resource to archive
        
    Returns:
        HttpResponse: Redirect response to resource detail page or error response
        
    Raises:
        404: If the resource is not found or is already archived
        PermissionDenied: If the user lacks permission to archive resources
        400: If archive reason is missing or archiving fails
        
    POST Data:
        - archive_reason: Required string explaining why the resource is being archived
        
    Example:
        POST /resources/123/archive/ with archive_reason="Organization closed"
    """
    from django.utils import timezone
    
    # Use the manager's all_including_archived method to get the resource
    resource = get_object_or_404(Resource.objects.all_including_archived(), pk=pk, is_archived=False)
    
    if not user_can_hard_delete(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access denied. Requires Admin role.")

    # Get archive reason from POST data
    archive_reason = request.POST.get("archive_reason", "").strip()
    
    if not archive_reason:
        return HttpResponse("Archive reason is required", status=400)

    try:
        resource.is_archived = True
        resource.archived_at = timezone.now()
        resource.archived_by = request.user
        resource.archive_reason = archive_reason
        resource.updated_by = request.user
        resource.save()
        # Redirect back to detail page for UX
        return redirect("directory:resource_detail", pk=resource.pk)
    except Exception as e:
        return HttpResponse(f"Error archiving resource: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def unarchive_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Unarchive a resource with permission validation and metadata cleanup.
    
    This view handles the restoration of archived resources, moving them back
    to active status. It validates user permissions and cleans up archive-related
    metadata while preserving the resource data.
    
    Features:
        - Permission validation (Admin role required)
        - Archive metadata cleanup (timestamp, user, reason)
        - User tracking update
        - Redirect to detail page for better UX
        
    Args:
        request: The HTTP request object
        pk: Primary key of the archived resource to unarchive
        
    Returns:
        HttpResponse: Redirect response to resource detail page
        
    Raises:
        404: If the resource is not found or is not archived
        PermissionDenied: If the user lacks permission to unarchive resources
        
    Example:
        POST /resources/123/unarchive/ -> Restore archived resource 123
    """
    # Use the manager's archived method to get the resource
    resource = get_object_or_404(Resource.objects.archived(), pk=pk)
    
    if not user_can_hard_delete(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access denied. Requires Admin role.")

    resource.is_archived = False
    resource.archived_at = None
    resource.archived_by = None
    resource.archive_reason = ""
    resource.updated_by = request.user
    resource.save()

    return redirect("directory:resource_detail", pk=resource.pk)


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view with comprehensive resource analytics and metrics.
    
    This view provides an overview of the resource directory system with
    key metrics, counts by status, verification tracking, and recent activity.
    It serves as the main administrative dashboard for monitoring system health
    and resource management status.
    
    Features:
        - Resource counts by status (draft, needs_review, published, archived)
        - Verification tracking for published resources
        - Recent activity monitoring
        - System health indicators
        - Administrative overview
        
    Template Context:
        - draft_count: Number of resources in draft status
        - review_count: Number of resources awaiting review
        - published_count: Number of published resources
        - archived_count: Number of archived resources
        - needs_verification: Number of published resources needing verification
        - recent_resources: List of recently updated resources (last 10)
        
    Returns:
        HttpResponse: Rendered dashboard template with analytics data
        
    Example:
        GET /dashboard/ -> Display system dashboard with metrics
    """
    # Get resource counts by status
    draft_count = Resource.objects.filter(status="draft", is_deleted=False).count()
    review_count = Resource.objects.filter(
        status="needs_review", is_deleted=False
    ).count()
    published_count = Resource.objects.filter(
        status="published", is_deleted=False
    ).count()

    # Get archived count
    archived_count = Resource.objects.archived().count()

    # Get resources needing verification
    from datetime import timedelta

    from django.conf import settings
    from django.utils import timezone

    verification_threshold = timezone.now() - timedelta(
        days=settings.VERIFICATION_EXPIRY_DAYS
    )
    needs_verification = Resource.objects.filter(
        status="published",
        is_deleted=False,
        last_verified_at__lt=verification_threshold,
    ).count()

    # Get recent activity
    recent_resources = Resource.objects.filter(is_deleted=False).order_by(
        "-updated_at"
    )[:10]

    context = {
        "draft_count": draft_count,
        "review_count": review_count,
        "published_count": published_count,
        "archived_count": archived_count,
        "needs_verification": needs_verification,
        "recent_resources": recent_resources,
    }

    return render(request, "directory/dashboard.html", context)


@login_required
def version_comparison(
    request: HttpRequest, resource_pk: int, version1_pk: int, version2_pk: int = None
) -> HttpResponse:
    """Compare two versions of a resource with detailed difference analysis.
    
    This view provides a side-by-side comparison of two versions of a resource,
    highlighting the differences between them. It can compare any two historical
    versions or compare a historical version with the current state of the resource.
    
    Features:
        - Side-by-side version comparison
        - Detailed difference highlighting
        - Support for comparing historical versions or current state
        - Comprehensive field comparison
        - User-friendly difference presentation
        
    Args:
        request: The HTTP request object
        resource_pk: Primary key of the resource to compare versions for
        version1_pk: Primary key of the first version to compare
        version2_pk: Primary key of the second version to compare (optional, defaults to current)
        
    Returns:
        HttpResponse: Rendered version comparison template with difference data
        
    Raises:
        404: If the resource or version is not found
        
    Template Context:
        - resource: The resource object being compared
        - version1: The first version object
        - version2_label: Label for the second version ("Current" or "vX")
        - differences: Dictionary of field differences between versions
        - version1_snapshot: Complete snapshot data for version 1
        - version2_snapshot: Complete snapshot data for version 2
        
    Example:
        GET /resources/123/versions/1/compare/ -> Compare version 1 with current
        GET /resources/123/versions/1/compare/2/ -> Compare version 1 with version 2
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)
    version1 = get_object_or_404(ResourceVersion, pk=version1_pk, resource=resource)

    # If no second version specified, compare with current resource state
    if version2_pk:
        version2 = get_object_or_404(ResourceVersion, pk=version2_pk, resource=resource)
        current_snapshot = version2.snapshot
        version2_label = f"v{version2.version_number}"
    else:
        # Create current snapshot for comparison
        current_snapshot = {
            "name": resource.name,
            "category": resource.category.name if resource.category else "",
            "description": resource.description,
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "status": resource.status,
            "source": resource.source,
            "last_verified_at": (
                resource.last_verified_at.isoformat()
                if resource.last_verified_at
                else ""
            ),
            "last_verified_by": (
                resource.last_verified_by.get_full_name()
                if resource.last_verified_by
                else ""
            ),
        }
        version2_label = "Current"

    # Compare the versions
    differences = compare_versions(version1.snapshot, current_snapshot)

    context = {
        "resource": resource,
        "version1": version1,
        "version2_label": version2_label,
        "differences": differences,
        "version1_snapshot": version1.snapshot,
        "version2_snapshot": current_snapshot,
    }

    return render(request, "directory/version_comparison.html", context)


@login_required
def version_history(request: HttpRequest, resource_pk: int) -> HttpResponse:
    """Show complete version history for a resource with chronological ordering.
    
    This view displays the complete version history of a resource, showing all
    changes made over time in chronological order. It provides access to the
    full audit trail for transparency and historical tracking.
    
    Features:
        - Complete version history display
        - Chronological ordering (newest first)
        - Access to all historical snapshots
        - Audit trail transparency
        - Historical change tracking
        
    Args:
        request: The HTTP request object
        resource_pk: Primary key of the resource to show version history for
        
    Returns:
        HttpResponse: Rendered version history template with complete version list
        
    Raises:
        404: If the resource is not found
        
    Template Context:
        - resource: The resource object
        - versions: Complete list of all versions ordered by version number (descending)
        
    Example:
        GET /resources/123/versions/ -> Display complete version history for resource 123
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)
    versions = resource.versions.all().order_by("-version_number")

    context = {
        "resource": resource,
        "versions": versions,
    }

    return render(request, "directory/version_history.html", context)

# Public views (no authentication required)
def public_home(request: HttpRequest) -> HttpResponse:
    """Public home page showing resources organized by category and service type.
    
    This view provides a public-facing overview of available resources, organized
    by category and service type with comprehensive statistics. It serves as the
    main landing page for non-authenticated users, showcasing the breadth of
    available services.
    
    Features:
        - Public access without authentication
        - Resource organization by category and service type
        - Comprehensive statistics and counts
        - Emergency and 24-hour service highlighting
        - Optimized database queries with select_related and prefetch_related
        
    Template Context:
        - categories: All categories with published resources
        - service_types: All service types with published resources
        - category_counts: Dictionary mapping category IDs to resource counts
        - service_type_counts: Dictionary mapping service type IDs to resource counts
        - emergency_count: Number of emergency services
        - twenty_four_hour_count: Number of 24-hour services
        - total_resources: Total number of published resources
        
    Returns:
        HttpResponse: Rendered public home template with resource overview
        
    Example:
        GET / -> Display public home page with resource statistics
    """
    # Get all published, non-archived resources
    resources = Resource.objects.filter(
        status="published", 
        is_deleted=False, 
        is_archived=False
    ).select_related('category').prefetch_related('service_types')
    
    # Get all categories with published resources
    categories = TaxonomyCategory.objects.filter(
        resources__status="published",
        resources__is_deleted=False,
        resources__is_archived=False
    ).distinct().order_by('name')
    
    # Get all service types with published resources
    service_types = ServiceType.objects.filter(
        resources__status="published",
        resources__is_deleted=False,
        resources__is_archived=False
    ).distinct().order_by('name')
    
    # Count resources by category
    category_counts = {}
    for category in categories:
        category_counts[category.id] = resources.filter(category=category).count()
    
    # Count resources by service type
    service_type_counts = {}
    for service_type in service_types:
        service_type_counts[service_type.id] = resources.filter(service_types=service_type).count()
    
    # Get emergency services count
    emergency_count = resources.filter(is_emergency_service=True).count()
    
    # Get 24-hour services count
    twenty_four_hour_count = resources.filter(is_24_hour_service=True).count()
    
    context = {
        'categories': categories,
        'service_types': service_types,
        'category_counts': category_counts,
        'service_type_counts': service_type_counts,
        'emergency_count': emergency_count,
        'twenty_four_hour_count': twenty_four_hour_count,
        'total_resources': resources.count(),
    }
    
    return render(request, 'directory/public_home.html', context)


def public_resource_list(request: HttpRequest) -> HttpResponse:
    """Public resource list view with comprehensive filtering and search capabilities.
    
    This view provides a public-facing list of published resources with advanced
    search, filtering, and sorting capabilities. It allows non-authenticated users
    to discover and browse available services based on various criteria.
    
    Features:
        - Public access without authentication
        - Full-text search using SQLite FTS5 with fallback
        - Multiple filter options (category, service type, location, operational)
        - Sorting by various fields
        - Pagination for large result sets
        - Optimized database queries
        - Comprehensive filter options in sidebar
        
    URL Parameters:
        - q: Search query string
        - category: Filter by taxonomy category ID
        - service_type: Filter by service type ID
        - city: Filter by city name (case-insensitive)
        - state: Filter by state code (case-insensitive)
        - emergency: Filter by emergency service status (true/false)
        - 24hour: Filter by 24-hour service status (true/false)
        - sort: Sort order (name, city, category, emergency)
        - page: Page number for pagination
        
    Template Context:
        - page_obj: Paginated queryset of filtered resources
        - search_query: Current search query
        - category_filter: Current category filter
        - service_type_filter: Current service type filter
        - city_filter: Current city filter
        - state_filter: Current state filter
        - emergency_filter: Current emergency filter
        - twenty_four_hour_filter: Current 24-hour filter
        - sort_by: Current sort order
        - categories: All categories with published resources
        - service_types: All service types with published resources
        - categories_dict: Dictionary mapping category IDs to names
        - service_types_dict: Dictionary mapping service type IDs to names
        - cities: List of unique cities with published resources
        - states: List of unique states with published resources
        
    Returns:
        HttpResponse: Rendered public resource list template with filtered data
        
    Example:
        GET /resources/public/?q=mental+health&category=1&sort=name&page=2
    """
    # Start with published, non-archived resources
    queryset = Resource.objects.filter(
        status="published", 
        is_deleted=False, 
        is_archived=False
    ).select_related('category').prefetch_related('service_types')
    
    # Search functionality
    search_query = request.GET.get("q", "").strip()
    if search_query:
        search_results = Resource.objects.search_combined(search_query)
        if search_results.exists():
            queryset = search_results.filter(
                status="published", 
                is_deleted=False, 
                is_archived=False
            )
        else:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(city__icontains=search_query)
                | Q(state__icontains=search_query)
            )
    
    # Filter by category
    category_filter = request.GET.get("category", "")
    if category_filter:
        queryset = queryset.filter(category_id=category_filter)
    
    # Filter by service type
    service_type_filter = request.GET.get("service_type", "")
    if service_type_filter:
        queryset = queryset.filter(service_types__id=service_type_filter)
    
    # Filter by city
    city_filter = request.GET.get("city", "")
    if city_filter:
        queryset = queryset.filter(city__icontains=city_filter)
    
    # Filter by state
    state_filter = request.GET.get("state", "")
    if state_filter:
        queryset = queryset.filter(state__icontains=state_filter)
    
    # Filter by emergency services
    emergency_filter = request.GET.get("emergency", "")
    if emergency_filter == "true":
        queryset = queryset.filter(is_emergency_service=True)
    elif emergency_filter == "false":
        queryset = queryset.filter(is_emergency_service=False)
    
    # Filter by 24-hour services
    twenty_four_hour_filter = request.GET.get("24hour", "")
    if twenty_four_hour_filter == "true":
        queryset = queryset.filter(is_24_hour_service=True)
    elif twenty_four_hour_filter == "false":
        queryset = queryset.filter(is_24_hour_service=False)
    
    # Sorting
    sort_by = request.GET.get("sort", "name")
    if sort_by == "name":
        queryset = queryset.order_by("name")
    elif sort_by == "city":
        queryset = queryset.order_by("city", "name")
    elif sort_by == "category":
        queryset = queryset.order_by("category__name", "name")
    elif sort_by == "emergency":
        queryset = queryset.order_by("-is_emergency_service", "name")
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for the sidebar
    categories = TaxonomyCategory.objects.filter(
        resources__status="published",
        resources__is_deleted=False,
        resources__is_archived=False
    ).distinct().order_by('name')
    
    service_types = ServiceType.objects.filter(
        resources__status="published",
        resources__is_deleted=False,
        resources__is_archived=False
    ).distinct().order_by('name')
    
    # Create dictionaries for template filter usage
    categories_dict = {str(cat.id): cat.name for cat in categories}
    service_types_dict = {str(st.id): st.name for st in service_types}
    
    # Get unique cities and states for filters
    cities = Resource.objects.filter(
        status="published", 
        is_deleted=False, 
        is_archived=False
    ).exclude(city="").values_list('city', flat=True).distinct().order_by('city')
    
    states = Resource.objects.filter(
        status="published", 
        is_deleted=False, 
        is_archived=False
    ).exclude(state="").values_list('state', flat=True).distinct().order_by('state')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'service_type_filter': service_type_filter,
        'city_filter': city_filter,
        'state_filter': state_filter,
        'emergency_filter': emergency_filter,
        'twenty_four_hour_filter': twenty_four_hour_filter,
        'sort_by': sort_by,
        'categories': categories,
        'service_types': service_types,
        'categories_dict': categories_dict,
        'service_types_dict': service_types_dict,
        'cities': cities,
        'states': states,
    }
    
    return render(request, 'directory/public_resource_list.html', context)


def public_resource_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Public resource detail view for published resources with related resource suggestions.
    
    This view displays comprehensive information about a published resource for
    non-authenticated users. It includes related resource suggestions based on
    category and service type similarities to help users discover additional
    relevant services.
    
    Features:
        - Public access without authentication
        - Complete resource information display
        - Related resource suggestions
        - Category and service type-based recommendations
        - Deduplication of related resources
        - Limited to published, non-archived resources
        
    Args:
        request: The HTTP request object
        pk: Primary key of the published resource to display
        
    Returns:
        HttpResponse: Rendered public resource detail template with resource and related data
        
    Raises:
        404: If the resource is not found, not published, or is archived/deleted
        
    Template Context:
        - resource: The published resource object
        - related_resources: List of related resources (up to 5, deduplicated)
        
    Example:
        GET /resources/public/123/ -> Display published resource 123 with related suggestions
    """
    resource = get_object_or_404(
        Resource, 
        pk=pk, 
        status="published", 
        is_deleted=False, 
        is_archived=False
    )
    
    # Get related resources (same category or service types)
    related_resources = Resource.objects.filter(
        status="published",
        is_deleted=False,
        is_archived=False
    ).exclude(pk=resource.pk)
    
    if resource.category:
        category_related = related_resources.filter(category=resource.category)[:3]
    else:
        category_related = []
    
    if resource.service_types.exists():
        service_related = related_resources.filter(
            service_types__in=resource.service_types.all()
        ).distinct()[:3]
    else:
        service_related = []
    
    # Combine and deduplicate related resources
    related = list(category_related) + list(service_related)
    related = list({r.pk: r for r in related}.values())[:5]
    
    context = {
        'resource': resource,
        'related_resources': related,
    }
    
    return render(request, 'directory/public_resource_detail.html', context)


def custom_logout(request: HttpRequest) -> HttpResponse:
    """Custom logout view that redirects to the public home page.
    
    This view handles user logout by clearing the session and redirecting
    to the public home page instead of the default Django logout behavior.
    It provides a seamless transition from authenticated to public access.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Redirect response to the public home page
        
    Example:
        GET /logout/ -> Log out user and redirect to public home page
    """
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    
    logout(request)
    return redirect('directory:public_home')
