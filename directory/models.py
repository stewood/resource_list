"""
Models for the resource directory application.
"""

import json
from datetime import timedelta
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection, models
from django.db.models import Q
from django.utils import timezone


class ResourceManager(models.Manager):
    """Custom manager for Resource model with FTS5 search capabilities."""

    def get_queryset(self):
        """Return only non-archived, non-deleted resources by default."""
        return super().get_queryset().filter(is_archived=False, is_deleted=False)

    def all_including_archived(self):
        """Return all resources including archived ones."""
        return super().get_queryset().filter(is_deleted=False)

    def archived(self):
        """Return only archived resources."""
        return super().get_queryset().filter(is_archived=True, is_deleted=False)

    def search_fts(self, query: str) -> models.QuerySet:
        """
        Search resources using SQLite FTS5 full-text search.

        Args:
            query: Search query string

        Returns:
            QuerySet of matching resources ordered by relevance
        """
        if not query.strip():
            return self.none()

        try:
            # Use raw SQL to perform FTS5 search
            with connection.cursor() as cursor:
                # Use string formatting for FTS5 query since it doesn't support parameter substitution
                sql = f"""
                    SELECT resource_id, rank
                    FROM resource_fts 
                    WHERE resource_fts MATCH '{query}'
                    ORDER BY rank
                """
                cursor.execute(sql)

                results = cursor.fetchall()

            if not results:
                return self.none()

            # Get resource IDs in order of relevance
            resource_ids = [row[0] for row in results]

            # Create a QuerySet with the results in the correct order
            preserved = models.Case(
                *[models.When(pk=pk, then=pos) for pos, pk in enumerate(resource_ids)]
            )
            return self.filter(pk__in=resource_ids).order_by(preserved)

        except Exception:
            # Fallback to basic search if FTS5 is not available
            return self.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(city__icontains=query)
                | Q(state__icontains=query)
            )

    def search_combined(self, query: str) -> models.QuerySet:
        """
        Combined search using FTS5 for full-text and icontains for exact matches.

        Args:
            query: Search query string

        Returns:
            QuerySet of matching resources
        """
        if not query.strip():
            return self.none()

        # Get FTS5 results
        fts_results = self.search_fts(query)

        # Get exact match results (for fields not in FTS5)
        exact_results = self.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(website__icontains=query)
            | Q(postal_code__icontains=query)
        )

        # Combine and deduplicate results
        combined_ids = list(fts_results.values_list("pk", flat=True))
        combined_ids.extend(list(exact_results.values_list("pk", flat=True)))

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for pk in combined_ids:
            if pk not in seen:
                seen.add(pk)
                unique_ids.append(pk)

        if not unique_ids:
            return self.none()

        # Return results in the combined order
        preserved = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(unique_ids)]
        )
        return self.filter(pk__in=unique_ids).order_by(preserved)


class TaxonomyCategory(models.Model):
    """Categories for organizing resources."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class ServiceType(models.Model):
    """Types of services offered by resources."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Service Type"
        verbose_name_plural = "Service Types"

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class Resource(models.Model):
    """A resource for people experiencing homelessness."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("needs_review", "Needs Review"),
        ("published", "Published"),
    ]

    # Custom manager with FTS5 search capabilities
    objects = ResourceManager()

    # Basic information
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        TaxonomyCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    service_types = models.ManyToManyField(
        ServiceType,
        blank=True,
        related_name="resources",
        help_text="Types of services offered by this resource",
    )
    description = models.TextField(blank=True)

    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Location
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    county = models.CharField(max_length=100, blank=True, help_text="County or parish name")
    postal_code = models.CharField(max_length=10, blank=True)

    # Operational fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    source = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True, help_text="Notes and citations for updates and verification")
    hours_of_operation = models.TextField(blank=True, help_text="Service hours and availability")
    is_emergency_service = models.BooleanField(default=False, help_text="Mark if this is a crisis or emergency service")
    is_24_hour_service = models.BooleanField(default=False, help_text="Mark if this service is available 24/7")
    eligibility_requirements = models.TextField(blank=True, help_text="Qualification criteria and requirements")
    populations_served = models.TextField(blank=True, help_text="Target demographics (e.g., veterans, women, children)")
    insurance_accepted = models.TextField(blank=True, help_text="Insurance plans accepted for medical services")
    cost_information = models.TextField(blank=True, help_text="Financial details and cost information")
    languages_available = models.CharField(max_length=200, blank=True, help_text="Languages supported for accessibility")
    capacity = models.CharField(max_length=100, blank=True, help_text="Service capacity information")

    # Verification
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_resources",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_resources"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="updated_resources"
    )
    is_deleted = models.BooleanField(default=False)

    # Archive fields
    is_archived = models.BooleanField(default=False, help_text="Mark if this resource is archived")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When this resource was archived")
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_resources",
        help_text="User who archived this resource",
    )
    archive_reason = models.TextField(blank=True, help_text="Reason for archiving this resource")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["city"]),
            models.Index(fields=["state"]),
            models.Index(fields=["county"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_emergency_service"]),
            models.Index(fields=["is_24_hour_service"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["is_archived"]),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """Validate the resource data."""
        errors = {}

        # Draft validation
        if self.status == "draft":
            if not self.name:
                errors["name"] = "Name is required for draft resources."

            # At least one contact method required
            if not any([self.phone, self.email, self.website]):
                errors["phone"] = (
                    "At least one contact method (phone, email, or website) is required."
                )

        # Needs review validation
        elif self.status == "needs_review":
            if not self.city or not self.state:
                errors["city"] = "City and state are required for review."

            if len(self.description) < settings.MIN_DESCRIPTION_LENGTH:
                errors["description"] = (
                    f"Description must be at least {settings.MIN_DESCRIPTION_LENGTH} characters for review."
                )

            if not self.source:
                errors["source"] = "Source is required for review."

        # Published validation
        elif self.status == "published":
            if not self.last_verified_at:
                errors["last_verified_at"] = (
                    "Verification date is required for published resources."
                )

            if not self.last_verified_by:
                errors["last_verified_by"] = (
                    "Verifier is required for published resources."
                )

            # Check if verification is within expiry period
            if self.last_verified_at:
                expiry_date = self.last_verified_at + timedelta(
                    days=settings.VERIFICATION_EXPIRY_DAYS
                )
                if timezone.now() > expiry_date:
                    errors["last_verified_at"] = (
                        f"Verification must be within {settings.VERIFICATION_EXPIRY_DAYS} days."
                    )

        # Archive validation
        if self.is_archived:
            if not self.archived_at:
                errors["archived_at"] = "Archive date is required when archiving a resource."
            if not self.archived_by:
                errors["archived_by"] = "Archive user is required when archiving a resource."
            if not self.archive_reason:
                errors["archive_reason"] = "Archive reason is required when archiving a resource."

        # Postal code validation
        if self.state and self.postal_code:
            if not (
                len(self.postal_code) in [5, 10]
                and (len(self.postal_code) == 5 or self.postal_code[5] == "-")
            ):
                errors["postal_code"] = (
                    "Postal code must be 5 digits or 5 digits followed by a hyphen and 4 digits."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the resource with validation and normalization."""
        # Normalize data
        if self.state:
            self.state = self.state.upper()

        if self.phone:
            # Basic phone normalization (remove non-digits)
            self.phone = "".join(filter(str.isdigit, self.phone))

        if self.website:
            # Ensure URL has scheme
            if not self.website.startswith(("http://", "https://")):
                self.website = "https://" + self.website

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def needs_verification(self) -> bool:
        """Check if the resource needs verification."""
        if not self.last_verified_at:
            return True

        expiry_date = self.last_verified_at + timedelta(
            days=settings.VERIFICATION_EXPIRY_DAYS
        )
        return timezone.now() > expiry_date

    @property
    def has_contact_info(self) -> bool:
        """Check if the resource has at least one contact method."""
        return bool(self.phone or self.email or self.website)


class ResourceVersion(models.Model):
    """Immutable snapshots of resource changes."""

    CHANGE_TYPES = [
        ("create", "Create"),
        ("update", "Update"),
        ("status_change", "Status Change"),
    ]

    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    snapshot_json = models.TextField()  # Full resource state at save time
    changed_fields = models.TextField()  # JSON array of changed field names
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    changed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="resource_versions"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["resource", "version_number"]
        ordering = ["-version_number"]

    def __str__(self) -> str:
        return f"{self.resource.name} v{self.version_number}"

    @property
    def snapshot(self) -> Dict[str, Any]:
        """Get the snapshot data as a dictionary."""
        return json.loads(self.snapshot_json)

    @property
    def changed_field_list(self) -> List[str]:
        """Get the list of changed fields."""
        return json.loads(self.changed_fields)


class AuditLog(models.Model):
    """Append-only audit log for all system actions."""

    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="audit_actions"
    )
    action = models.CharField(
        max_length=100
    )  # e.g., 'create_resource', 'update_resource'
    target_table = models.CharField(
        max_length=50
    )  # e.g., 'resource', 'taxonomy_category'
    target_id = models.CharField(max_length=50)  # ID of the affected record
    metadata_json = models.TextField(blank=True)  # Additional context
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor"]),
            models.Index(fields=["action"]),
            models.Index(fields=["target_table"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} by {self.actor.username} at {self.created_at}"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata as a dictionary."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
