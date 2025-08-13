"""
Models for CSV import/export functionality.
"""

import csv
import json
from io import StringIO
from typing import Any, Dict, List, Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from directory.models import Resource, ServiceType, TaxonomyCategory


class ImportJob(models.Model):
    """Track CSV import jobs and their status."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    # Job metadata
    name = models.CharField(max_length=200, help_text="Name for this import job")
    description = models.TextField(blank=True, help_text="Optional description")

    # File information
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)
    resources_created = models.PositiveIntegerField(default=0)

    # Configuration
    column_mapping = models.TextField(
        blank=True, help_text="JSON mapping of CSV columns to resource fields"
    )
    skip_header = models.BooleanField(
        default=True, help_text="Skip the first row as header"
    )

    # User tracking
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="import_jobs"
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"

    @property
    def column_mapping_dict(self) -> Dict[str, str]:
        """Get column mapping as a dictionary."""
        if self.column_mapping:
            return json.loads(self.column_mapping)
        return {}

    @column_mapping_dict.setter
    def column_mapping_dict(self, mapping: Dict[str, str]) -> None:
        """Set column mapping from a dictionary."""
        self.column_mapping = json.dumps(mapping)

    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the import job in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.valid_rows / self.total_rows) * 100


class ImportError(models.Model):
    """Track validation errors for individual rows in CSV imports."""

    ERROR_TYPES = [
        ("validation", "Validation Error"),
        ("mapping", "Column Mapping Error"),
        ("data_type", "Data Type Error"),
        ("required_field", "Required Field Missing"),
        ("format", "Format Error"),
    ]

    import_job = models.ForeignKey(
        ImportJob, on_delete=models.CASCADE, related_name="errors"
    )
    row_number = models.PositiveIntegerField(
        help_text="Row number in the CSV file (1-based)"
    )
    field_name = models.CharField(
        max_length=100, blank=True, help_text="Field that caused the error"
    )
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    error_message = models.TextField(help_text="Detailed error message")
    row_data = models.TextField(
        blank=True, help_text="JSON representation of the row data"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_number"]

    def __str__(self) -> str:
        return f"Row {self.row_number}: {self.error_message}"

    @property
    def row_data_dict(self) -> Dict[str, Any]:
        """Get row data as a dictionary."""
        if self.row_data:
            return json.loads(self.row_data)
        return {}


class CSVProcessor:
    """Utility class for processing CSV files."""

    def __init__(self, import_job: ImportJob):
        self.import_job = import_job
        self.column_mapping = import_job.column_mapping_dict

    def validate_csv_structure(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Validate CSV structure and return column information.

        Args:
            csv_content: CSV file content as string

        Returns:
            List of column information dictionaries
        """
        try:
            csv_file = StringIO(csv_content)
            reader = csv.reader(csv_file)

            # Read header row
            header_row = next(reader)

            columns = []
            for i, column_name in enumerate(header_row):
                columns.append(
                    {"index": i, "name": column_name.strip(), "sample_values": []}
                )

            # Read a few rows to get sample values
            csv_file.seek(0)
            reader = csv.reader(csv_file)
            next(reader)  # Skip header

            for row_num, row in enumerate(reader):
                if row_num >= 5:  # Only sample first 5 rows
                    break

                for i, value in enumerate(row):
                    if i < len(columns) and value.strip():
                        columns[i]["sample_values"].append(value.strip())

            return columns

        except Exception as e:
            raise ValidationError(f"Invalid CSV format: {str(e)}")

    def process_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Process CSV content and create resources.

        Args:
            csv_content: CSV file content as string

        Returns:
            Dictionary with processing results
        """
        results = {
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "resources_created": 0,
            "errors": [],
        }

        try:
            csv_file = StringIO(csv_content)
            reader = csv.reader(csv_file)

            # Skip header if configured
            if self.import_job.skip_header:
                next(reader)

            for row_num, row in enumerate(reader):
                results["total_rows"] += 1
                actual_row_num = row_num + (2 if self.import_job.skip_header else 1)

                try:
                    # Map row data to resource fields
                    resource_data = self._map_row_to_resource(row)

                    # Validate resource data
                    self._validate_resource_data(resource_data, actual_row_num)

                    # Create resource
                    resource = self._create_resource(resource_data)
                    results["resources_created"] += 1
                    results["valid_rows"] += 1

                except ValidationError as e:
                    results["invalid_rows"] += 1
                    self._create_import_error(actual_row_num, row, str(e), "validation")
                    results["errors"].append({"row": actual_row_num, "error": str(e)})
                except Exception as e:
                    results["invalid_rows"] += 1
                    self._create_import_error(actual_row_num, row, str(e), "data_type")
                    results["errors"].append({"row": actual_row_num, "error": str(e)})

            return results

        except Exception as e:
            raise ValidationError(f"CSV processing failed: {str(e)}")

    def _map_row_to_resource(self, row: List[str]) -> Dict[str, Any]:
        """
        Map CSV row data to resource fields.

        Args:
            row: List of string values from CSV row

        Returns:
            Dictionary mapping resource field names to values
        """
        resource_data = {
            "status": "draft",  # Default to draft
            "created_by": self.import_job.created_by,
            "updated_by": self.import_job.created_by,
        }

        for csv_index, field_name in self.column_mapping.items():
            try:
                csv_index = int(csv_index)
                if csv_index < len(row):
                    value = row[csv_index].strip()
                    if value:  # Only set non-empty values
                        # Handle boolean fields
                        if field_name in ["is_emergency_service", "is_24_hour_service"]:
                            resource_data[field_name] = self._parse_boolean(value)
                        else:
                            resource_data[field_name] = value
            except (ValueError, IndexError):
                continue

        return resource_data

    def _parse_boolean(self, value: str) -> bool:
        """
        Parse string value to boolean.

        Args:
            value: String value to parse

        Returns:
            Boolean value (True for 'true', 'yes', '1', 'on', 'y', False otherwise)
        """
        true_values = ["true", "yes", "1", "on", "y"]
        return value.lower() in true_values

    def _validate_resource_data(self, data: Dict[str, Any], row_num: int) -> None:
        """
        Validate resource data before creation.

        Args:
            data: Dictionary of resource field data to validate
            row_num: Row number for error reporting

        Raises:
            ValidationError: If data fails validation requirements
        """
        # Check required fields for draft status
        if not data.get("name"):
            raise ValidationError(f"Row {row_num}: Name is required")

        # Check for at least one contact method
        contact_methods = [data.get("phone"), data.get("email"), data.get("website")]
        if not any(contact_methods):
            raise ValidationError(
                f"Row {row_num}: At least one contact method (phone, email, or website) is required"
            )

        # Validate category if provided
        if data.get("category"):
            try:
                category = TaxonomyCategory.objects.get(name=data["category"])
                data["category"] = category
            except TaxonomyCategory.DoesNotExist:
                raise ValidationError(
                    f"Row {row_num}: Category '{data['category']}' does not exist"
                )

        # Validate service types if provided
        if data.get("service_types"):
            service_type_names = [name.strip() for name in data["service_types"].split(",")]
            valid_service_types = []
            for service_type_name in service_type_names:
                try:
                    service_type = ServiceType.objects.get(name=service_type_name)
                    valid_service_types.append(service_type)
                except ServiceType.DoesNotExist:
                    raise ValidationError(
                        f"Row {row_num}: Service type '{service_type_name}' does not exist"
                    )
            data["service_types"] = valid_service_types

    def _create_resource(self, data: Dict[str, Any]) -> Resource:
        """
        Create a resource from validated data.

        Args:
            data: Dictionary of validated resource field data

        Returns:
            Created Resource instance
        """
        # Handle ManyToManyField separately
        service_types = data.pop("service_types", [])
        
        # Create the resource
        resource = Resource.objects.create(**data)
        
        # Add service types if provided
        if service_types:
            resource.service_types.set(service_types)
        
        return resource

    def _create_import_error(
        self, row_num: int, row_data: List[str], error_message: str, error_type: str
    ) -> None:
        """
        Create an ImportError record.

        Args:
            row_num: Row number where the error occurred
            row_data: Original row data that caused the error
            error_message: Description of the error
            error_type: Type of error (validation, mapping, data_type, etc.)
        """
        ImportError.objects.create(
            import_job=self.import_job,
            row_number=row_num,
            error_type=error_type,
            error_message=error_message,
            row_data=json.dumps(dict(enumerate(row_data))),
        )
