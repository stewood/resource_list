"""
Resource Forms - Main Resource Creation and Editing Forms

This module contains the main form classes for resource creation and editing
in the resource directory application. The forms provide comprehensive data
validation, user input handling, and workflow management with role-based
permissions and status-based validation rules.

Form Classes:
    - ResourceForm: Main form for resource creation and editing

Features:
    - Complete resource field coverage with Bootstrap styling
    - Role-based field visibility and permissions
    - Status-based validation rules (draft, needs_review, published)
    - User context awareness and automatic field assignment
    - Verification tracking for published resources
    - Custom field widgets with helpful placeholders
    - Staff-only verifier selection

Validation Features:
    - Draft status: Basic requirements (name, contact method)
    - Needs Review: Enhanced requirements (city, state, description, source)
    - Published: Full requirements (verification, verifier, expiry checking)
    - Role-based permissions for sensitive fields (notes)
    - Automatic user assignment and tracking

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.forms.resource_forms import ResourceForm
    
    # Create a new resource form
    form = ResourceForm(data=request.POST, user=request.user)
    if form.is_valid():
        resource = form.save()
"""

from datetime import timedelta
from typing import Any, Dict

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import Resource


class ResourceForm(forms.ModelForm):
    """Form for creating and editing resources with comprehensive validation and role-based permissions.
    
    This form provides a complete interface for resource creation and editing with
    advanced validation rules based on resource status, role-based field visibility,
    and automatic user assignment. It implements the workflow validation requirements
    for draft, needs_review, and published statuses.
    
    Features:
        - Complete resource field coverage with Bootstrap styling
        - Role-based field visibility (notes field for Editor+ roles only)
        - Status-based validation rules with detailed error messages
        - Automatic user assignment for created_by and updated_by fields
        - Verification tracking for published resources
        - Custom field widgets with helpful placeholders
        - Staff-only verifier selection
        
    Validation Rules:
        - Draft: Name required, at least one contact method (phone/email/website)
        - Needs Review: City/state required, description 20+ chars, source required
        - Published: Verification date/verifier required, expiry period checking
        
    Field Visibility:
        - All users: Basic resource information fields
        - Editor/Reviewer/Admin only: Notes field (internal verification details)
        - Staff only: Verifier selection for published resources
        
    Args:
        user: User object for role-based permissions and automatic assignment
        
    Example:
        >>> form = ResourceForm(data=request.POST, user=request.user)
        >>> if form.is_valid():
        ...     resource = form.save()
        ...     print(f"Resource '{resource.name}' saved successfully")
    """

    class Meta:
        """Form metadata defining model, fields, and widgets."""
        model = Resource
        fields = [
            "name",
            "category",
            "service_types",
            "description",
            "phone",
            "email",
            "website",
            "address1",
            "address2",
            "city",
            "state",
            "county",
            "postal_code",
            "hours_of_operation",
            "is_emergency_service",
            "is_24_hour_service",
            "eligibility_requirements",
            "populations_served",
            "insurance_accepted",
            "cost_information",
            "languages_available",
            "capacity",
            "status",
            "source",
            "notes",
            "last_verified_at",
            "last_verified_by",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Resource name"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Description of the resource",
                }
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone number"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "Website URL"}
            ),
            "address1": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Address line 1"}
            ),
            "address2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Address line 2 (optional)",
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State (2-letter code)",
                    "maxlength": 2,
                }
            ),
            "county": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "County or parish name"}
            ),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Postal code"}
            ),
            "hours_of_operation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Service hours and availability (e.g., Mon-Fri 9AM-5PM, 24/7)",
                }
            ),
            "is_emergency_service": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_24_hour_service": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "eligibility_requirements": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Qualification criteria and requirements",
                }
            ),
            "populations_served": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Target demographics (e.g., veterans, women, children)",
                }
            ),
            "insurance_accepted": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Insurance plans accepted for medical services",
                }
            ),
            "cost_information": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Financial details and cost information",
                }
            ),
            "languages_available": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Languages supported for accessibility",
                }
            ),
            "capacity": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Service capacity information",
                }
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "source": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Source of this information",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "INTERNAL USE ONLY - Verification details: Include contact person, phone numbers, websites, dates contacted, and verification methods. Example: 'Contacted Jane Smith (502-555-1234) on 8/15/2024. Hours confirmed via website: www.example.org/hours. Eligibility requirements verified by phone call.'",
                }
            ),
            "last_verified_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "last_verified_by": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the form with user context and role-based field configuration.
        
        This method sets up the form with user-specific configurations including
        role-based field visibility, verifier filtering, and initial values.
        It handles the user parameter and configures the form based on user
        permissions and context.
        
        Args:
            *args: Positional arguments passed to the parent form
            **kwargs: Keyword arguments including:
                - user: User object for role-based permissions (optional)
                - Other standard form arguments (data, files, instance, etc.)
                
        Note:
            The user parameter is extracted from kwargs and stored as an instance
            attribute for use in validation and save methods. If no user is provided,
            role-based features are disabled.
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter verifiers to only include staff users
        if "last_verified_by" in self.fields:
            self.fields["last_verified_by"].queryset = User.objects.filter(
                is_staff=True
            )

        # Hide notes field for non-editor users
        if self.user and not self._user_can_edit_notes(self.user):
            if "notes" in self.fields:
                del self.fields["notes"]

        # Set initial values
        if not self.instance.pk:  # New resource
            self.fields["status"].initial = "draft"
            if self.user:
                self.fields["last_verified_by"].initial = self.user

    def _user_can_edit_notes(self, user: User) -> bool:
        """Check if user can edit notes field (Editor role or higher).
        
        This method determines whether a user has permission to view and edit
        the notes field, which contains internal verification details and is
        restricted to users with Editor, Reviewer, or Admin roles.
        
        Args:
            user: User object to check permissions for
            
        Returns:
            bool: True if user has Editor, Reviewer, or Admin role, False otherwise
            
        Note:
            This is a private method used internally by the form to control
            field visibility. The notes field contains sensitive internal
            information and should only be accessible to authorized users.
        """
        from ..permissions import user_has_role
        return user_has_role(user, "Editor") or user_has_role(user, "Reviewer") or user_has_role(user, "Admin")

    def clean(self) -> Dict[str, Any]:
        """Custom validation for the form with status-based validation rules.
        
        This method implements comprehensive validation rules based on the resource
        status being set. It enforces different requirements for draft, needs_review,
        and published statuses, ensuring data quality and workflow compliance.
        
        Validation Rules:
            - Draft: Name required, at least one contact method (phone/email/website)
            - Needs Review: City/state required, description 20+ chars, source required
            - Published: Verification date/verifier required, expiry period checking
            
        Args:
            None (uses cleaned_data from parent clean method)
            
        Returns:
            Dict[str, Any]: Cleaned form data
            
        Raises:
            ValidationError: If validation rules are not met for the target status
            
        Note:
            This method extends the parent clean() method and applies additional
            validation rules based on the status field value. It ensures that
            resources meet the appropriate requirements for their target status.
        """
        cleaned_data = super().clean()

        # Get the status being set
        status = cleaned_data.get("status")

        # Draft validation
        if status == "draft":
            name = cleaned_data.get("name")
            phone = cleaned_data.get("phone")
            email = cleaned_data.get("email")
            website = cleaned_data.get("website")

            if not name:
                raise ValidationError("Name is required for draft resources.")

            if not any([phone, email, website]):
                raise ValidationError(
                    "At least one contact method (phone, email, or website) is required."
                )

        # Needs review validation
        elif status == "needs_review":
            city = cleaned_data.get("city")
            state = cleaned_data.get("state")
            description = cleaned_data.get("description")
            source = cleaned_data.get("source")

            if not city or not state:
                raise ValidationError("City and state are required for review.")

            if not description or len(description) < 20:
                raise ValidationError(
                    "Description must be at least 20 characters for review."
                )

            if not source:
                raise ValidationError("Source is required for review.")

        # Published validation
        elif status == "published":
            last_verified_at = cleaned_data.get("last_verified_at")
            last_verified_by = cleaned_data.get("last_verified_by")

            if not last_verified_at:
                raise ValidationError(
                    "Verification date is required for published resources."
                )

            if not last_verified_by:
                raise ValidationError("Verifier is required for published resources.")

            # Check if verification is within expiry period
            if last_verified_at:
                from django.conf import settings

                expiry_date = last_verified_at + timedelta(
                    days=settings.VERIFICATION_EXPIRY_DAYS
                )
                if timezone.now() > expiry_date:
                    raise ValidationError(
                        f"Verification must be within {settings.VERIFICATION_EXPIRY_DAYS} days."
                    )

        return cleaned_data

    def save(self, commit: bool = True) -> Resource:
        """Save the form with proper user assignment and tracking.
        
        This method saves the resource with automatic user assignment for
        created_by and updated_by fields. It handles both new resource creation
        and existing resource updates with appropriate user tracking.
        
        Args:
            commit: Whether to save the resource to the database immediately
                   (default: True)
                   
        Returns:
            Resource: The saved resource instance
            
        Note:
            If commit=False, the resource is not saved to the database but
            the user assignment is still applied to the instance. The caller
            is responsible for saving the resource later.
        """
        resource = super().save(commit=False)

        # Set the user who is making the change
        if self.user:
            if not resource.pk:  # New resource
                resource.created_by = self.user
            resource.updated_by = self.user

        if commit:
            resource.save()
            
            # Handle service areas if provided
            self._save_service_areas(resource)
            
        return resource

    def _save_service_areas(self, resource: Resource) -> None:
        """Save service areas for the resource.
        
        This method handles the association of coverage areas with the resource
        based on the service_areas data provided in the form.
        
        Args:
            resource: The resource instance to associate service areas with
        """
        service_areas_data = self.data.get('service_areas')
        if service_areas_data:
            try:
                import json
                coverage_area_ids = json.loads(service_areas_data)
                
                # Clear existing associations using the through model
                from ..models import ResourceCoverage
                ResourceCoverage.objects.filter(resource=resource).delete()
                
                # Add new associations
                if coverage_area_ids:
                    from ..models import CoverageArea
                    coverage_areas = CoverageArea.objects.filter(id__in=coverage_area_ids)
                    
                    # Create associations through the through model
                    associations = []
                    for coverage_area in coverage_areas:
                        associations.append(ResourceCoverage(
                            resource=resource,
                            coverage_area=coverage_area,
                            created_by=self.user if self.user else None,
                            notes='Added via resource form'
                        ))
                    
                    if associations:
                        ResourceCoverage.objects.bulk_create(associations)
                    
            except (json.JSONDecodeError, ValueError) as e:
                # Log error but don't fail the form save
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error processing service areas for resource {resource.id}: {e}")
