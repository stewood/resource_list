"""
URL configuration for directory app.
"""

from django.urls import path

from . import views

app_name = "directory"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    # Resource views
    path("resources/", views.ResourceListView.as_view(), name="resource_list"),
    path(
        "resources/create/", views.ResourceCreateView.as_view(), name="resource_create"
    ),
    path(
        "resources/<int:pk>/",
        views.ResourceDetailView.as_view(),
        name="resource_detail",
    ),
    path(
        "resources/<int:pk>/edit/",
        views.ResourceUpdateView.as_view(),
        name="resource_update",
    ),
    # Resource actions
    path(
        "resources/<int:pk>/submit-review/",
        views.submit_for_review,
        name="submit_for_review",
    ),
    path(
        "resources/<int:pk>/publish/", views.publish_resource, name="publish_resource"
    ),
    path(
        "resources/<int:pk>/unpublish/",
        views.unpublish_resource,
        name="unpublish_resource",
    ),
    # Version history and comparison
    path(
        "resources/<int:resource_pk>/versions/",
        views.version_history,
        name="version_history",
    ),
    path(
        "resources/<int:resource_pk>/versions/<int:version1_pk>/compare/",
        views.version_comparison,
        name="version_comparison",
    ),
    path(
        "resources/<int:resource_pk>/versions/<int:version1_pk>/compare/<int:version2_pk>/",
        views.version_comparison,
        name="version_comparison_two",
    ),
]
