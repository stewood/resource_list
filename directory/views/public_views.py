"""
Public Views - Non-Authenticated Access to Published Resources

This module contains Django views for public access to published resources without
authentication requirements. These views provide the public-facing interface for
discovering and browsing available services, organized by category and service type.

Key Views:
    - public_home: Public home page with resource statistics and organization
    - public_resource_list: Public resource listing with search and filters
    - public_resource_detail: Individual published resource display with related suggestions
    - custom_logout: Custom logout handling with redirect to public home

Features:
    - Public access without authentication requirements
    - Full-text search using SQLite FTS5 with fallback
    - Advanced filtering by category, service type, location, and operational characteristics
    - Resource organization and statistics
    - Related resource suggestions
    - Optimized database queries for performance

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.core.paginator for pagination
    - directory.models for data access

Usage:
    from directory.views.public_views import public_home, public_resource_list
    
    # URL patterns typically map to these views
    # / -> public_home
    # /resources/ -> public_resource_list
    # /resources/<pk>/ -> public_resource_detail
    # /logout/ -> custom_logout
"""

from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Resource, ServiceType, TaxonomyCategory


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
    ).select_related('category').prefetch_related('service_types', 'coverage_areas')
    
    # Search functionality
    search_query = request.GET.get("q", "").strip()
    if search_query:
        search_results = Resource.objects.search_combined(search_query)
        if search_results.exists():
            queryset = search_results.filter(
                status="published", 
                is_deleted=False, 
                is_archived=False
            ).select_related('category').prefetch_related('service_types', 'coverage_areas')
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
    logout(request)
    return redirect('directory:public_home')
