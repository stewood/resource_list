"""
URL configuration for directory app.
"""

from django.urls import path

from . import views

app_name = "directory"

urlpatterns = [
    # Public views (no authentication required)
    path("", views.public_home, name="public_home"),
    path("resources/", views.public_resource_list, name="public_resource_list"),
    path("resources/<int:pk>/", views.public_resource_detail, name="public_resource_detail"),
    
    # Admin views (authentication required)
    path("manage/dashboard/", views.dashboard, name="dashboard"),
    path("manage/resources/", views.ResourceListView.as_view(), name="resource_list"),
    path(
        "manage/resources/create/", views.ResourceCreateView.as_view(), name="resource_create"
    ),
    path(
        "manage/resources/<int:pk>/",
        views.ResourceDetailView.as_view(),
        name="resource_detail",
    ),
    path(
        "manage/resources/<int:pk>/edit/",
        views.ResourceUpdateView.as_view(),
        name="resource_update",
    ),
    # Resource actions
    path(
        "manage/resources/<int:pk>/submit-review/",
        views.submit_for_review,
        name="submit_for_review",
    ),
    path(
        "manage/resources/<int:pk>/publish/", views.publish_resource, name="publish_resource"
    ),
    path(
        "manage/resources/<int:pk>/unpublish/",
        views.unpublish_resource,
        name="unpublish_resource",
    ),
    # Version history and comparison
    path(
        "manage/resources/<int:resource_pk>/versions/",
        views.version_history,
        name="version_history",
    ),
    path(
        "manage/resources/<int:resource_pk>/versions/<int:version1_pk>/compare/",
        views.version_comparison,
        name="version_comparison",
    ),
    path(
        "manage/resources/<int:resource_pk>/versions/<int:version1_pk>/compare/<int:version2_pk>/",
        views.version_comparison,
        name="version_comparison_two",
    ),
    # Archive views
    path("manage/archives/", views.ArchiveListView.as_view(), name="archive_list"),
    path(
        "manage/archives/<int:pk>/",
        views.ArchiveDetailView.as_view(),
        name="archive_detail",
    ),
    # Archive actions
    path(
        "manage/resources/<int:pk>/archive/",
        views.archive_resource,
        name="archive_resource",
    ),
    path(
        "manage/resources/<int:pk>/unarchive/",
        views.unarchive_resource,
        name="unarchive_resource",
    ),
    
    # Authentication
    path("logout/", views.custom_logout, name="logout"),
]
