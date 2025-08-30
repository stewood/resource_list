"""
Resource Coverage Through Model - Audit Trail for Resource-CoverageArea Relationships

This module contains the ResourceCoverage through model that manages the many-to-many
relationship between Resources and CoverageAreas with full audit trail support.

Author: Resource Directory Team
Created: 2025-01-15
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models import ResourceCoverage

    # Create a resource-coverage association
    association = ResourceCoverage.objects.create(
        resource=resource,
        coverage_area=coverage_area,
        created_by=user
    )
"""

from typing import Any

from django.contrib.auth.models import User
from django.db import models


class ResourceCoverage(models.Model):
    """Through model for Resource-CoverageArea relationship with audit trail.

    This model manages the many-to-many relationship between Resources and
    CoverageAreas while providing a complete audit trail of when associations
    were created, by whom, and any additional metadata.

    The through model allows for:
    - Audit trail of all resource-coverage area associations
    - Tracking who created each association
    - Additional metadata about the association
    - Proper cleanup when resources or coverage areas are deleted

    Attributes:
        resource: The resource being associated
        coverage_area: The coverage area being associated
        created_by: User who created the association
        created_at: When the association was created

    Example:
        >>> # Associate a resource with a coverage area
        >>> association = ResourceCoverage.objects.create(
        ...     resource=crisis_center,
        ...     coverage_area=laurel_county,
        ...     created_by=admin_user
        ... )

        >>> # Get all coverage areas for a resource
        >>> resource.coverage_areas.all()

        >>> # Get all resources in a coverage area
        >>> coverage_area.resources.all()
    """

    # Core relationship fields
    resource = models.ForeignKey(
        "Resource",
        on_delete=models.CASCADE,
        related_name="resource_coverage_associations",
        help_text="The resource being associated with a coverage area",
    )
    coverage_area = models.ForeignKey(
        "CoverageArea",
        on_delete=models.CASCADE,
        related_name="resource_coverage_associations",
        help_text="The coverage area being associated with a resource",
    )

    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_resource_coverage_associations",
        help_text="User who created this resource-coverage area association",
    )

    # Additional metadata (optional)
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this resource-coverage area association",
    )

    class Meta:
        # Ensure unique resource-coverage area combinations
        unique_together = ["resource", "coverage_area"]
        ordering = ["-created_at"]
        verbose_name = "Resource Coverage Association"
        verbose_name_plural = "Resource Coverage Associations"
        indexes = [
            models.Index(fields=["resource"]),
            models.Index(fields=["coverage_area"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self) -> str:
        """Return a descriptive string representation."""
        return f"{self.resource.name} → {self.coverage_area.name}"

    def clean(self) -> None:
        """Validate the resource-coverage area association.

        This method implements validation rules:
        - Resource and coverage area must be provided
        - Cannot create duplicate associations
        - Created by user must be provided

        Raises:
            ValidationError: If validation fails
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Basic field validation
        if not self.resource:
            errors["resource"] = "Resource is required."

        if not self.coverage_area:
            errors["coverage_area"] = "Coverage area is required."

        if not self.created_by:
            errors["created_by"] = "Created by user is required."

        # Check for duplicate associations (if this is a new instance)
        if not self.pk and self.resource and self.coverage_area:
            if ResourceCoverage.objects.filter(
                resource=self.resource, coverage_area=self.coverage_area
            ).exists():
                errors["__all__"] = (
                    "This resource is already associated with this coverage area."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the association with validation.

        Args:
            *args: Standard save arguments
            **kwargs: Standard save keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def display_name(self) -> str:
        """Return a formatted display name for the association.

        Returns:
            str: Formatted display name
        """
        return f"{self.resource.name} serves {self.coverage_area.display_name}"

    @property
    def is_active(self) -> bool:
        """Check if this association is active.

        An association is considered active if both the resource and
        coverage area are not archived or deleted.

        Returns:
            bool: True if the association is active
        """
        return (
            not self.resource.is_archived
            and not self.resource.is_deleted
            and self.resource.status == "published"
        )
