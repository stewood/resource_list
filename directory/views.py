"""
Views for the resource directory application.
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView

from .forms import ResourceForm
from .models import Resource, ResourceVersion, ServiceType, TaxonomyCategory
from .permissions import (
    require_admin,
    require_editor,
    require_reviewer,
    user_can_publish,
    user_can_submit_for_review,
    user_can_hard_delete,
)
from .utils import compare_versions


class ResourceListView(LoginRequiredMixin, ListView):
    """List view for resources with filtering and search."""

    model = Resource
    template_name = "directory/resource_list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self):
        """Filter queryset based on search and filter parameters."""
        # Start with non-archived resources by default
        queryset = Resource.objects.all()

        # Check if user wants to see archived resources
        show_archived = self.request.GET.get("show_archived", "").lower() == "true"
        if show_archived:
            queryset = Resource.objects.all_including_archived()
        else:
            queryset = Resource.objects.all()  # This uses the manager's default filter

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                # Apply archive filter to search results
                if show_archived:
                    queryset = search_results.filter(is_deleted=False)
                else:
                    queryset = search_results
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

        # Sorting
        sort_by = self.request.GET.get("sort", "-updated_at")
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

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
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
            "sort": self.request.GET.get("sort", "-updated_at"),
        }

        # Add permission context
        context["user_can_publish"] = user_can_publish(self.request.user)
        context["user_can_submit_review"] = user_can_submit_for_review(
            self.request.user
        )

        return context


class ResourceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single resource."""

    model = Resource
    template_name = "directory/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self):
        """Filter out deleted resources but include archived ones."""
        return Resource.objects.all_including_archived()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Add permission context
        context["user_can_publish"] = user_can_publish(self.request.user)
        context["user_can_submit_review"] = user_can_submit_for_review(
            self.request.user
        )

        # Add version history
        context["versions"] = self.object.versions.all()[:10]  # Last 10 versions

        return context


class ResourceCreateView(LoginRequiredMixin, CreateView):
    """Create view for new resources."""

    model = Resource
    form_class = ResourceForm
    template_name = "directory/resource_form.html"
    success_url = reverse_lazy("directory:resource_list")

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        if not user_can_submit_for_review(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Access denied. Requires Editor, Reviewer, or Admin role.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass user to form for validation."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Set the user who created the resource."""
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        return context


class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for resources."""

    model = Resource
    form_class = ResourceForm
    template_name = "directory/resource_form.html"
    context_object_name = "resource"

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        if not user_can_submit_for_review(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Access denied. Requires Editor, Reviewer, or Admin role.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filter out deleted resources."""
        return Resource.objects.all_including_archived()

    def get_form_kwargs(self):
        """Pass user to form for validation."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        """Handle form validation."""
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the resource detail page."""
        return reverse("directory:resource_detail", kwargs={"pk": self.object.pk})


class ArchiveListView(LoginRequiredMixin, ListView):
    """List view for archived resources."""

    model = Resource
    template_name = "directory/archive_list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self):
        """Get only archived resources."""
        queryset = Resource.objects.archived()

        # Search using FTS5
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            # Use combined search (FTS5 + exact matches)
            search_results = Resource.objects.search_combined(search_query)
            if search_results.exists():
                queryset = search_results.filter(is_archived=True, is_deleted=False)
            else:
                # Fallback to basic search if FTS5 fails
                queryset = queryset.filter(
                    Q(name__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(city__icontains=search_query)
                    | Q(state__icontains=search_query)
                )

        # Filters
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

        # Sorting
        sort_by = self.request.GET.get("sort", "-archived_at")
        if sort_by in [
            "name",
            "-name",
            "city",
            "-city",
            "archived_at",
            "-archived_at",
            "archived_by",
            "-archived_by",
        ]:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        
        # Get filter options
        context["categories"] = TaxonomyCategory.objects.all().order_by("name")
        context["service_types"] = ServiceType.objects.all().order_by("name")
        
        # Get archive statistics
        context["total_archived"] = Resource.objects.archived().count()
        context["archived_by_category"] = {}
        for category in TaxonomyCategory.objects.all():
            count = Resource.objects.archived().filter(category=category).count()
            if count > 0:
                context["archived_by_category"][category.name] = count

        return context


class ArchiveDetailView(LoginRequiredMixin, DetailView):
    """Detail view for archived resources."""

    model = Resource
    template_name = "directory/archive_detail.html"
    context_object_name = "resource"

    def get_queryset(self):
        """Get only archived resources."""
        return Resource.objects.archived()

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        
        # Get version history
        context["versions"] = self.object.versions.all()[:10]
        
        return context


@login_required
@require_http_methods(["POST"])
def submit_for_review(request: HttpRequest, pk: int) -> HttpResponse:
    """Submit a resource for review."""
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
    """Publish a resource."""
    resource = get_object_or_404(Resource, pk=pk, is_deleted=False)

    if not user_can_publish(request.user):
        return HttpResponse("Permission denied", status=403)

    # Validate that the resource meets publish requirements
    try:
        from django.utils import timezone

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
    """Unpublish a resource."""
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
    """Archive a resource."""
    from django.utils import timezone
    
    # Use the manager's all_including_archived method to get the resource
    resource = get_object_or_404(Resource.objects.all_including_archived(), pk=pk, is_archived=False)
    
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
    """Unarchive a resource."""
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


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view with resource counts and metrics."""
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
    from datetime import timedelta

    from django.conf import settings
    from django.utils import timezone

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
    """
    Compare two versions of a resource.

    Args:
        resource_pk: Primary key of the resource
        version1_pk: Primary key of the first version to compare
        version2_pk: Primary key of the second version to compare (optional, defaults to current)
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
            "status": resource.status,
            "source": resource.source,
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
    """
    Show complete version history for a resource.
    """
    resource = get_object_or_404(Resource, pk=resource_pk, is_deleted=False)
    versions = resource.versions.all().order_by("-version_number")

    context = {
        "resource": resource,
        "versions": versions,
    }

    return render(request, "directory/version_history.html", context)
