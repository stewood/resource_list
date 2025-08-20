"""
Resource List View - Advanced Resource Listing with Search and Filtering

This module contains the ResourceListView which provides comprehensive resource
listing functionality with advanced search, filtering, and pagination capabilities.

Features:
    - Full-text search using SQLite FTS5 with fallback
    - Advanced filtering by status, category, location, and operational characteristics
    - Archive status filtering (active vs archived resources)
    - Sorting by various fields
    - Pagination with configurable page size
    - Permission-based context data

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.views.resource_list_view import ResourceListView
    
    # URL patterns typically map to this view
    # /resources/ -> ResourceListView
"""

from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q
from django.views.generic import ListView

from ..models import Resource, ServiceType, TaxonomyCategory
from ..permissions import user_can_publish, user_can_submit_for_review


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
        queryset = Resource.objects.all().select_related('category').prefetch_related('service_types', 'coverage_areas')

        # Check if user wants to see archived resources
        show_archived = self.request.GET.get("show_archived", "").lower() == "true"
        if show_archived:
            queryset = Resource.objects.all_including_archived().select_related('category').prefetch_related('service_types', 'coverage_areas')
        else:
            queryset = Resource.objects.all().select_related('category').prefetch_related('service_types', 'coverage_areas')  # This uses the manager's default filter

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                # Apply archive filter to search results
                if show_archived:
                    queryset = search_results.filter(is_deleted=False).select_related('category').prefetch_related('service_types', 'coverage_areas')
                else:
                    queryset = search_results.select_related('category').prefetch_related('service_types', 'coverage_areas')
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
