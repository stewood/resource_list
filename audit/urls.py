"""
URL configuration for audit app.
"""

from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="audit_log_list"),
    path("dashboard/", views.audit_dashboard, name="audit_dashboard"),
    path("export/", views.export_audit_logs, name="export_audit_logs"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="audit_log_detail"),
]
