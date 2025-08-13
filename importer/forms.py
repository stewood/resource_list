"""
Forms for CSV import/export functionality.
"""

import csv
from io import StringIO
from typing import Any, Dict, List

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from directory.models import Resource, TaxonomyCategory

from .models import ImportJob


class CSVUploadForm(forms.ModelForm):
    """Form for uploading CSV files."""

    csv_file = forms.FileField(
        label=_("CSV File"),
        help_text=_("Upload a CSV file with resource data. Maximum size: 10MB."),
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
    )

    class Meta:
        model = ImportJob
        fields = ["name", "description", "skip_header"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter a name for this import job",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description of this import",
                }
            ),
            "skip_header": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_csv_file(self) -> Any:
        """Validate the uploaded CSV file."""
        csv_file = self.cleaned_data.get("csv_file")

        if not csv_file:
            raise ValidationError(_("Please select a CSV file to upload."))

        # Check file size (10MB limit)
        if csv_file.size > 10 * 1024 * 1024:
            raise ValidationError(_("File size must be less than 10MB."))

        # Check file extension
        if not csv_file.name.lower().endswith(".csv"):
            raise ValidationError(_("Please upload a CSV file."))

        # Validate CSV format
        try:
            content = csv_file.read().decode("utf-8")
            csv_file.seek(0)  # Reset file pointer

            # Try to parse as CSV
            csv_file_obj = StringIO(content)
            reader = csv.reader(csv_file_obj)

            # Check if we can read at least one row
            try:
                header = next(reader)
                if not header or len(header) < 2:
                    raise ValidationError(_("CSV file must have at least 2 columns."))
            except StopIteration:
                raise ValidationError(_("CSV file appears to be empty."))

        except UnicodeDecodeError:
            raise ValidationError(_("CSV file must be encoded in UTF-8."))
        except Exception as e:
            raise ValidationError(_(f"Invalid CSV format: {str(e)}"))

        return csv_file

    def save(self, commit: bool = True) -> ImportJob:
        """Save the import job with file information."""
        import_job = super().save(commit=False)

        if self.user:
            import_job.created_by = self.user

        if self.cleaned_data.get("csv_file"):
            csv_file = self.cleaned_data["csv_file"]
            import_job.file_name = csv_file.name
            import_job.file_size = csv_file.size

        if commit:
            import_job.save()

        return import_job


class ColumnMappingForm(forms.Form):
    """Form for mapping CSV columns to resource fields."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.csv_columns = kwargs.pop("csv_columns", [])
        self.current_mapping = kwargs.pop("current_mapping", {})
        super().__init__(*args, **kwargs)

        # Get available resource fields
        resource_fields = self._get_resource_fields()

        # Create choice field for each CSV column
        for column in self.csv_columns:
            field_name = f"column_{column['index']}"
            self.fields[field_name] = forms.ChoiceField(
                choices=[("", "-- Skip this column --")] + resource_fields,
                required=False,
                initial=self.current_mapping.get(str(column["index"]), ""),
                widget=forms.Select(
                    attrs={
                        "class": "form-control",
                        "data-column-index": column["index"],
                        "data-column-name": column["name"],
                    }
                ),
            )

    def _get_resource_fields(self) -> List[tuple]:
        """Get available resource fields for mapping."""
        return [
            ("name", "Name"),
            ("category", "Category"),
            ("service_types", "Service Types"),
            ("description", "Description"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("website", "Website"),
            ("address1", "Address Line 1"),
            ("address2", "Address Line 2"),
            ("city", "City"),
            ("state", "State"),
            ("county", "County"),
            ("postal_code", "Postal Code"),
            ("hours_of_operation", "Hours of Operation"),
            ("is_emergency_service", "Is Emergency Service"),
            ("is_24_hour_service", "Is 24 Hour Service"),
            ("eligibility_requirements", "Eligibility Requirements"),
            ("populations_served", "Populations Served"),
            ("insurance_accepted", "Insurance Accepted"),
            ("cost_information", "Cost Information"),
            ("languages_available", "Languages Available"),
            ("capacity", "Capacity"),
            ("source", "Source"),
        ]

    def get_column_mapping(self) -> Dict[str, str]:
        """Get the column mapping as a dictionary."""
        mapping = {}
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith("column_") and value:
                column_index = field_name.replace("column_", "")
                mapping[column_index] = value
        return mapping


class ImportPreviewForm(forms.Form):
    """Form for confirming import after preview."""

    confirm_import = forms.BooleanField(
        label=_("I confirm that I want to import these resources"),
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_confirm_import(self) -> bool:
        """Validate confirmation."""
        confirmed = self.cleaned_data.get("confirm_import")
        if not confirmed:
            raise ValidationError(_("You must confirm the import to proceed."))
        return confirmed


class ExportForm(forms.Form):
    """Form for configuring CSV export."""

    # Filter options
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

    # Export options
    include_header = forms.BooleanField(
        label=_("Include header row"),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    fields_to_export = forms.MultipleChoiceField(
        choices=[
            ("name", "Name"),
            ("category", "Category"),
            ("description", "Description"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("website", "Website"),
            ("address1", "Address Line 1"),
            ("address2", "Address Line 2"),
            ("city", "City"),
            ("state", "State"),
            ("postal_code", "Postal Code"),
            ("status", "Status"),
            ("source", "Source"),
            ("last_verified_at", "Last Verified At"),
            ("created_at", "Created At"),
            ("updated_at", "Updated At"),
        ],
        initial=[
            "name",
            "category",
            "description",
            "phone",
            "email",
            "website",
            "address1",
            "city",
            "state",
            "postal_code",
            "status",
            "source",
        ],
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    def get_queryset(self) -> Any:
        """Get filtered queryset based on form data."""
        queryset = Resource.objects.filter(is_deleted=False)

        # Apply filters
        if self.cleaned_data.get("status"):
            queryset = queryset.filter(status=self.cleaned_data["status"])

        if self.cleaned_data.get("category"):
            queryset = queryset.filter(category=self.cleaned_data["category"])

        if self.cleaned_data.get("city"):
            queryset = queryset.filter(city__icontains=self.cleaned_data["city"])

        if self.cleaned_data.get("state"):
            queryset = queryset.filter(state__icontains=self.cleaned_data["state"])

        return queryset.order_by("name")
