"""
Forms for the resource directory application.
"""

from typing import Any, Dict

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Resource, ServiceType, TaxonomyCategory


class ResourceForm(forms.ModelForm):
    """Form for creating and editing resources."""

    class Meta:
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
        """Initialize the form with user context."""
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
        """Check if user can edit notes field (Editor role or higher)."""
        from .permissions import user_has_role
        return user_has_role(user, "Editor") or user_has_role(user, "Reviewer") or user_has_role(user, "Admin")

    def clean(self) -> Dict[str, Any]:
        """Custom validation for the form."""
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
                from datetime import timedelta

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
        """Save the form with proper user assignment."""
        resource = super().save(commit=False)

        # Set the user who is making the change
        if self.user:
            if not resource.pk:  # New resource
                resource.created_by = self.user
            resource.updated_by = self.user

        if commit:
            resource.save()
        return resource


class ResourceFilterForm(forms.Form):
    """Form for filtering resources."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search resources..."}
        ),
    )

    status = forms.ChoiceField(
        choices=[("", "All Statuses")] + Resource.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    category = forms.ModelChoiceField(
        queryset=TaxonomyCategory.objects.all().order_by("name"),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by city"}
        ),
    )

    state = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by state"}
        ),
    )

    sort = forms.ChoiceField(
        choices=[
            ("-updated_at", "Recently Updated"),
            ("name", "Name A-Z"),
            ("-name", "Name Z-A"),
            ("city", "City A-Z"),
            ("-city", "City Z-A"),
            ("status", "Status"),
            ("-status", "Status (Reverse)"),
        ],
        required=False,
        initial="-updated_at",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
