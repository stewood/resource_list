"""
Dashboard Views - Analytics, Metrics, and Version Management

This module contains Django views for the administrative dashboard and version
management functionality. These views provide system analytics, metrics, and
tools for comparing and viewing resource version history.

Key Views:
    - dashboard: Main administrative dashboard with system metrics
    - version_comparison: Side-by-side comparison of resource versions
    - version_history: Complete version history for a resource

Features:
    - Comprehensive system analytics and metrics
    - Resource counts by status and verification status
    - Recent activity monitoring
    - Version comparison with detailed difference analysis
    - Complete audit trail access
    - System health indicators

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Dependencies:
    - Django 5.0.2+
    - django.contrib.auth for authentication
    - directory.models for data access
    - directory.utils for version comparison utilities

Usage:
    from directory.views.dashboard_views import dashboard, version_comparison

    # URL patterns typically map to these views
    # /dashboard/ -> dashboard
    # /resources/<pk>/versions/ -> version_history
    # /resources/<pk>/versions/<v1>/compare/ -> version_comparison
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

logger = logging.getLogger(__name__)

from ..models import Resource, ResourceVersion
from ..utils import compare_versions, generate_diff_html
from ..permissions import user_can_publish, user_can_hard_delete


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view with comprehensive resource analytics and metrics.

    This view provides an overview of the resource directory system with
    key metrics, counts by status, verification tracking, and recent activity.
    It serves as the main administrative dashboard for monitoring system health
    and resource management status.

    Features:
        - Resource counts by status (draft, needs_review, published, archived)
        - Verification tracking for published resources
        - Recent activity monitoring
        - System health indicators
        - Administrative overview

    Template Context:
        - draft_count: Number of resources in draft status
        - review_count: Number of resources awaiting review
        - published_count: Number of published resources
        - archived_count: Number of archived resources
        - needs_verification: Number of published resources needing verification
        - recent_resources: List of recently updated resources (last 10)

    Returns:
        HttpResponse: Rendered dashboard template with analytics data

    Example:
        GET /dashboard/ -> Display system dashboard with metrics
    """
    # Get resource counts by status
    draft_count = Resource.objects.filter(status="draft", is_deleted=False).count()
    review_count = Resource.objects.filter(
        status="needs_review", is_deleted=False
    ).count()
    published_count = Resource.objects.filter(
        status="published", is_deleted=False
    ).count()

    # Get archived count
    archived_count = Resource.objects.archived().count()

    # Get resources needing verification
    verification_threshold = timezone.now() - timedelta(
        days=settings.VERIFICATION_EXPIRY_DAYS
    )
    needs_verification = Resource.objects.filter(
        status="published",
        is_deleted=False,
        last_verified_at__lt=verification_threshold,
    ).count()

    # Get recent activity
    recent_resources = Resource.objects.filter(is_deleted=False).order_by(
        "-updated_at"
    )[:10]

    context = {
        "draft_count": draft_count,
        "review_count": review_count,
        "published_count": published_count,
        "archived_count": archived_count,
        "needs_verification": needs_verification,
        "recent_resources": recent_resources,
    }

    return render(request, "directory/dashboard.html", context)


@login_required
def version_comparison(
    request: HttpRequest, resource_pk: int, version1_pk: int, version2_pk: int = None
) -> HttpResponse:
    """Compare two versions of a resource with detailed difference analysis.

    This view provides a side-by-side comparison of two versions of a resource,
    highlighting the differences between them. It can compare any two historical
    versions or compare a historical version with the current state of the resource.

    Features:
        - Side-by-side version comparison
        - Detailed difference highlighting
        - Support for comparing historical versions or current state
        - Comprehensive field comparison
        - User-friendly difference presentation

    Args:
        request: The HTTP request object
        resource_pk: Primary key of the resource to compare versions for
        version1_pk: Primary key of the first version to compare
        version2_pk: Primary key of the second version to compare (optional, defaults to current)

    Returns:
        HttpResponse: Rendered version comparison template with difference data

    Raises:
        404: If the resource or version is not found

    Template Context:
        - resource: The resource object being compared
        - version1: The first version object
        - version2_label: Label for the second version ("Current" or "vX")
        - differences: Dictionary of field differences between versions
        - version1_snapshot: Complete snapshot data for version 1
        - version2_snapshot: Complete snapshot data for version 2

    Example:
        GET /resources/123/versions/1/compare/ -> Compare version 1 with current
        GET /resources/123/versions/1/compare/2/ -> Compare version 1 with version 2
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)
    version1 = get_object_or_404(ResourceVersion, pk=version1_pk, resource=resource)

    # If no second version specified, compare with current resource state
    if version2_pk:
        version2 = get_object_or_404(ResourceVersion, pk=version2_pk, resource=resource)
        current_snapshot = version2.snapshot
        version2_label = f"v{version2.version_number}"
    else:
        # Create current snapshot for comparison
        current_snapshot = {
            "name": resource.name,
            "category": resource.category.name if resource.category else "",
            "description": resource.description,
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            "status": resource.status,
            "source": resource.source,
            "hours_of_operation": resource.hours_of_operation,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            "is_emergency_service": resource.is_emergency_service,
            "is_24_hour_service": resource.is_24_hour_service,
            "insurance_accepted": resource.insurance_accepted,
            "capacity": resource.capacity,
            "service_types": ", ".join([st.name for st in resource.service_types.all()]) if resource.service_types.exists() else "",
            "coverage_areas": ", ".join([ca.name for ca in resource.coverage_areas.all()]) if resource.coverage_areas.exists() else "",
            "last_verified_at": (
                resource.last_verified_at.isoformat()
                if resource.last_verified_at
                else ""
            ),
            "last_verified_by": (
                resource.last_verified_by.get_full_name()
                if resource.last_verified_by
                else ""
            ),
        }
        version2_label = "Current"

    # Compare the versions
    differences = compare_versions(version1.snapshot, current_snapshot)

    context = {
        "resource": resource,
        "version1": version1,
        "version2_label": version2_label,
        "differences": differences,
        "version1_snapshot": version1.snapshot,
        "version2_snapshot": current_snapshot,
    }

    return render(request, "directory/version_comparison.html", context)


@login_required
def version_history(request: HttpRequest, resource_pk: int) -> HttpResponse:
    """Show complete version history for a resource with chronological ordering.

    This view displays the complete version history of a resource, showing all
    changes made over time in chronological order. It provides access to the
    full audit trail for transparency and historical tracking.

    Features:
        - Complete version history display
        - Chronological ordering (newest first)
        - Access to all historical snapshots
        - Audit trail transparency
        - Historical change tracking

    Args:
        request: The HTTP request object
        resource_pk: Primary key of the resource to show version history for

    Returns:
        HttpResponse: Rendered version history template with complete version list

    Raises:
        404: If the resource is not found

    Template Context:
        - resource: The resource object
        - versions: Complete list of all versions ordered by version number (descending)

    Example:
        GET /resources/123/versions/ -> Display complete version history for resource 123
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)
    versions = resource.versions.all().order_by("-version_number")

    context = {
        "resource": resource,
        "versions": versions,
        # Add permission context for buttons
        "user_can_publish": user_can_publish(request.user),
        "user_can_archive": user_can_hard_delete(request.user),
    }

    return render(request, "directory/version_history.html", context)


@login_required
def published_comparison(request: HttpRequest, resource_pk: int) -> HttpResponse:
    """Compare current resource state with the last published version.

    This view provides a focused comparison between the current state of a resource
    and the last version that was published. This is particularly useful for
    reviewing changes before publishing updates.

    Features:
        - Comparison with last published version
        - Focused on changes since last publication
        - User-friendly difference presentation
        - Handles cases where resource was never published

    Args:
        request: The HTTP request object
        resource_pk: Primary key of the resource to compare

    Returns:
        HttpResponse: Rendered comparison template with difference data

    Raises:
        404: If the resource is not found

    Template Context:
        - resource: The resource object being compared
        - last_published_version: The last published version (or None)
        - differences: Dictionary of field differences
        - current_snapshot: Current resource state
        - published_snapshot: Last published version state (or None)
        - was_never_published: Boolean indicating if resource was never published

    Example:
        GET /resources/123/published-comparison/ -> Compare current with last published
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)

    # Find the last published version
    # Look for the last version where the resource status was "published"
    last_published_version = None
    for version in ResourceVersion.objects.filter(resource=resource).order_by('-version_number'):
        try:
            snapshot_data = version.snapshot
            if snapshot_data.get('status') == 'published':
                last_published_version = version
                break
        except (KeyError, TypeError):
            # Skip versions with invalid snapshot data
            continue

    # Create current snapshot for comparison (focusing on meaningful data, excluding system metadata)
    current_snapshot = {
        # Basic information
        "name": resource.name,
        "category": resource.category.name if resource.category else "",
        "description": resource.description,

        # Contact information
        "phone": resource.phone,
        "email": resource.email,
        "website": resource.website,

        # Location information
        "address1": resource.address1,
        "address2": resource.address2,
        "city": resource.city,
        "state": resource.state,
        "postal_code": resource.postal_code,
        "county": resource.county,

        # Service information
        "hours_of_operation": resource.hours_of_operation,
        "eligibility_requirements": resource.eligibility_requirements,
        "populations_served": resource.populations_served,
        "cost_information": resource.cost_information,
        "languages_available": resource.languages_available,
        "is_emergency_service": resource.is_emergency_service,
        "is_24_hour_service": resource.is_24_hour_service,
        "insurance_accepted": resource.insurance_accepted,
        "capacity": resource.capacity,

        # Service types (ManyToManyField - convert to readable string)
        "service_types": ", ".join([st.name for st in resource.service_types.all()]) if resource.service_types.exists() else "",

        # Coverage areas (ManyToManyField - convert to readable string)
        "coverage_areas": ", ".join([ca.name for ca in resource.coverage_areas.all()]) if resource.coverage_areas.exists() else "",

        # Source (keep this as it represents verification data)
        "source": resource.source,
    }

    was_never_published = False
    published_snapshot = None
    differences = {}

    if last_published_version:
        published_snapshot = last_published_version.snapshot

        # Filter out system/metadata fields to focus on meaningful data
        # These fields change every time and don't represent actual content changes
        system_fields_to_exclude = {
            'id', 'created_by_id', 'updated_by_id', 'last_verified_by_id',
            'created_at', 'updated_at', 'is_deleted', 'last_verified_at',
            'last_verified_by', 'status', 'notes'  # Exclude workflow fields and notes (shown separately)
        }

        # Create filtered published snapshot with only meaningful fields
        filtered_published_snapshot = {}
        for key, value in published_snapshot.items():
            if key not in system_fields_to_exclude:
                if key == 'category_id' and value:
                    # Convert category_id to category name for comparison
                    try:
                        from directory.models import TaxonomyCategory
                        category = TaxonomyCategory.objects.get(id=value)
                        filtered_published_snapshot['category'] = category.name
                    except TaxonomyCategory.DoesNotExist:
                        filtered_published_snapshot['category'] = ""
                else:
                    filtered_published_snapshot[key] = value

        # Get all differences
        all_differences = compare_versions(filtered_published_snapshot, current_snapshot)

        # Filter to only show meaningful content changes
        differences = {}
        for field, diff in all_differences.items():
            # Skip system fields that were excluded from comparison
            if field in system_fields_to_exclude:
                continue

            # Only include if there's a meaningful change
            if diff['diff_type'] == 'added' and diff['new_value']:
                # Include added fields that have actual content
                differences[field] = diff
            elif diff['diff_type'] == 'changed':  # Fixed: was 'modified', should be 'changed'
                # Include modified fields (actual content changes)
                differences[field] = diff
            elif diff['diff_type'] == 'removed' and diff['old_value']:
                # Include removed fields that had content
                differences[field] = diff

        # Calculate change counts for the template
        change_counts = {
            'added': sum(1 for diff in differences.values() if diff['diff_type'] == 'added'),
            'changed': sum(1 for diff in differences.values() if diff['diff_type'] == 'changed'),
            'removed': sum(1 for diff in differences.values() if diff['diff_type'] == 'removed'),
        }
    else:
        was_never_published = True
        # For new resources, show current state as "added" fields
        differences = {
            field: {
                "old_value": None,
                "new_value": value,
                "diff_type": "added",
                "diff_html": generate_diff_html("", str(value) if value else "")
            }
            for field, value in current_snapshot.items()
            if value  # Only show non-empty fields
        }

    context = {
        "resource": resource,
        "last_published_version": last_published_version,
        "differences": differences,
        "current_snapshot": current_snapshot,
        "published_snapshot": published_snapshot,
        "was_never_published": was_never_published,
        "change_counts": change_counts if 'change_counts' in locals() else {'added': 0, 'changed': 0, 'removed': 0},
        # Add permission context for buttons
        "user_can_publish": user_can_publish(request.user),
        "user_can_archive": user_can_hard_delete(request.user),
    }

    return render(request, "directory/published_comparison.html", context)
