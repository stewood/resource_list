"""
Resource Directory Views Package

This package contains all Django views for the resource directory application,
organized into logical modules for better maintainability and code organization.

View Modules:
    - resource_views: Core resource CRUD operations (list, detail, create, update)
    - search_views: Search and filtering functionality
    - workflow_views: Workflow transitions and status changes
    - archive_views: Archive management and archive-specific views
    - public_views: Non-authenticated public access views
    - dashboard_views: Dashboard and analytics views

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.views import ResourceListView, ResourceDetailView
    
    # All views are available through the package namespace
    # URL patterns can import directly from this package
"""

# Import all view classes and functions for backward compatibility
from .resource_views import (
    ResourceListView,
    ResourceDetailView,
    ResourceCreateView,
    ResourceUpdateView,
)
from .workflow_views import (
    submit_for_review,
    publish_resource,
    unpublish_resource,
    archive_resource,
    unarchive_resource,
)
from .archive_views import (
    ArchiveListView,
    ArchiveDetailView,
)
from .dashboard_views import (
    dashboard,
    version_comparison,
    version_history,
)
from .public_views import (
    public_home,
    public_resource_list,
    public_resource_detail,
    custom_logout,
)
from .api_views import (
    AreaSearchView,
    LocationSearchView,
    ResourceAreaManagementView,
    ResourceEligibilityView,
)

# Export all views for easy importing
__all__ = [
    # Resource views
    "ResourceListView",
    "ResourceDetailView", 
    "ResourceCreateView",
    "ResourceUpdateView",
    
    # Workflow views
    "submit_for_review",
    "publish_resource",
    "unpublish_resource",
    "archive_resource",
    "unarchive_resource",
    
    # Archive views
    "ArchiveListView",
    "ArchiveDetailView",
    
    # Dashboard views
    "dashboard",
    "version_comparison",
    "version_history",
    
    # Public views
    "public_home",
    "public_resource_list",
    "public_resource_detail",
    "custom_logout",
    
    # API views
    "AreaSearchView",
    "LocationSearchView",
    "ResourceAreaManagementView",
    "ResourceEligibilityView",
]
