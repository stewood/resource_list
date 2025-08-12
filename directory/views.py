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
from .models import Resource, TaxonomyCategory
from .permissions import (
    require_editor, require_reviewer, require_admin,
    user_can_publish, user_can_submit_for_review
)


class ResourceListView(LoginRequiredMixin, ListView):
    """List view for resources with filtering and search."""
    
    model = Resource
    template_name = 'directory/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter queryset based on search and filter parameters."""
        queryset = Resource.objects.filter(is_deleted=False)
        
        # Search
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(state__icontains=search_query)
            )
        
        # Filters
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        category_filter = self.request.GET.get('category', '')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        city_filter = self.request.GET.get('city', '')
        if city_filter:
            queryset = queryset.filter(city__icontains=city_filter)
        
        state_filter = self.request.GET.get('state', '')
        if state_filter:
            queryset = queryset.filter(state__icontains=state_filter)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-updated_at')
        if sort_by in ['name', '-name', 'city', '-city', 'status', '-status', 'updated_at', '-updated_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['categories'] = TaxonomyCategory.objects.all().order_by('name')
        context['status_choices'] = Resource.STATUS_CHOICES
        
        # Add current filters for form persistence
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'city': self.request.GET.get('city', ''),
            'state': self.request.GET.get('state', ''),
            'sort': self.request.GET.get('sort', '-updated_at'),
        }
        
        # Add permission context
        context['user_can_publish'] = user_can_publish(self.request.user)
        context['user_can_submit_review'] = user_can_submit_for_review(self.request.user)
        
        return context


class ResourceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single resource."""
    
    model = Resource
    template_name = 'directory/resource_detail.html'
    context_object_name = 'resource'
    
    def get_queryset(self):
        """Filter out deleted resources."""
        return Resource.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        
        # Add permission context
        context['user_can_publish'] = user_can_publish(self.request.user)
        context['user_can_submit_review'] = user_can_submit_for_review(self.request.user)
        
        # Add version history
        context['versions'] = self.object.versions.all()[:10]  # Last 10 versions
        
        return context


class ResourceCreateView(LoginRequiredMixin, CreateView):
    """Create view for new resources."""
    
    model = Resource
    form_class = ResourceForm
    template_name = 'directory/resource_form.html'
    success_url = reverse_lazy('directory:resource_list')
    
    def get_form_kwargs(self):
        """Pass user to form for validation."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Set the user who created the resource."""
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for existing resources."""
    
    model = Resource
    form_class = ResourceForm
    template_name = 'directory/resource_form.html'
    
    def get_queryset(self):
        """Filter out deleted resources."""
        return Resource.objects.filter(is_deleted=False)
    
    def get_form_kwargs(self):
        """Pass user to form for validation."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Set the user who updated the resource."""
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect to the resource detail page."""
        return reverse('directory:resource_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['action'] = 'Edit'
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
        resource.status = 'needs_review'
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
        resource.status = 'published'
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
        return HttpResponse("Permission denied", status=403)
    
    resource.status = 'needs_review'
    resource.save()
    return HttpResponse("Resource unpublished successfully")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view with resource counts and metrics."""
    # Get resource counts by status
    draft_count = Resource.objects.filter(status='draft', is_deleted=False).count()
    review_count = Resource.objects.filter(status='needs_review', is_deleted=False).count()
    published_count = Resource.objects.filter(status='published', is_deleted=False).count()
    
    # Get resources needing verification
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    
    verification_threshold = timezone.now() - timedelta(days=settings.VERIFICATION_EXPIRY_DAYS)
    needs_verification = Resource.objects.filter(
        status='published',
        is_deleted=False,
        last_verified_at__lt=verification_threshold
    ).count()
    
    # Get recent activity
    recent_resources = Resource.objects.filter(
        is_deleted=False
    ).order_by('-updated_at')[:10]
    
    context = {
        'draft_count': draft_count,
        'review_count': review_count,
        'published_count': published_count,
        'needs_verification': needs_verification,
        'recent_resources': recent_resources,
    }
    
    return render(request, 'directory/dashboard.html', context)
