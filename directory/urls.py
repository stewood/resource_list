"""
URL configuration for directory app.
"""

from django.urls import path

from .views import (
    # Resource views
    ResourceListView,
    ResourceDetailView,
    ResourceCreateView,
    ResourceUpdateView,
    # Workflow views
    submit_for_review,
    publish_resource,
    unpublish_resource,
    archive_resource,
    unarchive_resource,
    # Archive views
    ArchiveListView,
    ArchiveDetailView,
    # Dashboard views
    dashboard,
    version_comparison,
    version_history,
    # Public views
    public_home,
    public_resource_list,
    public_resource_detail,
    custom_logout,
    # API views
    AreaSearchView,
    LocationSearchView,
)

app_name = "directory"

urlpatterns = [
    # Public views (no authentication required)
    path("", public_home, name="public_home"),
    path("resources/", public_resource_list, name="public_resource_list"),
    path("resources/<int:pk>/", public_resource_detail, name="public_resource_detail"),
    
    # Admin views (authentication required)
    path("manage/dashboard/", dashboard, name="dashboard"),
    path("manage/resources/", ResourceListView.as_view(), name="resource_list"),
    path(
        "manage/resources/create/", ResourceCreateView.as_view(), name="resource_create"
    ),
    path(
        "manage/resources/<int:pk>/",
        ResourceDetailView.as_view(),
        name="resource_detail",
    ),
    path(
        "manage/resources/<int:pk>/edit/",
        ResourceUpdateView.as_view(),
        name="resource_update",
    ),
    # Resource actions
    path(
        "manage/resources/<int:pk>/submit-review/",
        submit_for_review,
        name="submit_for_review",
    ),
    path(
        "manage/resources/<int:pk>/publish/", publish_resource, name="publish_resource"
    ),
    path(
        "manage/resources/<int:pk>/unpublish/",
        unpublish_resource,
        name="unpublish_resource",
    ),
    # Version history and comparison
    path(
        "manage/resources/<int:resource_pk>/versions/",
        version_history,
        name="version_history",
    ),
    path(
        "manage/resources/<int:resource_pk>/versions/<int:version1_pk>/compare/",
        version_comparison,
        name="version_comparison",
    ),
    path(
        "manage/resources/<int:resource_pk>/versions/<int:version1_pk>/compare/<int:version2_pk>/",
        version_comparison,
        name="version_comparison_two",
    ),
    # Archive views
    path("manage/archives/", ArchiveListView.as_view(), name="archive_list"),
    path(
        "manage/archives/<int:pk>/",
        ArchiveDetailView.as_view(),
        name="archive_detail",
    ),
    # Archive actions
    path(
        "manage/resources/<int:pk>/archive/",
        archive_resource,
        name="archive_resource",
    ),
    path(
        "manage/resources/<int:pk>/unarchive/",
        unarchive_resource,
        name="unarchive_resource",
    ),
    
    # Authentication
    path("logout/", custom_logout, name="logout"),
    
    # API endpoints
    path("api/areas/search/", AreaSearchView.as_view(), name="api_area_search"),
    path("api/search/by-location/", LocationSearchView.as_view(), name="api_location_search"),
]
