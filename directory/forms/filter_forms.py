"""
Filter Forms - Resource Filtering and Search Forms

This module contains form classes for filtering and searching resources
in the resource directory application. The forms provide comprehensive
filtering capabilities with multiple criteria and sorting options.

Form Classes:
    - ResourceFilterForm: Form for filtering and searching resources

Features:
    - Full-text search capability with placeholder text
    - Status filtering (draft, needs_review, published)
    - Category filtering with dropdown selection
    - Location-based filtering (city, state)
    - Multiple sorting options with user-friendly labels
    - Bootstrap-compatible form styling
    - All fields optional for flexible filtering

Filter Options:
    - q: Text search across resource fields
    - status: Filter by resource status
    - category: Filter by taxonomy category
    - city: Filter by city name
    - state: Filter by state code
    - sort: Sort order for results

Sort Options:
    - Recently Updated (default): -updated_at
    - Name A-Z: name
    - Name Z-A: -name
    - City A-Z: city
    - City Z-A: -city
    - Status: status
    - Status (Reverse): -status

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.forms.filter_forms import ResourceFilterForm
    
    # Create a filter form
    filter_form = ResourceFilterForm(request.GET)
    if filter_form.is_valid():
        queryset = filter_form.get_filtered_queryset()
"""

import logging
from typing import Any

from django import forms
from django.db import models
from django.db.models import Q

from ..models import Resource, TaxonomyCategory

logger = logging.getLogger(__name__)


class ResourceFilterForm(forms.Form):
    """Form for filtering and searching resources with comprehensive filter options.
    
    This form provides a complete interface for filtering and searching resources
    with multiple filter criteria including search terms, status, category,
    location, and sorting options. It supports both basic text search and
    structured filtering for efficient resource discovery.
    
    Features:
        - Full-text search capability with placeholder text
        - Status filtering (draft, needs_review, published)
        - Category filtering with dropdown selection
        - Location-based filtering (city, state)
        - Multiple sorting options with user-friendly labels
        - Bootstrap-compatible form styling
        - All fields optional for flexible filtering
        
    Filter Options:
        - q: Text search across resource fields
        - status: Filter by resource status
        - category: Filter by taxonomy category
        - city: Filter by city name
        - state: Filter by state code
        - sort: Sort order for results
        
    Sort Options:
        - Recently Updated (default): -updated_at
        - Name A-Z: name
        - Name Z-A: -name
        - City A-Z: city
        - City Z-A: -city
        - Status: status
        - Status (Reverse): -status
        
    Example:
        >>> filter_form = ResourceFilterForm(request.GET)
        >>> if filter_form.is_valid():
        ...     queryset = filter_form.get_filtered_queryset()
        ...     resources = queryset.filter(status='published')
    """

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search resources..."}
        ),
    )

    status = forms.ChoiceField(
        choices=[("", "All Statuses")] + Resource.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    category = forms.ModelChoiceField(
        queryset=TaxonomyCategory.objects.all().order_by("name"),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by city"}
        ),
    )

    state = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by state"}
        ),
    )

    # Location-based search fields
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter address or location"}
        ),
        help_text="Enter an address to find resources serving that location"
    )

    lat = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Latitude coordinate (auto-filled when address is geocoded)"
    )

    lon = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Longitude coordinate (auto-filled when address is geocoded)"
    )

    radius_miles = forms.FloatField(
        required=False,
        initial=10.0,
        min_value=0.5,
        max_value=100.0,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.5", "min": "0.5", "max": "100"}
        ),
        help_text="Search radius in miles (0.5-100 miles)"
    )

    sort = forms.ChoiceField(
        choices=[
            ("-updated_at", "Recently Updated"),
            ("name", "Name A-Z"),
            ("-name", "Name Z-A"),
            ("city", "City A-Z"),
            ("-city", "City Z-A"),
            ("status", "Status"),
            ("-status", "Status (Reverse)"),
            ("distance", "Distance (when location specified)"),
            ("coverage_specificity", "Coverage Specificity"),
            ("proximity", "Proximity (Distance + Coverage)"),
        ],
        required=False,
        initial="-updated_at",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def get_filtered_queryset(self) -> Any:
        """Get a filtered queryset based on form data.
        
        This method applies all the filter criteria from the form to create
        a filtered queryset of resources. It handles text search, status
        filtering, category filtering, location filtering, and sorting.
        
        The method uses the Resource model's custom manager methods for
        advanced search capabilities and combines multiple filter criteria
        to provide comprehensive filtering.
        
        Returns:
            QuerySet: Filtered and sorted resource queryset
            
        Note:
            This method assumes the form has been validated. If the form
            is not valid, it returns an empty queryset. The method uses
            the Resource.objects manager which automatically filters out
            archived and deleted resources.
        """
        if not self.is_valid():
            return Resource.objects.none()

        queryset = Resource.objects.all()

        # Text search
        search_query = self.cleaned_data.get("q")
        if search_query:
            queryset = queryset.search_combined(search_query)

        # Status filter
        status = self.cleaned_data.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Category filter
        category = self.cleaned_data.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # City filter
        city = self.cleaned_data.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)

        # State filter
        state = self.cleaned_data.get("state")
        if state:
            queryset = queryset.filter(state__icontains=state)

        # Location-based filtering
        address = self.cleaned_data.get("address")
        lat = self.cleaned_data.get("lat")
        lon = self.cleaned_data.get("lon")
        radius_miles = self.cleaned_data.get("radius_miles", 10.0)

        if address and lat and lon:
            # Use spatial filtering when coordinates are available
            try:
                # Use proximity-based filtering for better ranking
                spatial_queryset = Resource.objects.filter_by_location_with_proximity(
                    lat=float(lat),
                    lon=float(lon),
                    radius_miles=float(radius_miles) if radius_miles else None,
                    sort_by_proximity=True
                )
                # Combine with existing filters
                spatial_ids = list(spatial_queryset.values_list('pk', flat=True))
                if spatial_ids:
                    queryset = queryset.filter(pk__in=spatial_ids)
                    # Preserve spatial ordering when proximity-based sorting is requested
                    if self.cleaned_data.get("sort") in ["distance", "proximity"]:
                        from django.db.models import Case, When
                        preserved = Case(
                            *[When(pk=pk, then=pos) for pos, pk in enumerate(spatial_ids)]
                        )
                        queryset = queryset.order_by(preserved)
                else:
                    # No spatial results, return empty queryset
                    queryset = Resource.objects.none()
            except (ValueError, TypeError) as e:
                # Fallback to text-based search if spatial filtering fails
                logger.warning(f"Spatial filtering failed for {address}: {e}")
                queryset = queryset.filter(
                    Q(city__icontains=address) | 
                    Q(state__icontains=address) |
                    Q(county__icontains=address)
                )
        elif address:
            # Text-based location search when no coordinates
            queryset = queryset.filter(
                Q(city__icontains=address) | 
                Q(state__icontains=address) |
                Q(county__icontains=address)
            )

        # Enhanced Location-Based Result Ranking
        sort = self.cleaned_data.get("sort")
        
        # Handle location-based sorting when coordinates are available
        if (lat and lon) and sort in ["distance", "proximity", "coverage_specificity"]:
            try:
                # Apply proximity ranking annotations
                queryset = Resource.objects.annotate_proximity_ranking(
                    queryset, float(lat), float(lon)
                )
                
                if sort == "proximity":
                    # Sort by proximity score (combines distance and coverage specificity)
                    queryset = queryset.order_by('-proximity_score', '-specificity_score', 'distance_miles', 'name')
                elif sort == "distance":
                    # Sort by distance only
                    queryset = queryset.order_by('distance_miles', '-specificity_score', 'name')
                elif sort == "coverage_specificity":
                    # Sort by coverage specificity first, then by proximity
                    queryset = queryset.order_by('-specificity_score', '-proximity_score', 'distance_miles', 'name')
                
            except Exception as e:
                logger.warning(f"Proximity ranking failed: {e}")
                # Fallback to basic coverage specificity sorting
                queryset = queryset.annotate(
                    coverage_count=models.Count('coverage_areas')
                ).order_by('-coverage_count', 'name')
        
        # Handle non-location-based sorting or when coordinates are not available
        elif sort:
            if sort == "coverage_specificity":
                # Sort by coverage area count (more specific = higher priority)
                queryset = queryset.annotate(
                    coverage_count=models.Count('coverage_areas')
                ).order_by('-coverage_count', 'name')
            elif sort in ["distance", "proximity"]:
                # Fallback to default sorting if proximity requested but no coordinates
                logger.info("Location-based sorting requested but no coordinates available, using default sorting")
                queryset = queryset.order_by("-updated_at")
            else:
                queryset = queryset.order_by(sort)
        else:
            # Default sorting - prioritize resources with coverage areas
            queryset = queryset.annotate(
                coverage_count=models.Count('coverage_areas')
            ).order_by('-coverage_count', '-updated_at')

        return queryset

    def get_search_summary(self) -> str:
        """Get a human-readable summary of the current filters.
        
        This method creates a summary string describing the current
        filter criteria applied to the search. It's useful for
        displaying to users what filters are currently active.
        
        Returns:
            str: Human-readable summary of active filters
            
        Example:
            >>> form = ResourceFilterForm({'q': 'mental health', 'city': 'London'})
            >>> form.get_search_summary()
            "Search results for 'mental health' in London"
        """
        filters = []

        # Search query
        search_query = self.cleaned_data.get("q")
        if search_query:
            filters.append(f"'{search_query}'")

        # Status
        status = self.cleaned_data.get("status")
        if status:
            status_display = dict(Resource.STATUS_CHOICES).get(status, status)
            filters.append(f"status: {status_display}")

        # Category
        category = self.cleaned_data.get("category")
        if category:
            filters.append(f"category: {category.name}")

        # Location
        location_parts = []
        city = self.cleaned_data.get("city")
        state = self.cleaned_data.get("state")
        address = self.cleaned_data.get("address")
        radius_miles = self.cleaned_data.get("radius_miles")
        
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        if address:
            location_parts.append(f"near '{address}'")
            if radius_miles:
                location_parts.append(f"within {radius_miles} miles")
            
        if location_parts:
            filters.append(f"location: {', '.join(location_parts)}")

        if not filters:
            return "All resources"

        return " | ".join(filters)
