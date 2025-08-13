"""
Views for the audit application.
"""

import csv
from datetime import datetime, timedelta
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView

from directory.models import AuditLog
from directory.permissions import require_admin


class AuditLogListView(LoginRequiredMixin, ListView):
    """List view for audit logs with filtering and search."""

    model = AuditLog
    template_name = "audit/audit_log_list.html"
    context_object_name = "audit_logs"
    paginate_by = 50

    def get_queryset(self):
        """Filter queryset based on search and filter parameters."""
        queryset = AuditLog.objects.all()

        # Search
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(action__icontains=search_query)
                | Q(target_table__icontains=search_query)
                | Q(target_id__icontains=search_query)
                | Q(actor__username__icontains=search_query)
                | Q(actor__first_name__icontains=search_query)
                | Q(actor__last_name__icontains=search_query)
                | Q(metadata_json__icontains=search_query)
            )

        # Filters
        action_filter = self.request.GET.get("action", "")
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        table_filter = self.request.GET.get("table", "")
        if table_filter:
            queryset = queryset.filter(target_table=table_filter)

        actor_filter = self.request.GET.get("actor", "")
        if actor_filter:
            queryset = queryset.filter(actor_id=actor_filter)

        # Date range filter
        date_from = self.request.GET.get("date_from", "")
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                queryset = queryset.filter(created_at__gte=date_from_obj)
            except ValueError:
                pass

        date_to = self.request.GET.get("date_to", "")
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                ) + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=date_to_obj)
            except ValueError:
                pass

        # Time range filter (last 24h, 7d, 30d)
        time_range = self.request.GET.get("time_range", "")
        if time_range:
            now = timezone.now()
            if time_range == "24h":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=1))
            elif time_range == "7d":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
            elif time_range == "30d":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=30))

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Get unique values for filter dropdowns
        context["actions"] = (
            AuditLog.objects.values_list("action", flat=True)
            .distinct()
            .order_by("action")
        )
        context["tables"] = (
            AuditLog.objects.values_list("target_table", flat=True)
            .distinct()
            .order_by("target_table")
        )
        context["actors"] = (
            AuditLog.objects.select_related("actor")
            .values(
                "actor__id", "actor__username", "actor__first_name", "actor__last_name"
            )
            .distinct()
            .order_by("actor__username")
        )

        # Add current filters for form persistence
        context["current_filters"] = {
            "q": self.request.GET.get("q", ""),
            "action": self.request.GET.get("action", ""),
            "table": self.request.GET.get("table", ""),
            "actor": self.request.GET.get("actor", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "time_range": self.request.GET.get("time_range", ""),
        }

        # Add summary statistics
        total_logs = AuditLog.objects.count()
        today_logs = AuditLog.objects.filter(
            created_at__gte=timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        ).count()

        context["summary_stats"] = {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "filtered_count": context["audit_logs"].count(),
        }

        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single audit log entry."""

    model = AuditLog
    template_name = "audit/audit_log_detail.html"
    context_object_name = "audit_log"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Try to get the related object if it exists
        try:
            if self.object.target_table == "resource":
                from directory.models import Resource

                related_object = Resource.objects.filter(
                    id=self.object.target_id
                ).first()
                context["related_object"] = related_object
        except Exception:
            context["related_object"] = None

        return context


@login_required
@require_admin
def export_audit_logs(request: HttpRequest) -> HttpResponse:
    """Export audit logs to CSV."""
    # Get filtered queryset (same as list view)
    queryset = AuditLog.objects.all()

    # Apply filters
    search_query = request.GET.get("q", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(action__icontains=search_query)
            | Q(target_table__icontains=search_query)
            | Q(target_id__icontains=search_query)
            | Q(actor__username__icontains=search_query)
        )

    action_filter = request.GET.get("action", "")
    if action_filter:
        queryset = queryset.filter(action=action_filter)

    table_filter = request.GET.get("table", "")
    if table_filter:
        queryset = queryset.filter(target_table=table_filter)

    actor_filter = request.GET.get("actor", "")
    if actor_filter:
        queryset = queryset.filter(actor_id=actor_filter)

    # Date range filter
    date_from = request.GET.get("date_from", "")
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            queryset = queryset.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass

    date_to = request.GET.get("date_to", "")
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=date_to_obj)
        except ValueError:
            pass

    # Time range filter
    time_range = request.GET.get("time_range", "")
    if time_range:
        now = timezone.now()
        if time_range == "24h":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=1))
        elif time_range == "7d":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        elif time_range == "30d":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=30))

    # Order by created_at descending
    queryset = queryset.order_by("-created_at")

    # Generate CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )

    # Create CSV writer
    writer = csv.writer(response)

    # Write header
    writer.writerow(
        [
            "Timestamp",
            "Actor",
            "Action",
            "Target Table",
            "Target ID",
            "Metadata",
            "IP Address",
        ]
    )

    # Write data rows
    for audit_log in queryset:
        writer.writerow(
            [
                audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                audit_log.actor.get_full_name() or audit_log.actor.username,
                audit_log.action,
                audit_log.target_table,
                audit_log.target_id,
                audit_log.metadata_json,
                "",  # IP address would need to be captured in the model
            ]
        )

    return response


@login_required
@require_admin
def audit_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view for audit statistics."""
    # Get date range for filtering
    days = int(request.GET.get("days", 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Get audit logs in date range
    audit_logs = AuditLog.objects.filter(created_at__range=[start_date, end_date])

    # Calculate statistics
    total_actions = audit_logs.count()
    actions_by_type = (
        audit_logs.values("action").annotate(count=Count("id")).order_by("-count")
    )

    actions_by_user = (
        audit_logs.values("actor__username")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    actions_by_table = (
        audit_logs.values("target_table").annotate(count=Count("id")).order_by("-count")
    )

    # Daily activity
    daily_activity = (
        audit_logs.extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    context = {
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
        "total_actions": total_actions,
        "actions_by_type": actions_by_type,
        "actions_by_user": actions_by_user,
        "actions_by_table": actions_by_table,
        "daily_activity": daily_activity,
    }

    return render(request, "audit/audit_dashboard.html", context)
