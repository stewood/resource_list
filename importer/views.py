"""
Views for CSV import/export functionality.
"""

import csv
import json
from io import StringIO
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import FormView

from directory.permissions import require_editor

from .forms import (ColumnMappingForm, CSVUploadForm, ExportForm,
                    ImportPreviewForm)
from .models import CSVProcessor, ImportError, ImportJob


class ImportJobListView(LoginRequiredMixin, ListView):
    """List view for import jobs."""

    model = ImportJob
    template_name = "importer/import_job_list.html"
    context_object_name = "import_jobs"
    paginate_by = 20

    def get_queryset(self):
        """Filter queryset to show only user's import jobs."""
        return ImportJob.objects.filter(created_by=self.request.user)


class ImportJobDetailView(LoginRequiredMixin, DetailView):
    """Detail view for an import job."""

    model = ImportJob
    template_name = "importer/import_job_detail.html"
    context_object_name = "import_job"

    def get_queryset(self):
        """Filter queryset to show only user's import jobs."""
        return ImportJob.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Add errors with pagination
        errors = self.object.errors.all()
        paginator = Paginator(errors, 50)  # Show 50 errors per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["error_page_obj"] = page_obj
        context["total_errors"] = errors.count()

        return context


class CSVUploadView(LoginRequiredMixin, CreateView):
    """View for uploading CSV files."""

    model = ImportJob
    form_class = CSVUploadForm
    template_name = "importer/csv_upload.html"
    success_url = reverse_lazy("importer:column_mapping")

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save the import job and store CSV content in session."""
        import_job = form.save()

        # Read and store CSV content in session
        csv_file = form.cleaned_data["csv_file"]
        csv_content = csv_file.read().decode("utf-8")

        self.request.session["csv_content"] = csv_content
        self.request.session["import_job_id"] = import_job.id

        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to column mapping with the import job ID."""
        return reverse(
            "importer:column_mapping",
            kwargs={"pk": self.request.session.get("import_job_id")},
        )


class ColumnMappingView(LoginRequiredMixin, FormView):
    """View for mapping CSV columns to resource fields."""

    form_class = ColumnMappingForm
    template_name = "importer/column_mapping.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check if we have CSV content in session."""
        if "csv_content" not in request.session:
            return redirect("importer:csv_upload")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Get CSV columns and current mapping for form."""
        kwargs = super().get_form_kwargs()

        # Get CSV content from session
        csv_content = self.request.session.get("csv_content")

        # Get import job
        import_job_id = self.request.session.get("import_job_id")
        import_job = get_object_or_404(
            ImportJob, id=import_job_id, created_by=self.request.user
        )

        # Process CSV to get columns
        processor = CSVProcessor(import_job)
        csv_columns = processor.validate_csv_structure(csv_content)

        kwargs["csv_columns"] = csv_columns
        kwargs["current_mapping"] = import_job.column_mapping_dict

        return kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Get import job
        import_job_id = self.request.session.get("import_job_id")
        context["import_job"] = get_object_or_404(
            ImportJob, id=import_job_id, created_by=self.request.user
        )

        return context

    def form_valid(self, form):
        """Save column mapping and redirect to preview."""
        # Get import job
        import_job_id = self.request.session.get("import_job_id")
        import_job = get_object_or_404(
            ImportJob, id=import_job_id, created_by=self.request.user
        )

        # Save column mapping
        column_mapping = form.get_column_mapping()
        import_job.column_mapping_dict = column_mapping
        import_job.save()

        return redirect("importer:import_preview", pk=import_job.id)


class ImportPreviewView(LoginRequiredMixin, FormView):
    """View for previewing import before processing."""

    form_class = ImportPreviewForm
    template_name = "importer/import_preview.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check if we have CSV content in session."""
        if "csv_content" not in request.session:
            return redirect("importer:csv_upload")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add preview data to context."""
        context = super().get_context_data(**kwargs)

        # Get import job
        import_job = get_object_or_404(
            ImportJob, id=self.kwargs["pk"], created_by=self.request.user
        )
        context["import_job"] = import_job

        # Get CSV content from session
        csv_content = self.request.session.get("csv_content")

        # Generate preview data
        processor = CSVProcessor(import_job)
        preview_data = self._generate_preview(csv_content, processor)
        context["preview_data"] = preview_data

        return context

    def _generate_preview(
        self, csv_content: str, processor: CSVProcessor
    ) -> Dict[str, Any]:
        """Generate preview data for the first few rows."""
        try:
            csv_file = StringIO(csv_content)
            reader = csv.reader(csv_file)

            # Skip header if configured
            if processor.import_job.skip_header:
                next(reader)

            preview_rows = []
            sample_count = 0

            for row_num, row in enumerate(reader):
                if sample_count >= 5:  # Show first 5 rows
                    break

                try:
                    # Map row data to resource fields
                    resource_data = processor._map_row_to_resource(row)

                    # Validate resource data
                    processor._validate_resource_data(resource_data, row_num + 1)

                    preview_rows.append(
                        {
                            "row_number": row_num + 1,
                            "data": resource_data,
                            "status": "valid",
                            "error": None,
                        }
                    )

                except Exception as e:
                    preview_rows.append(
                        {
                            "row_number": row_num + 1,
                            "data": processor._map_row_to_resource(row),
                            "status": "invalid",
                            "error": str(e),
                        }
                    )

                sample_count += 1

            return {"rows": preview_rows, "total_previewed": len(preview_rows)}

        except Exception as e:
            return {"rows": [], "total_previewed": 0, "error": str(e)}

    def form_valid(self, form):
        """Process the import."""
        # Get import job
        import_job = get_object_or_404(
            ImportJob, id=self.kwargs["pk"], created_by=self.request.user
        )

        # Get CSV content from session
        csv_content = self.request.session.get("csv_content")

        # Process the import
        return self._process_import(import_job, csv_content)

    def _process_import(self, import_job: ImportJob, csv_content: str) -> HttpResponse:
        """Process the CSV import."""
        try:
            # Update import job status
            import_job.status = "processing"
            import_job.started_at = timezone.now()
            import_job.save()

            # Process CSV
            processor = CSVProcessor(import_job)
            results = processor.process_csv(csv_content)

            # Update import job with results
            import_job.total_rows = results["total_rows"]
            import_job.valid_rows = results["valid_rows"]
            import_job.invalid_rows = results["invalid_rows"]
            import_job.resources_created = results["resources_created"]
            import_job.status = "completed"
            import_job.completed_at = timezone.now()
            import_job.save()

            # Clear session data
            self.request.session.pop("csv_content", None)
            self.request.session.pop("import_job_id", None)

            return redirect("importer:import_job_detail", pk=import_job.id)

        except Exception as e:
            # Update import job status to failed
            import_job.status = "failed"
            import_job.completed_at = timezone.now()
            import_job.save()

            # Re-raise the exception
            raise e


class ExportView(LoginRequiredMixin, FormView):
    """View for exporting resources to CSV."""

    form_class = ExportForm
    template_name = "importer/export.html"

    def form_valid(self, form):
        """Generate and return CSV file."""
        # Get filtered queryset
        queryset = form.get_queryset()

        # Get export configuration
        include_header = form.cleaned_data.get("include_header", True)
        fields_to_export = form.cleaned_data.get("fields_to_export", [])

        # Generate CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="resources_export.csv"'

        # Create CSV writer
        writer = csv.writer(response)

        # Write header if requested
        if include_header:
            writer.writerow(fields_to_export)

        # Write data rows
        for resource in queryset:
            row = []
            for field in fields_to_export:
                value = getattr(resource, field, "")

                # Handle special cases
                if field == "category" and resource.category:
                    value = resource.category.name
                elif (
                    field in ["last_verified_at", "created_at", "updated_at"] and value
                ):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")

                row.append(str(value) if value is not None else "")

            writer.writerow(row)

        return response


@login_required
@require_http_methods(["POST"])
def cancel_import(request: HttpRequest, pk: int) -> HttpResponse:
    """Cancel an import job."""
    import_job = get_object_or_404(
        ImportJob, id=pk, created_by=request.user, status="pending"
    )

    # Clear session data
    request.session.pop("csv_content", None)
    request.session.pop("import_job_id", None)

    # Delete the import job
    import_job.delete()

    return redirect("importer:import_job_list")


@login_required
def download_error_report(request: HttpRequest, pk: int) -> HttpResponse:
    """Download error report for an import job."""
    import_job = get_object_or_404(ImportJob, id=pk, created_by=request.user)

    # Get all errors
    errors = import_job.errors.all()

    # Generate CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="import_errors_{pk}.csv"'

    # Create CSV writer
    writer = csv.writer(response)

    # Write header
    writer.writerow(
        ["Row Number", "Error Type", "Field Name", "Error Message", "Row Data"]
    )

    # Write error data
    for error in errors:
        row_data = json.dumps(error.row_data_dict) if error.row_data else ""
        writer.writerow(
            [
                error.row_number,
                error.get_error_type_display(),
                error.field_name,
                error.error_message,
                row_data,
            ]
        )

    return response
