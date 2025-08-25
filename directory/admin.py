"""
Admin interface for the directory app.
"""

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import AuditLog, Resource, ResourceVersion, ServiceType, TaxonomyCategory
from .permissions import (user_can_hard_delete, user_can_manage_taxonomies,
                          user_can_manage_users, user_can_publish,
                          user_can_submit_for_review, user_can_verify,
                          user_is_admin, user_is_editor, user_is_reviewer)
from .utils import export_resources_to_csv


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    """Admin interface for service types."""

    list_display = ["name", "slug", "resource_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at"]

    def resource_count(self, obj):
        """Display the number of resources using this service type."""
        return obj.resources.count()

    resource_count.short_description = "Resources"

    def has_add_permission(self, request):
        """Only Reviewers and Admins can add service types."""
        return user_can_manage_taxonomies(request.user)

    def has_change_permission(self, request, obj=None):
        """Only Reviewers and Admins can change service types."""
        return user_can_manage_taxonomies(request.user)

    def has_delete_permission(self, request, obj=None):
        """Only Admins can delete service types."""
        return user_is_admin(request.user)


@admin.register(TaxonomyCategory)
class TaxonomyCategoryAdmin(admin.ModelAdmin):
    """Admin interface for taxonomy categories."""

    list_display = ["name", "slug", "resource_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def resource_count(self, obj):
        """Display the number of resources in this category."""
        return obj.resources.count()

    resource_count.short_description = "Resources"

    def has_add_permission(self, request):
        """Only Reviewers and Admins can add categories."""
        return user_can_manage_taxonomies(request.user)

    def has_change_permission(self, request, obj=None):
        """Only Reviewers and Admins can change categories."""
        return user_can_manage_taxonomies(request.user)

    def has_delete_permission(self, request, obj=None):
        """Only Admins can delete categories."""
        return user_is_admin(request.user)


class ResourceVersionInline(admin.TabularInline):
    """Inline display of resource versions."""

    model = ResourceVersion
    extra = 0
    readonly_fields = [
        "version_number",
        "change_type",
        "changed_by",
        "changed_at",
        "changed_fields",
    ]
    fields = ["version_number", "change_type", "changed_by", "changed_at"]
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin interface for resources."""

    list_display = [
        "name",
        "category",
        "status",
        "city",
        "state",
        "county",
        "is_emergency_service",
        "is_24_hour_service",
        "is_archived",
        "needs_verification_display",
        "updated_at",
    ]
    list_filter = [
        "status",
        "category",
        "service_types",
        "state",
        "city",
        "county",
        "is_emergency_service",
        "is_24_hour_service",
        "is_archived",
        "is_deleted",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "name",
        "description",
        "phone",
        "email",
        "website",
        "address1",
        "address2",
        "city",
        "state",
        "county",
        "source",
        "hours_of_operation",
        "eligibility_requirements",
        "populations_served",
        "insurance_accepted",
        "cost_information",
        "languages_available",
        "capacity",
        "notes",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "archived_at",
        "archived_by",
        "needs_verification",
        "has_contact_info",
        "next_verification_date",
    ]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "category", "service_types", "description", "status")},
        ),
        (
            "Source Information",
            {
                "fields": ("source",),
                "description": "Public source attribution for this information (e.g., 'Kentucky Cabinet for Health and Family Services', 'Organization Website'). This will be displayed to the public.",
            },
        ),
        (
            "Verification Notes (Internal)",
            {
                "fields": ("notes",),
                "description": "INTERNAL USE ONLY - Verification details, contact information, and audit trail. This field is NOT visible to the public and should only be used by editors for tracking verification sources, contact person details, dates contacted, and verification methods.",
            },
        ),
        ("Contact Information", {"fields": ("phone", "email", "website")}),
        (
            "Location",
            {"fields": ("address1", "address2", "city", "state", "county", "postal_code")},
        ),
        (
            "Service Details",
            {
                "fields": (
                    "hours_of_operation",
                    "is_emergency_service",
                    "is_24_hour_service",
                    "eligibility_requirements",
                    "populations_served",
                    "insurance_accepted",
                    "cost_information",
                    "languages_available",
                    "capacity",
                )
            },
        ),
        ("Verification", {"fields": ("last_verified_at", "last_verified_by", "verification_frequency_days", "next_verification_date")}),
        (
            "Archive Information",
            {
                "fields": ("is_archived", "archived_at", "archived_by", "archive_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                    "is_deleted",
                    "needs_verification",
                    "has_contact_info",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [ResourceVersionInline]
    actions = ["submit_for_review", "publish_resource", "unpublish_resource", "archive_resources", "unarchive_resources", "export_to_csv"]

    def needs_verification_display(self, obj):
        """Display verification status with color coding."""
        if obj.needs_verification:
            return format_html('<span style="color: red;">⚠ Needs Verification</span>')
        return format_html('<span style="color: green;">✓ Verified</span>')

    needs_verification_display.short_description = "Verification Status"

    def save_model(self, request, obj, form, change):
        """Set the user who is making the change."""
        if not change:  # Creating new resource
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filter out deleted resources by default, but include archived ones."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)

    def has_delete_permission(self, request, obj=None):
        """Only Admins can hard delete resources."""
        return user_can_hard_delete(request.user)

    def has_add_permission(self, request):
        """All authenticated users can add resources."""
        return request.user.is_authenticated

    def has_change_permission(self, request, obj=None):
        """All authenticated users can change resources."""
        return request.user.is_authenticated

    def submit_for_review(self, request, queryset):
        """Submit selected resources for review."""
        if not user_can_submit_for_review(request.user):
            raise PermissionDenied(
                "You don't have permission to submit resources for review."
            )

        updated = queryset.update(status="needs_review")
        self.message_user(
            request, f"Successfully submitted {updated} resource(s) for review."
        )

    submit_for_review.short_description = "Submit selected resources for review"

    def publish_resource(self, request, queryset):
        """Publish selected resources."""
        if not user_can_publish(request.user):
            raise PermissionDenied("You don't have permission to publish resources.")

        # Update verification info
        from django.utils import timezone

        updated = queryset.update(
            status="published",
            last_verified_at=timezone.now(),
            last_verified_by=request.user,
        )
        self.message_user(request, f"Successfully published {updated} resource(s).")

    publish_resource.short_description = "Publish selected resources"

    def unpublish_resource(self, request, queryset):
        """Unpublish selected resources."""
        if not user_can_publish(request.user):
            raise PermissionDenied("You don't have permission to unpublish resources.")

        updated = queryset.update(status="needs_review")
        self.message_user(request, f"Successfully unpublished {updated} resource(s).")

    unpublish_resource.short_description = "Unpublish selected resources"

    def archive_resources(self, request, queryset):
        """Archive selected resources."""
        if not user_can_hard_delete(request.user):
            raise PermissionDenied("You don't have permission to archive resources.")

        # Filter out already archived resources
        to_archive = queryset.filter(is_archived=False)
        
        if not to_archive.exists():
            self.message_user(request, "No resources to archive.")
            return

        # For bulk archive, we'll set a generic reason
        from django.utils import timezone
        
        updated = to_archive.update(
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=request.user,
            archive_reason="Bulk archived by admin",
        )
        self.message_user(request, f"Successfully archived {updated} resource(s).")

    archive_resources.short_description = "Archive selected resources"

    def unarchive_resources(self, request, queryset):
        """Unarchive selected resources."""
        if not user_can_hard_delete(request.user):
            raise PermissionDenied("You don't have permission to unarchive resources.")

        # Filter to only archived resources
        to_unarchive = queryset.filter(is_archived=True)
        
        if not to_unarchive.exists():
            self.message_user(request, "No archived resources to unarchive.")
            return

        updated = to_unarchive.update(
            is_archived=False,
            archived_at=None,
            archived_by=None,
            archive_reason="",
        )
        self.message_user(request, f"Successfully unarchived {updated} resource(s).")

    unarchive_resources.short_description = "Unarchive selected resources"

    def export_to_csv(self, request, queryset):
        """Export selected resources to CSV."""
        if not user_is_admin(request.user):
            raise PermissionDenied("You don't have permission to export resources.")

        # If no resources are selected, export all non-deleted resources
        if not queryset.exists():
            queryset = Resource.objects.filter(is_deleted=False)

        return export_resources_to_csv(queryset, include_header=True)

    export_to_csv.short_description = "Export selected resources to CSV"


@admin.register(ResourceVersion)
class ResourceVersionAdmin(admin.ModelAdmin):
    """Admin interface for resource versions."""

    list_display = [
        "resource_name",
        "version_number",
        "change_type",
        "changed_by",
        "changed_at",
    ]
    list_filter = ["change_type", "changed_at"]
    search_fields = ["resource__name"]
    readonly_fields = [
        "resource",
        "version_number",
        "snapshot_json",
        "changed_fields",
        "change_type",
        "changed_by",
        "changed_at",
    ]
    fields = [
        "resource",
        "version_number",
        "change_type",
        "changed_by",
        "changed_at",
        "snapshot_json",
        "changed_fields",
    ]

    def resource_name(self, obj):
        """Display resource name with link."""
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:directory_resource_change", args=[obj.resource.id]),
            obj.resource.name,
        )

    resource_name.short_description = "Resource"

    def has_add_permission(self, request):
        """Versions are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Versions are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Versions cannot be deleted."""
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs."""

    list_display = ["action", "actor", "target_table", "target_id", "created_at"]
    list_filter = ["action", "target_table", "created_at", "actor"]
    search_fields = ["action", "actor__username", "target_id"]
    readonly_fields = [
        "actor",
        "action",
        "target_table",
        "target_id",
        "metadata_json",
        "created_at",
    ]
    fields = [
        "actor",
        "action",
        "target_table",
        "target_id",
        "metadata_json",
        "created_at",
    ]

    def has_add_permission(self, request):
        """Audit logs are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs cannot be deleted."""
        return False
