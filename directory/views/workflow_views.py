"""
Workflow Views - Resource Status Transitions and Workflow Management

This module contains Django views for managing resource workflow transitions
and status changes. These views handle the progression of resources through
the workflow stages (draft → needs_review → published) and archive management.

Key Views:
    - submit_for_review: Transition from draft to needs_review status
    - publish_resource: Transition from needs_review to published status
    - unpublish_resource: Revert from published to needs_review status
    - archive_resource: Archive active resources with reason tracking
    - unarchive_resource: Restore archived resources to active status

Features:
    - Permission-based access control for each workflow stage
    - Comprehensive validation of resource requirements
    - Automatic user tracking and metadata updates
    - Error handling with descriptive messages
    - Archive reason tracking and validation

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - django.views.decorators for HTTP method restrictions
    - directory.models for data access
    - directory.permissions for access control

Usage:
    from directory.views.workflow_views import publish_resource, archive_resource

    # URL patterns typically map to these views
    # POST /resources/<pk>/submit-review/ -> submit_for_review
    # POST /resources/<pk>/publish/ -> publish_resource
    # POST /resources/<pk>/unpublish/ -> unpublish_resource
    # POST /resources/<pk>/archive/ -> archive_resource
    # POST /resources/<pk>/unarchive/ -> unarchive_resource
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from ..models import Resource
from ..permissions import (
    user_can_hard_delete,
    user_can_publish,
    user_can_submit_for_review,
)


@require_http_methods(["POST"])
def submit_for_review(request: HttpRequest, pk: int) -> HttpResponse:
    """Submit a resource for review with validation and permission checks.

    This view handles the workflow transition from draft to needs_review status.
    It validates that the user has permission to submit resources for review and
    ensures the resource meets all requirements for the needs_review status.

    Features:
        - Permission validation (Editor, Reviewer, or Admin required)
        - Resource validation for needs_review status requirements
        - Error handling with descriptive error messages
        - Status transition with automatic validation

    Args:
        request: The HTTP request object
        pk: Primary key of the resource to submit for review

    Returns:
        HttpResponse: Success message or error response with appropriate status code

    Raises:
        404: If the resource is not found or is deleted
        403: If the user lacks permission to submit for review
        400: If the resource fails validation for needs_review status

    Example:
        POST /resources/123/submit-for-review/ -> Submit resource 123 for review
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_submit_for_review(request.user):
        return HttpResponse("Permission denied", status=403)

    # Validate that the resource meets review requirements
    try:
        resource.status = "needs_review"
        resource.full_clean()
        resource.save()
        return HttpResponse("Resource submitted for review successfully")
    except Exception as e:
        return HttpResponse(f"Validation error: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def publish_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish a resource with verification and permission checks.

    This view handles the workflow transition from needs_review to published status.
    It validates that the user has permission to publish resources and ensures
    the resource meets all requirements for the published status. It also sets
    verification metadata including timestamp and verifier.

    Features:
        - Permission validation (Reviewer or Admin required)
        - Resource validation for published status requirements
        - Automatic verification metadata setting
        - Error handling with descriptive error messages
        - Status transition with automatic validation

    Args:
        request: The HTTP request object
        pk: Primary key of the resource to publish

    Returns:
        HttpResponse: Success message or error response with appropriate status code

    Raises:
        404: If the resource is not found or is deleted
        403: If the user lacks permission to publish resources
        400: If the resource fails validation for published status

    Example:
        POST /resources/123/publish/ -> Publish resource 123
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_publish(request.user):
        return HttpResponse("Permission denied", status=403)

    # Validate that the resource meets publish requirements
    try:
        resource.status = "published"
        resource.last_verified_at = timezone.now()
        resource.last_verified_by = request.user
        resource.full_clean()
        resource.save()
        return HttpResponse("Resource published successfully")
    except Exception as e:
        return HttpResponse(f"Validation error: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def unpublish_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Unpublish a resource with permission checks and status reversion.

    This view handles the workflow transition from published back to needs_review status.
    It validates that the user has permission to unpublish resources and reverts
    the resource status while updating the user tracking information.

    Features:
        - Permission validation (Reviewer or Admin required)
        - Status reversion from published to needs_review
        - User tracking update
        - Error handling with descriptive error messages

    Args:
        request: The HTTP request object
        pk: Primary key of the resource to unpublish

    Returns:
        HttpResponse: Success message or error response with appropriate status code

    Raises:
        404: If the resource is not found or is deleted
        PermissionDenied: If the user lacks permission to unpublish resources

    Example:
        POST /resources/123/unpublish/ -> Unpublish resource 123
    """
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_publish(request.user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Access denied. Requires Reviewer or Admin role.")

    resource.status = "needs_review"
    resource.updated_by = request.user
    resource.save()

    return HttpResponse("Resource unpublished successfully")


@login_required
@require_http_methods(["POST"])
def archive_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Archive a resource with reason tracking and permission validation.

    This view handles the archival of resources, moving them from active status
    to archived status while preserving all data for historical purposes. It
    requires a reason for archiving and validates user permissions.

    Features:
        - Permission validation (Admin role required)
        - Archive reason requirement and tracking
        - Automatic timestamp and user assignment
        - User tracking update
        - Error handling with descriptive error messages
        - Redirect to detail page for better UX

    Args:
        request: The HTTP request object containing POST data
        pk: Primary key of the resource to archive

    Returns:
        HttpResponse: Redirect response to resource detail page or error response

    Raises:
        404: If the resource is not found or is already archived
        PermissionDenied: If the user lacks permission to archive resources
        400: If archive reason is missing or archiving fails

    POST Data:
        - archive_reason: Required string explaining why the resource is being archived

    Example:
        POST /resources/123/archive/ with archive_reason="Organization closed"
    """
    # Use the manager's all_including_archived method to get the resource
    resource = get_object_or_404(
        Resource.objects.all_including_archived(), pk=pk, is_archived=False
    )

    if not user_can_hard_delete(request.user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Access denied. Requires Admin role.")

    # Get archive reason from POST data
    archive_reason = request.POST.get("archive_reason", "").strip()

    if not archive_reason:
        return HttpResponse("Archive reason is required", status=400)

    try:
        resource.is_archived = True
        resource.archived_at = timezone.now()
        resource.archived_by = request.user
        resource.archive_reason = archive_reason
        resource.updated_by = request.user
        resource.save()
        # Redirect back to detail page for UX
        return redirect("directory:resource_detail", pk=resource.pk)
    except Exception as e:
        return HttpResponse(f"Error archiving resource: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def unarchive_resource(request: HttpRequest, pk: int) -> HttpResponse:
    """Unarchive a resource with permission validation and metadata cleanup.

    This view handles the restoration of archived resources, moving them back
    to active status. It validates user permissions and cleans up archive-related
    metadata while preserving the resource data.

    Features:
        - Permission validation (Admin role required)
        - Archive metadata cleanup (timestamp, user, reason)
        - User tracking update
        - Redirect to detail page for better UX

    Args:
        request: The HTTP request object
        pk: Primary key of the archived resource to unarchive

    Returns:
        HttpResponse: Redirect response to resource detail page

    Raises:
        404: If the resource is not found or is not archived
        PermissionDenied: If the user lacks permission to unarchive resources

    Example:
        POST /resources/123/unarchive/ -> Restore archived resource 123
    """
    # Use the manager's archived method to get the resource
    resource = get_object_or_404(Resource.objects.archived(), pk=pk)

    if not user_can_hard_delete(request.user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Access denied. Requires Admin role.")

    resource.is_archived = False
    resource.archived_at = None
    resource.archived_by = None
    resource.archive_reason = ""
    resource.updated_by = request.user
    resource.save()

    return redirect("directory:resource_detail", pk=resource.pk)
