"""
Archive Views - Archive Management and Historical Resource Access

This module contains Django views for managing archived resources and providing
access to historical resource data. These views allow users to browse, search,
and view resources that have been archived (marked as inactive but preserved
for historical purposes).

Key Views:
    - ArchiveListView: Comprehensive listing of archived resources with search and filters
    - ArchiveDetailView: Individual archived resource display with version history

Features:
    - Full-text search using SQLite FTS5 with fallback
    - Advanced filtering by category, service type, and location
    - Archive statistics and category breakdowns
    - Complete version history access
    - Permission-based field visibility
    - Sorting by archive-specific fields

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
    from directory.views.archive_views import ArchiveListView, ArchiveDetailView

    # URL patterns typically map to these views
    # /archives/ -> ArchiveListView
    # /archives/<pk>/ -> ArchiveDetailView
"""

from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q
from django.views.generic import DetailView, ListView

from ..models import Resource, ServiceType, TaxonomyCategory
from ..permissions import user_has_role


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
        context["can_view_notes"] = (
            user_has_role(self.request.user, "Editor")
            or user_has_role(self.request.user, "Reviewer")
            or user_has_role(self.request.user, "Admin")
        )

        # Get version history
        context["versions"] = self.object.versions.all()[:10]

        return context
