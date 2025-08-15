"""
Resource Model - Core Resource Data Model

This module contains the main Resource model for the resource directory application,
which represents resources that provide services to people experiencing homelessness.
The model includes comprehensive information about resources including contact details,
location, service information, verification status, and workflow management.

Features:
    - Comprehensive resource information storage
    - Status workflow management (draft, needs_review, published)
    - Contact information and location tracking
    - Service type and category relationships
    - Verification and audit trail integration
    - Soft delete and archiving capabilities
    - Custom validation rules based on status
    - Data normalization and cleaning

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models.resource import Resource
    
    # Create a new resource
    resource = Resource.objects.create(
        name="Crisis Intervention Center",
        description="24/7 crisis intervention services",
        phone="555-1234",
        city="London",
        state="KY",
        status="published"
    )
    
    # Search resources
    results = Resource.objects.search_combined("mental health")
"""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .managers import ResourceManager
from .taxonomy import ServiceType, TaxonomyCategory


class Resource(models.Model):
    """Core model representing a resource for people experiencing homelessness.
    
    This is the primary model for storing information about resources that provide
    services to people experiencing homelessness. Each resource represents a physical
    location, organization, or service that can help individuals in need.
    
    The model includes comprehensive information about the resource including:
    - Basic identification and description
    - Contact information and location
    - Service details and operational information
    - Verification and audit trail data
    - Status management and workflow
    
    Resources can be in different states (draft, needs review, published) and
    support soft deletion and archiving for data integrity.
    
    Attributes:
        STATUS_CHOICES: Available status options for resources
        objects: Custom manager with FTS5 search capabilities
        
    Status Workflow:
        - draft: Initial state, not visible to public
        - needs_review: Submitted for review by editors
        - published: Approved and visible to public
        
    Example:
        >>> resource = Resource.objects.create(
        ...     name="Crisis Intervention Center",
        ...     category=mental_health_category,
        ...     description="24/7 crisis intervention services",
        ...     phone="555-1234",
        ...     city="London",
        ...     state="KY",
        ...     status="published"
        ... )
    """

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
    notes = models.TextField(blank=True, help_text="INTERNAL USE ONLY - Notes and citations for updates and verification. This field is NOT visible to the public.")
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
        """Return the resource name as the string representation."""
        return self.name

    def clean(self) -> None:
        """Validate the resource data based on status and business rules.
        
        This method implements comprehensive validation rules that vary based on
        the resource status. The validation ensures data quality and compliance
        with business requirements at each stage of the workflow.
        
        Validation Rules:
            - Draft: Name required, at least one contact method
            - Needs Review: City/state required, description 20+ chars, source required
            - Published: Verification date/verifier required, expiry period checking
            - Archive: Archive metadata required when archiving
            - Email: Valid email format validation
            - Website: Valid URL format validation
            - Phone: Valid phone number format validation
            - State: Valid US state code validation
            
        Raises:
            ValidationError: If validation fails with field-specific errors
        """
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

        # Email validation
        if self.email:
            try:
                from django.core.validators import validate_email
                validate_email(self.email)
            except ValidationError:
                errors["email"] = "Please enter a valid email address."

        # Website validation
        if self.website:
            try:
                from django.core.validators import URLValidator
                validator = URLValidator()
                validator(self.website)
            except ValidationError:
                errors["website"] = "Please enter a valid URL."

        # Phone number validation
        if self.phone:
            phone_errors = self._validate_phone_number(self.phone)
            if phone_errors:
                errors["phone"] = phone_errors

        # State validation
        if self.state:
            state_errors = self._validate_state_code(self.state)
            if state_errors:
                errors["state"] = state_errors

        # Postal code validation
        if self.state and self.postal_code:
            postal_errors = self._validate_postal_code(self.postal_code)
            if postal_errors:
                errors["postal_code"] = postal_errors

        if errors:
            raise ValidationError(errors)

    def _validate_phone_number(self, phone: str) -> str:
        """Validate phone number format.
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            str: Error message if invalid, empty string if valid
        """
        import re
        
        # Remove all non-digits for validation
        digits_only = re.sub(r'\D', '', phone)
        
        # US phone numbers should be 10 or 11 digits
        if len(digits_only) < 10:
            return "Phone number must have at least 10 digits."
        
        if len(digits_only) > 11:
            return "Phone number cannot have more than 11 digits."
        
        # If 11 digits, first digit should be 1 (country code)
        if len(digits_only) == 11 and digits_only[0] != '1':
            return "If phone number has 11 digits, it must start with 1 (country code)."
        
        return ""

    def _validate_state_code(self, state: str) -> str:
        """Validate US state code.
        
        Args:
            state (str): State code to validate
            
        Returns:
            str: Error message if invalid, empty string if valid
        """
        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC', 'PR', 'VI', 'GU', 'MP', 'AS'  # Include territories
        }
        
        if state.upper() not in valid_states:
            return f"'{state}' is not a valid US state or territory code."
        
        return ""

    def _validate_postal_code(self, postal_code: str) -> str:
        """Validate US postal code format.
        
        Args:
            postal_code (str): Postal code to validate
            
        Returns:
            str: Error message if invalid, empty string if valid
        """
        import re
        
        # Pattern for US postal codes: 5 digits or 5+4 format
        pattern = r'^\d{5}(-\d{4})?$'
        
        if not re.match(pattern, postal_code):
            return "Postal code must be 5 digits or 5 digits followed by a hyphen and 4 digits."
        
        return ""

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the resource with validation and data normalization.
        
        This method performs data normalization and validation before saving
        the resource. It ensures consistent data format and validates business
        rules based on the resource status.
        
        Normalization:
            - State codes converted to uppercase
            - Phone numbers stripped of non-digits
            - Website URLs given https:// scheme if missing
            
        Args:
            *args: Standard save arguments
            **kwargs: Standard save keyword arguments
        """
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
        """Check if the resource needs verification.
        
        A resource needs verification if it has never been verified or if
        the verification has expired based on the configured expiry period.
        
        Returns:
            bool: True if verification is needed, False otherwise
        """
        if not self.last_verified_at:
            return True

        expiry_date = self.last_verified_at + timedelta(
            days=settings.VERIFICATION_EXPIRY_DAYS
        )
        return timezone.now() > expiry_date

    @property
    def has_contact_info(self) -> bool:
        """Check if the resource has at least one contact method.
        
        Returns:
            bool: True if phone, email, or website is provided
        """
        return bool(self.phone or self.email or self.website)
