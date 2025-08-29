"""
Management command for managing the geocoding cache.

This command provides utilities for managing the GeocodingCache model,
including cleanup operations, statistics, and cache management.

Usage:
    python manage.py manage_geocoding_cache --cleanup-expired
    python manage.py manage_geocoding_cache --cleanup-old --days=7
    python manage.py manage_geocoding_cache --stats
    python manage.py manage_geocoding_cache --clear-all

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from directory.models import GeocodingCache


class Command(BaseCommand):
    """Management command for geocoding cache operations."""

    help = "Manage the geocoding cache (cleanup, statistics, etc.)"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--cleanup-expired",
            action="store_true",
            help="Remove expired cache entries",
        )
        parser.add_argument(
            "--cleanup-old",
            action="store_true",
            help="Remove old cache entries regardless of expiration",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days old for cleanup (default: 7)",
        )
        parser.add_argument(
            "--stats", action="store_true", help="Show cache statistics"
        )
        parser.add_argument(
            "--clear-all",
            action="store_true",
            help="Clear all cache entries (use with caution)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        if not any(
            [
                options["cleanup_expired"],
                options["cleanup_old"],
                options["stats"],
                options["clear_all"],
            ]
        ):
            self.stdout.write(
                self.style.ERROR("Please specify an action. Use --help for options.")
            )
            return

        # Show statistics
        if options["stats"]:
            self._show_stats()

        # Cleanup expired entries
        if options["cleanup_expired"]:
            self._cleanup_expired(options["dry_run"])

        # Cleanup old entries
        if options["cleanup_old"]:
            self._cleanup_old(options["days"], options["dry_run"])

        # Clear all entries
        if options["clear_all"]:
            self._clear_all(options["dry_run"])

    def _show_stats(self):
        """Show cache statistics."""
        self.stdout.write(self.style.SUCCESS("=== Geocoding Cache Statistics ==="))

        stats = GeocodingCache.get_cache_stats()

        self.stdout.write(f"Total entries: {stats['total_entries']}")
        self.stdout.write(f"Active entries: {stats['active_entries']}")
        self.stdout.write(f"Expired entries: {stats['expired_entries']}")
        self.stdout.write(f"Average hit count: {stats['average_hit_count']}")

        if stats["provider_distribution"]:
            self.stdout.write("\nProvider distribution:")
            for provider_stat in stats["provider_distribution"]:
                self.stdout.write(
                    f"  {provider_stat['provider']}: {provider_stat['count']} entries"
                )

        # Show some recent entries
        recent_entries = GeocodingCache.objects.order_by("-last_accessed")[:5]
        if recent_entries:
            self.stdout.write("\nMost recently accessed entries:")
            for entry in recent_entries:
                self.stdout.write(
                    f"  {entry.query[:50]}... -> ({entry.latitude}, {entry.longitude}) "
                    f"[{entry.hit_count} hits, {entry.provider}]"
                )

    def _cleanup_expired(self, dry_run: bool):
        """Cleanup expired cache entries."""
        if dry_run:
            expired_count = GeocodingCache.objects.filter(
                expires_at__lte=timezone.now()
            ).count()
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would remove {expired_count} expired entries"
                )
            )
        else:
            expired_count = GeocodingCache.cleanup_expired()
            self.stdout.write(
                self.style.SUCCESS(f"Removed {expired_count} expired cache entries")
            )

    def _cleanup_old(self, days: int, dry_run: bool):
        """Cleanup old cache entries."""
        if dry_run:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            old_count = GeocodingCache.objects.filter(
                created_at__lte=cutoff_date
            ).count()
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would remove {old_count} entries older than {days} days"
                )
            )
        else:
            old_count = GeocodingCache.cleanup_old_entries(days)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Removed {old_count} cache entries older than {days} days"
                )
            )

    def _clear_all(self, dry_run: bool):
        """Clear all cache entries."""
        if dry_run:
            total_count = GeocodingCache.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would remove all {total_count} cache entries"
                )
            )
        else:
            # Confirm with user
            total_count = GeocodingCache.objects.count()
            confirm = input(
                f"Are you sure you want to delete all {total_count} cache entries? (yes/no): "
            )

            if confirm.lower() == "yes":
                deleted_count, _ = GeocodingCache.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Removed all {deleted_count} cache entries")
                )
            else:
                self.stdout.write(self.style.WARNING("Operation cancelled"))
