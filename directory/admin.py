"""
Admin interface for the directory app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Resource, TaxonomyCategory, ResourceVersion, AuditLog


@admin.register(TaxonomyCategory)
class TaxonomyCategoryAdmin(admin.ModelAdmin):
    """Admin interface for taxonomy categories."""
    
    list_display = ['name', 'slug', 'resource_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def resource_count(self, obj):
        """Display the number of resources in this category."""
        return obj.resources.count()
    resource_count.short_description = 'Resources'


class ResourceVersionInline(admin.TabularInline):
    """Inline display of resource versions."""
    
    model = ResourceVersion
    extra = 0
    readonly_fields = [
        'version_number', 'change_type', 'changed_by', 
        'changed_at', 'changed_fields'
    ]
    fields = ['version_number', 'change_type', 'changed_by', 'changed_at']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin interface for resources."""
    
    list_display = [
        'name', 'category', 'status', 'city', 'state', 
        'needs_verification_display', 'updated_at'
    ]
    list_filter = [
        'status', 'category', 'state', 'city', 'is_deleted',
        'created_at', 'updated_at'
    ]
    search_fields = [
        'name', 'description', 'phone', 'email', 'website',
        'address1', 'address2', 'city', 'state'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'needs_verification', 'has_contact_info'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'status', 'source')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Location', {
            'fields': ('address1', 'address2', 'city', 'state', 'postal_code')
        }),
        ('Verification', {
            'fields': ('last_verified_at', 'last_verified_by')
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by',
                'is_deleted', 'needs_verification', 'has_contact_info'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [ResourceVersionInline]
    
    def needs_verification_display(self, obj):
        """Display verification status with color coding."""
        if obj.needs_verification:
            return format_html(
                '<span style="color: red;">⚠ Needs Verification</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Verified</span>'
        )
    needs_verification_display.short_description = 'Verification Status'
    
    def save_model(self, request, obj, form, change):
        """Set the user who is making the change."""
        if not change:  # Creating new resource
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Filter out deleted resources by default."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)


@admin.register(ResourceVersion)
class ResourceVersionAdmin(admin.ModelAdmin):
    """Admin interface for resource versions."""
    
    list_display = [
        'resource_name', 'version_number', 'change_type', 
        'changed_by', 'changed_at'
    ]
    list_filter = ['change_type', 'changed_at']
    search_fields = ['resource__name']
    readonly_fields = [
        'resource', 'version_number', 'snapshot_json', 
        'changed_fields', 'change_type', 'changed_by', 'changed_at'
    ]
    fields = [
        'resource', 'version_number', 'change_type', 'changed_by', 
        'changed_at', 'snapshot_json', 'changed_fields'
    ]
    
    def resource_name(self, obj):
        """Display resource name with link."""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:directory_resource_change', args=[obj.resource.id]),
            obj.resource.name
        )
    resource_name.short_description = 'Resource'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs."""
    
    list_display = [
        'action', 'actor', 'target_table', 'target_id', 'created_at'
    ]
    list_filter = ['action', 'target_table', 'created_at', 'actor']
    search_fields = ['action', 'actor__username', 'target_id']
    readonly_fields = [
        'actor', 'action', 'target_table', 'target_id', 
        'metadata_json', 'created_at'
    ]
    fields = [
        'actor', 'action', 'target_table', 'target_id', 
        'metadata_json', 'created_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
