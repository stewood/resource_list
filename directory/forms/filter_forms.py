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

from typing import Any

from django import forms
from django.db.models import Q

from ..models import Resource, TaxonomyCategory


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

    sort = forms.ChoiceField(
        choices=[
            ("-updated_at", "Recently Updated"),
            ("name", "Name A-Z"),
            ("-name", "Name Z-A"),
            ("city", "City A-Z"),
            ("-city", "City Z-A"),
            ("status", "Status"),
            ("-status", "Status (Reverse)"),
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

        # Sorting
        sort = self.cleaned_data.get("sort")
        if sort:
            queryset = queryset.order_by(sort)
        else:
            # Default sorting
            queryset = queryset.order_by("-updated_at")

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
        
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
            
        if location_parts:
            filters.append(f"location: {', '.join(location_parts)}")

        if not filters:
            return "All resources"

        return " | ".join(filters)
