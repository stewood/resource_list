"""
URL configuration for importer app.
"""

from django.urls import path

from . import views

app_name = "importer"

urlpatterns = [
    # Import job management
    path("jobs/", views.ImportJobListView.as_view(), name="import_job_list"),
    path(
        "jobs/<int:pk>/", views.ImportJobDetailView.as_view(), name="import_job_detail"
    ),
    # CSV import workflow
    path("upload/", views.CSVUploadView.as_view(), name="csv_upload"),
    path("mapping/<int:pk>/", views.ColumnMappingView.as_view(), name="column_mapping"),
    path("preview/<int:pk>/", views.ImportPreviewView.as_view(), name="import_preview"),
    # Import actions
    path("jobs/<int:pk>/cancel/", views.cancel_import, name="cancel_import"),
    path(
        "jobs/<int:pk>/errors/",
        views.download_error_report,
        name="download_error_report",
    ),
    # Export
    path("export/", views.ExportView.as_view(), name="export"),
]
