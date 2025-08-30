"""
Search Analytics Models

This module contains models for tracking location search usage patterns
to improve search suggestions and user experience.

Models:
    - LocationSearchLog: Tracks individual location searches
    - SearchAnalytics: Aggregated search statistics
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class LocationSearchLog(models.Model):
    """Model to track individual location searches for analytics.

    This model captures detailed information about each location search
    to help understand user behavior and improve search functionality.
    """

    # Search details
    address = models.CharField(max_length=255, help_text="Original search address")
    lat = models.FloatField(null=True, blank=True, help_text="Geocoded latitude")
    lon = models.FloatField(null=True, blank=True, help_text="Geocoded longitude")
    radius_miles = models.FloatField(default=10.0, help_text="Search radius in miles")

    # Search results
    results_count = models.IntegerField(
        default=0, help_text="Number of results returned"
    )
    search_duration_ms = models.IntegerField(
        default=0, help_text="Search execution time in milliseconds"
    )

    # Geocoding info
    geocoding_success = models.BooleanField(
        default=True, help_text="Whether geocoding was successful"
    )
    geocoding_provider = models.CharField(
        max_length=50, default="nominatim", help_text="Geocoding service used"
    )

    # User info
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the search",
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="IP address of the user"
    )
    user_agent = models.TextField(blank=True, help_text="User agent string")

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When the search was performed"
    )

    class Meta:
        db_table = "location_search_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["address"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["geocoding_success"]),
            models.Index(fields=["radius_miles"]),
        ]

    def __str__(self):
        return f"Search: {self.address} ({self.results_count} results) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def log_search(
        cls,
        address,
        lat=None,
        lon=None,
        radius_miles=10.0,
        results_count=0,
        search_duration_ms=0,
        geocoding_success=True,
        user=None,
        ip_address=None,
        user_agent="",
    ):
        """Log a location search for analytics.

        Args:
            address: The search address
            lat: Geocoded latitude
            lon: Geocoded longitude
            radius_miles: Search radius
            results_count: Number of results returned
            search_duration_ms: Search execution time
            geocoding_success: Whether geocoding succeeded
            user: User who performed the search
            ip_address: User's IP address
            user_agent: User agent string
        """
        return cls.objects.create(
            address=address,
            lat=lat,
            lon=lon,
            radius_miles=radius_miles,
            results_count=results_count,
            search_duration_ms=search_duration_ms,
            geocoding_success=geocoding_success,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def get_popular_locations(cls, days=30, limit=10):
        """Get most popular search locations.

        Args:
            days: Number of days to look back
            limit: Maximum number of locations to return

        Returns:
            List of (address, count) tuples
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)

        return (
            cls.objects.filter(created_at__gte=cutoff_date, geocoding_success=True)
            .values("address")
            .annotate(count=models.Count("id"))
            .order_by("-count")[:limit]
        )

    @classmethod
    def get_radius_usage(cls, days=30):
        """Get search radius usage statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with radius usage statistics
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)

        queryset = cls.objects.filter(created_at__gte=cutoff_date)

        return {
            "total_searches": queryset.count(),
            "avg_radius": queryset.aggregate(avg=models.Avg("radius_miles"))["avg"],
            "radius_distribution": list(
                queryset.values("radius_miles")
                .annotate(count=models.Count("id"))
                .order_by("radius_miles")
            ),
        }

    @classmethod
    def get_geocoding_stats(cls, days=30):
        """Get geocoding success rate statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with geocoding statistics
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)

        queryset = cls.objects.filter(created_at__gte=cutoff_date)
        total = queryset.count()
        successful = queryset.filter(geocoding_success=True).count()

        return {
            "total_searches": total,
            "successful_geocoding": successful,
            "failed_geocoding": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }


class SearchAnalytics(models.Model):
    """Aggregated search analytics for performance optimization.

    This model stores pre-calculated analytics data to avoid
    expensive queries on the search log table.
    """

    # Analytics period
    date = models.DateField(help_text="Date for this analytics record")
    period_type = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="daily",
        help_text="Type of analytics period",
    )

    # Search metrics
    total_searches = models.IntegerField(
        default=0, help_text="Total number of searches"
    )
    unique_addresses = models.IntegerField(
        default=0, help_text="Number of unique addresses searched"
    )
    avg_results_per_search = models.FloatField(
        default=0.0, help_text="Average results per search"
    )
    avg_search_duration_ms = models.FloatField(
        default=0.0, help_text="Average search duration"
    )

    # Geocoding metrics
    geocoding_success_rate = models.FloatField(
        default=0.0, help_text="Geocoding success rate percentage"
    )

    # Popular data
    top_locations = models.JSONField(default=list, help_text="Top searched locations")
    radius_distribution = models.JSONField(
        default=dict, help_text="Search radius usage distribution"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "search_analytics"
        unique_together = ["date", "period_type"]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date", "period_type"]),
        ]

    def __str__(self):
        return f"Analytics: {self.date} ({self.period_type}) - {self.total_searches} searches"

    @classmethod
    def generate_daily_analytics(cls, date=None):
        """Generate daily analytics for a specific date.

        Args:
            date: Date to generate analytics for (defaults to today)
        """
        from django.utils import timezone
        from datetime import date as date_type

        if date is None:
            date = timezone.now().date()

        # Get search logs for the date
        logs = LocationSearchLog.objects.filter(created_at__date=date)

        total_searches = logs.count()
        if total_searches == 0:
            return None

        # Calculate metrics
        unique_addresses = logs.values("address").distinct().count()
        avg_results = logs.aggregate(avg=models.Avg("results_count"))["avg"] or 0.0
        avg_duration = (
            logs.aggregate(avg=models.Avg("search_duration_ms"))["avg"] or 0.0
        )

        # Geocoding success rate
        successful_geocoding = logs.filter(geocoding_success=True).count()
        geocoding_success_rate = (
            (successful_geocoding / total_searches * 100) if total_searches > 0 else 0
        )

        # Top locations
        top_locations = list(
            logs.values("address")
            .annotate(count=models.Count("id"))
            .order_by("-count")[:10]
        )

        # Radius distribution
        radius_distribution = dict(
            logs.values("radius_miles")
            .annotate(count=models.Count("id"))
            .order_by("radius_miles")
        )

        # Create or update analytics record
        analytics, created = cls.objects.update_or_create(
            date=date,
            period_type="daily",
            defaults={
                "total_searches": total_searches,
                "unique_addresses": unique_addresses,
                "avg_results_per_search": avg_results,
                "avg_search_duration_ms": avg_duration,
                "geocoding_success_rate": geocoding_success_rate,
                "top_locations": top_locations,
                "radius_distribution": radius_distribution,
            },
        )

        return analytics
