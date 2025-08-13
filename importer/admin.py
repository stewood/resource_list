"""
Admin interface for CSV import/export functionality.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import ImportError, ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """Admin interface for ImportJob model."""

    list_display = [
        "name",
        "status",
        "created_by",
        "uploaded_at",
        "total_rows",
        "valid_rows",
        "invalid_rows",
        "success_rate_display",
    ]
    list_filter = ["status", "uploaded_at", "created_by"]
    search_fields = ["name", "description", "file_name"]
    readonly_fields = [
        "file_name",
        "file_size",
        "uploaded_at",
        "started_at",
        "completed_at",
        "total_rows",
        "valid_rows",
        "invalid_rows",
        "resources_created",
        "duration_display",
        "success_rate_display",
        "column_mapping_display",
    ]
    date_hierarchy = "uploaded_at"

    fieldsets = (
        ("Job Information", {"fields": ("name", "description", "created_by")}),
        ("File Information", {"fields": ("file_name", "file_size", "uploaded_at")}),
        (
            "Processing Status",
            {"fields": ("status", "started_at", "completed_at", "duration_display")},
        ),
        (
            "Results",
            {
                "fields": (
                    "total_rows",
                    "valid_rows",
                    "invalid_rows",
                    "resources_created",
                    "success_rate_display",
                )
            },
        ),
        ("Configuration", {"fields": ("skip_header", "column_mapping_display")}),
    )

    def success_rate_display(self, obj):
        """Display success rate as a percentage with color coding."""
        rate = obj.success_rate
        if rate >= 90:
            color = "green"
        elif rate >= 70:
            color = "orange"
        else:
            color = "red"

        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)

    success_rate_display.short_description = "Success Rate"

    def duration_display(self, obj):
        """Display duration in a readable format."""
        duration = obj.duration
        if duration is None:
            return "N/A"

        if duration < 60:
            return f"{duration:.1f} seconds"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            return f"{minutes}m {seconds:.1f}s"

    duration_display.short_description = "Duration"

    def column_mapping_display(self, obj):
        """Display column mapping in a readable format."""
        mapping = obj.column_mapping_dict
        if not mapping:
            return "No mapping configured"

        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">CSV Column</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Resource Field</th></tr>'

        for csv_index, field_name in mapping.items():
            html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{csv_index}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{field_name}</td></tr>'

        html += "</table>"
        return mark_safe(html)

    column_mapping_display.short_description = "Column Mapping"


@admin.register(ImportError)
class ImportErrorAdmin(admin.ModelAdmin):
    """Admin interface for ImportError model."""

    list_display = [
        "import_job",
        "row_number",
        "error_type",
        "field_name",
        "error_message_short",
        "created_at",
    ]
    list_filter = ["error_type", "created_at", "import_job__status"]
    search_fields = ["error_message", "field_name", "import_job__name"]
    readonly_fields = [
        "import_job",
        "row_number",
        "error_type",
        "field_name",
        "error_message",
        "row_data_display",
        "created_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Error Information",
            {
                "fields": (
                    "import_job",
                    "row_number",
                    "error_type",
                    "field_name",
                    "error_message",
                )
            },
        ),
        ("Row Data", {"fields": ("row_data_display",)}),
        ("Metadata", {"fields": ("created_at",)}),
    )

    def error_message_short(self, obj):
        """Display truncated error message."""
        message = obj.error_message
        if len(message) > 50:
            return f"{message[:50]}..."
        return message

    error_message_short.short_description = "Error Message"

    def row_data_display(self, obj):
        """Display row data in a readable format."""
        row_data = obj.row_data_dict
        if not row_data:
            return "No row data available"

        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Column</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Value</th></tr>'

        for column_index, value in row_data.items():
            html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{column_index}</td>'
            html += (
                f'<td style="border: 1px solid #ddd; padding: 8px;">{value}</td></tr>'
            )

        html += "</table>"
        return mark_safe(html)

    row_data_display.short_description = "Row Data"
