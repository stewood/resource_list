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

import logging
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q
from django.views.generic import ListView

from ..models import Resource, ServiceType, TaxonomyCategory
from ..permissions import user_can_publish, user_can_submit_for_review

logger = logging.getLogger(__name__)


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
        queryset = (
            Resource.objects.all()
            .select_related("category")
            .prefetch_related("service_types", "coverage_areas")
        )

        # Check if user wants to see archived resources
        show_archived = self.request.GET.get("show_archived", "").lower() == "true"
        if show_archived:
            queryset = (
                Resource.objects.all_including_archived()
                .select_related("category")
                .prefetch_related("service_types", "coverage_areas")
            )
        else:
            queryset = (
                Resource.objects.all()
                .select_related("category")
                .prefetch_related("service_types", "coverage_areas")
            )  # This uses the manager's default filter

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                # Apply archive filter to search results
                if show_archived:
                    queryset = (
                        search_results.filter(is_deleted=False)
                        .select_related("category")
                        .prefetch_related("service_types", "coverage_areas")
                    )
                else:
                    queryset = search_results.select_related(
                        "category"
                    ).prefetch_related("service_types", "coverage_areas")
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

        # Location-based filtering
        address_filter = self.request.GET.get("address", "").strip()
        lat_filter = self.request.GET.get("lat", "")
        lon_filter = self.request.GET.get("lon", "")
        radius_miles = self.request.GET.get("radius_miles", "10.0")

        if address_filter and lat_filter and lon_filter:
            # Use spatial filtering when coordinates are available
            try:
                # Use proximity-based filtering for better ranking
                spatial_queryset = Resource.objects.filter_by_location_with_proximity(
                    lat=float(lat_filter),
                    lon=float(lon_filter),
                    radius_miles=float(radius_miles) if radius_miles else None,
                    sort_by_proximity=True,
                )
                # Combine with existing filters
                spatial_ids = list(spatial_queryset.values_list("pk", flat=True))
                if spatial_ids:
                    queryset = queryset.filter(pk__in=spatial_ids)
                    # Preserve spatial ordering when proximity-based sorting is requested
                    if self.request.GET.get("sort") in ["distance", "proximity"]:
                        from django.db.models import Case, When

                        preserved = Case(
                            *[
                                When(pk=pk, then=pos)
                                for pos, pk in enumerate(spatial_ids)
                            ]
                        )
                        queryset = queryset.order_by(preserved)
                else:
                    # No spatial results, return empty queryset
                    queryset = Resource.objects.none()
            except (ValueError, TypeError) as e:
                # Fallback to text-based search if spatial filtering fails
                logger.warning(f"Spatial filtering failed for {address_filter}: {e}")
                queryset = queryset.filter(
                    Q(city__icontains=address_filter)
                    | Q(state__icontains=address_filter)
                    | Q(county__icontains=address_filter)
                )
        elif address_filter:
            # Text-based location search when no coordinates
            queryset = queryset.filter(
                Q(city__icontains=address_filter)
                | Q(state__icontains=address_filter)
                | Q(county__icontains=address_filter)
            )

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

        # Enhanced Location-Based Result Ranking
        sort_by = self.request.GET.get("sort", "-updated_at")

        # Handle location-based sorting when coordinates are available
        if (lat_filter and lon_filter) and sort_by in [
            "distance",
            "proximity",
            "coverage_specificity",
        ]:
            try:
                # Apply proximity ranking annotations
                queryset = Resource.objects.annotate_proximity_ranking(
                    queryset, float(lat_filter), float(lon_filter)
                )

                if sort_by == "proximity":
                    # Sort by proximity score (combines distance and coverage specificity)
                    queryset = queryset.order_by(
                        "-proximity_score",
                        "-specificity_score",
                        "distance_miles",
                        "name",
                    )
                elif sort_by == "distance":
                    # Sort by distance only
                    queryset = queryset.order_by(
                        "distance_miles", "-specificity_score", "name"
                    )
                elif sort_by == "coverage_specificity":
                    # Sort by coverage specificity first, then by proximity
                    queryset = queryset.order_by(
                        "-specificity_score",
                        "-proximity_score",
                        "distance_miles",
                        "name",
                    )

            except Exception as e:
                logger.warning(f"Proximity ranking failed: {e}")
                # Fallback to basic coverage specificity sorting
                queryset = queryset.annotate(
                    coverage_count=models.Count("coverage_areas")
                ).order_by("-coverage_count", "name")

        # Handle non-location-based sorting or when coordinates are not available
        elif sort_by:
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
            elif sort_by == "coverage_specificity":
                # Sort by coverage area count (more specific = higher priority)
                queryset = queryset.annotate(
                    coverage_count=models.Count("coverage_areas")
                ).order_by("-coverage_count", "name")
            elif sort_by in ["distance", "proximity"]:
                # Fallback to default sorting if location-based sorting requested but no coordinates
                logger.info(
                    "Location-based sorting requested but no coordinates available, using default sorting"
                )
                queryset = queryset.order_by("-updated_at")
            else:
                queryset = queryset.order_by(sort_by)
        else:
            # Default sorting - prioritize resources with coverage areas
            queryset = queryset.annotate(
                coverage_count=models.Count("coverage_areas")
            ).order_by("-coverage_count", "-updated_at")

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
            "address": self.request.GET.get("address", ""),
            "lat": self.request.GET.get("lat", ""),
            "lon": self.request.GET.get("lon", ""),
            "radius_miles": self.request.GET.get("radius_miles", "10.0"),
            "sort": self.request.GET.get("sort", "-updated_at"),
        }

        # Add permission context
        context["user_can_publish"] = user_can_publish(self.request.user)
        context["user_can_submit_review"] = user_can_submit_for_review(
            self.request.user
        )

        return context
