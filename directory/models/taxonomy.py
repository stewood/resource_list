"""
Taxonomy Models - Classification and Organization Models

This module contains the taxonomy models for organizing and classifying resources
in the resource directory. These models provide the hierarchical structure and
categorization system that helps users find relevant resources quickly.

Models:
    - TaxonomyCategory: Primary classification categories (e.g., "Mental Health", "Housing")
    - ServiceType: Specific service types offered by resources (e.g., "Crisis Intervention")

Features:
    - Automatic slug generation from names
    - Unique constraints to prevent duplicates
    - Descriptive text fields for detailed explanations
    - Timestamp tracking for audit purposes

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models.taxonomy import TaxonomyCategory, ServiceType

    # Create a category
    category = TaxonomyCategory.objects.create(
        name="Mental Health Services",
        description="Resources for mental health support and counseling"
    )

    # Create a service type
    service_type = ServiceType.objects.create(
        name="Crisis Intervention",
        description="Immediate assistance for crisis situations"
    )
"""

from typing import Any

from django.db import models


class TaxonomyCategory(models.Model):
    """Taxonomy category for organizing and classifying resources.

    This model represents the primary classification system for resources,
    allowing them to be organized into logical categories such as "Mental Health",
    "Housing", "Food Assistance", etc. Categories help users find relevant
    resources quickly and provide a hierarchical structure for the resource directory.

    Each category can contain multiple resources and is used for filtering
    and organizing the resource list views.

    Attributes:
        name (str): Human-readable name of the category (e.g., "Mental Health")
        slug (str): URL-friendly version of the name (e.g., "mental-health")
        description (str): Detailed description of what this category includes
        created_at (datetime): When the category was created
        updated_at (datetime): When the category was last modified

    Example:
        >>> category = TaxonomyCategory.objects.create(
        ...     name="Mental Health Services",
        ...     description="Resources for mental health support and counseling"
        ... )
        >>> print(category.slug)  # "mental-health-services"
    """

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
        """Return the category name as the string representation."""
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the category, auto-generating slug if not provided.

        If no slug is provided, this method automatically generates one
        from the category name by converting to lowercase and replacing
        spaces with hyphens.

        Args:
            *args: Standard save arguments
            **kwargs: Standard save keyword arguments
        """
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class ServiceType(models.Model):
    """Service type classification for resources.

    This model represents specific types of services that resources can offer,
    such as "Crisis Intervention", "Case Management", "Emergency Shelter", etc.
    Service types provide a more granular classification than categories and
    allow resources to be tagged with multiple service types.

    Service types help users find resources that offer specific services
    and enable advanced filtering and search capabilities.

    Attributes:
        name (str): Human-readable name of the service type (e.g., "Crisis Intervention")
        slug (str): URL-friendly version of the name (e.g., "crisis-intervention")
        description (str): Detailed description of what this service type includes
        created_at (datetime): When the service type was created

    Example:
        >>> service_type = ServiceType.objects.create(
        ...     name="Crisis Intervention",
        ...     description="Immediate assistance for crisis situations"
        ... )
        >>> print(service_type.slug)  # "crisis-intervention"
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Service Type"
        verbose_name_plural = "Service Types"

    def __str__(self) -> str:
        """Return the service type name as the string representation."""
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the service type, auto-generating slug if not provided.

        If no slug is provided, this method automatically generates one
        from the service type name by converting to lowercase and replacing
        spaces with hyphens.

        Args:
            *args: Standard save arguments
            **kwargs: Standard save keyword arguments
        """
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)
