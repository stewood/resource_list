"""
Management command to test FTS5 search functionality.
"""

from django.core.management.base import BaseCommand

from directory.models import Resource


class Command(BaseCommand):
    """Test FTS5 search functionality."""

    help = "Test FTS5 search functionality with sample queries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--query", type=str, default="shelter", help="Search query to test"
        )

    def handle(self, *args, **options):
        """Execute the command."""
        query = options["query"]

        self.stdout.write(f'Testing search for: "{query}"')

        # Test FTS5 search
        self.stdout.write("\n1. Testing FTS5 search:")
        try:
            fts_results = Resource.objects.search_fts(query)
            self.stdout.write(f"   FTS5 results: {fts_results.count()}")
            for resource in fts_results[:3]:
                self.stdout.write(
                    f"   - {resource.name} ({resource.city}, {resource.state})"
                )
        except Exception as e:
            self.stdout.write(f"   FTS5 search failed: {e}")

        # Test combined search
        self.stdout.write("\n2. Testing combined search:")
        try:
            combined_results = Resource.objects.search_combined(query)
            self.stdout.write(f"   Combined results: {combined_results.count()}")
            for resource in combined_results[:3]:
                self.stdout.write(
                    f"   - {resource.name} ({resource.city}, {resource.state})"
                )
        except Exception as e:
            self.stdout.write(f"   Combined search failed: {e}")

        # Test basic search (fallback)
        self.stdout.write("\n3. Testing basic search (fallback):")
        try:
            basic_results = (
                Resource.objects.filter(name__icontains=query)
                | Resource.objects.filter(description__icontains=query)
                | Resource.objects.filter(city__icontains=query)
                | Resource.objects.filter(state__icontains=query)
            )
            self.stdout.write(f"   Basic results: {basic_results.count()}")
            for resource in basic_results[:3]:
                self.stdout.write(
                    f"   - {resource.name} ({resource.city}, {resource.state})"
                )
        except Exception as e:
            self.stdout.write(f"   Basic search failed: {e}")

        self.stdout.write(
            self.style.SUCCESS("\nSearch testing completed successfully!")
        )
