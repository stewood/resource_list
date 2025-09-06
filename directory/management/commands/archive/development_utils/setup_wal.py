"""
Management command to set up SQLite WAL mode and configure the database.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Set up SQLite WAL mode and configure database settings."""

    help = "Configure SQLite database with WAL mode and optimal settings"

    def handle(self, *args, **options):
        """Execute the command."""
        with connection.cursor() as cursor:
            # Enable WAL mode
            cursor.execute("PRAGMA journal_mode=WAL;")
            result = cursor.fetchone()
            journal_mode = result[0] if result else "unknown"
            self.stdout.write(f"Journal mode: {journal_mode}")

            # Set synchronous mode to NORMAL for better performance
            cursor.execute("PRAGMA synchronous=NORMAL;")
            result = cursor.fetchone()
            synchronous = result[0] if result else "unknown"
            self.stdout.write(f"Synchronous mode: {synchronous}")

            # Set busy timeout to 20 seconds
            cursor.execute("PRAGMA busy_timeout=20000;")
            result = cursor.fetchone()
            busy_timeout = result[0] if result else "unknown"
            self.stdout.write(f"Busy timeout: {busy_timeout}ms")

            # Set cache size to 10000 pages (about 40MB)
            cursor.execute("PRAGMA cache_size=10000;")
            result = cursor.fetchone()
            cache_size = result[0] if result else "unknown"
            self.stdout.write(f"Cache size: {cache_size} pages")

            # Set temp store to memory
            cursor.execute("PRAGMA temp_store=MEMORY;")
            result = cursor.fetchone()
            temp_store = result[0] if result else "unknown"
            self.stdout.write(f"Temp store: {temp_store}")

            # Set mmap size to 268435456 bytes (256MB)
            cursor.execute("PRAGMA mmap_size=268435456;")
            result = cursor.fetchone()
            mmap_size = result[0] if result else "unknown"
            self.stdout.write(f"MMAP size: {mmap_size} bytes")

        self.stdout.write(
            self.style.SUCCESS("Successfully configured SQLite database with WAL mode")
        )
