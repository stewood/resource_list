"""Management command to create test boundary data for development.

This command creates test CoverageArea records with proper geometry for
Kentucky counties and states. This allows testing the service area
functionality without requiring TIGER/Line data import.

Usage:
    python manage.py create_test_boundaries

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.gis.geos import Point, Polygon, MultiPolygon

from directory.models import CoverageArea


class Command(BaseCommand):
    """Create test boundary data for development."""

    help = "Create test boundary data for Kentucky counties and states"

    def handle(self, *args, **options):
        """Execute the command."""
        # Check if GIS is enabled
        from django.conf import settings

        if not getattr(settings, "GIS_ENABLED", False):
            self.stdout.write(
                self.style.WARNING(
                    "GIS is not enabled. This command requires GIS functionality. "
                    "Set GIS_ENABLED=1 in your environment to enable."
                )
            )
            return

        # Get or create default user
        default_user, created = User.objects.get_or_create(
            username="test_boundary_creator",
            defaults={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "Boundary",
            },
        )

        if created:
            self.stdout.write("Created default user for test boundaries")

        # Clear existing test data
        deleted_count = CoverageArea.objects.filter(ext_ids__test_data=True).delete()[0]

        if deleted_count > 0:
            self.stdout.write(f"Deleted {deleted_count} existing test boundaries")

        # Create test data
        created_count = self._create_test_boundaries(default_user)

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} test boundaries")
        )

    def _create_test_boundaries(self, user):
        """Create test boundary data.

        Args:
            user: User for creating records

        Returns:
            Number of boundaries created
        """
        created_count = 0

        # Kentucky state boundary (simplified rectangle)
        kentucky_geom = self._create_kentucky_boundary()

        with transaction.atomic():
            coverage_area = CoverageArea.objects.create(
                kind="STATE",
                name="Kentucky",
                geom=kentucky_geom,
                center=kentucky_geom.centroid,
                ext_ids={
                    "state_fips": "21",
                    "state_name": "Kentucky",
                    "state_abbr": "KY",
                    "test_data": True,
                },
                created_by=user,
                updated_by=user,
            )
            created_count += 1
            self.stdout.write("Created Kentucky state boundary")

        # Kentucky counties (simplified polygons)
        counties = [
            ("Laurel County", "125", 37.1283, -84.0836),
            ("Whitley County", "235", 36.7584, -84.1624),
            ("Knox County", "121", 36.8906, -83.8541),
            ("Bell County", "013", 36.7307, -83.6741),
            ("Clay County", "051", 37.1617, -83.7149),
            ("Harlan County", "095", 36.8567, -83.3219),
            ("Leslie County", "131", 37.0942, -83.3819),
            ("Perry County", "193", 37.2442, -83.2219),
            ("Letcher County", "133", 37.1219, -82.8541),
            ("Pike County", "195", 37.4641, -82.3941),
        ]

        for county_name, county_fips, lat, lon in counties:
            county_geom = self._create_county_boundary(lat, lon)

            with transaction.atomic():
                coverage_area = CoverageArea.objects.create(
                    kind="COUNTY",
                    name=county_name,
                    geom=county_geom,
                    center=county_geom.centroid,
                    ext_ids={
                        "state_fips": "21",
                        "county_fips": county_fips,
                        "state_name": "Kentucky",
                        "county_name": county_name,
                        "test_data": True,
                    },
                    created_by=user,
                    updated_by=user,
                )
                created_count += 1
                self.stdout.write(f"Created {county_name} boundary")

        return created_count

    def _create_kentucky_boundary(self):
        """Create a simplified Kentucky state boundary.

        Returns:
            MultiPolygon geometry for Kentucky
        """
        # Simplified Kentucky boundary (rough rectangle)
        # Kentucky roughly spans from 36.5°N to 39.1°N and 81.9°W to 89.6°W
        coords = [
            (-89.6, 36.5),  # Southwest
            (-81.9, 36.5),  # Southeast
            (-81.9, 39.1),  # Northeast
            (-89.6, 39.1),  # Northwest
            (-89.6, 36.5),  # Close the polygon
        ]

        polygon = Polygon(coords, srid=4326)
        return MultiPolygon([polygon], srid=4326)

    def _create_county_boundary(self, center_lat, center_lon):
        """Create a simplified county boundary.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude

        Returns:
            MultiPolygon geometry for the county
        """
        # Create a rough square around the center point
        # Each county is roughly 0.5 degrees across
        half_size = 0.25

        coords = [
            (center_lon - half_size, center_lat - half_size),  # Southwest
            (center_lon + half_size, center_lat - half_size),  # Southeast
            (center_lon + half_size, center_lat + half_size),  # Northeast
            (center_lon - half_size, center_lat + half_size),  # Northwest
            (center_lon - half_size, center_lat - half_size),  # Close the polygon
        ]

        polygon = Polygon(coords, srid=4326)
        return MultiPolygon([polygon], srid=4326)
