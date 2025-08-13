"""
Management command to set up initial service types.
"""

from django.core.management.base import BaseCommand
from directory.models import ServiceType


class Command(BaseCommand):
    """Set up initial service types based on resources.csv analysis."""

    help = "Create initial service types for the resource directory"

    def handle(self, *args, **options):
        """Create the initial service types."""
        service_types = [
            {
                "name": "Hotline",
                "description": "24/7 crisis and information hotlines",
            },
            {
                "name": "Counseling",
                "description": "Mental health and addiction counseling services",
            },
            {
                "name": "Housing",
                "description": "Housing assistance and shelter services",
            },
            {
                "name": "Food Assistance",
                "description": "Food banks, meal programs, and nutrition assistance",
            },
            {
                "name": "Legal Services",
                "description": "Legal aid and advocacy services",
            },
            {
                "name": "Healthcare",
                "description": "Medical and healthcare services",
            },
            {
                "name": "Employment",
                "description": "Job training and employment services",
            },
            {
                "name": "Transportation",
                "description": "Transportation assistance and services",
            },
            {
                "name": "Education",
                "description": "Educational programs and support",
            },
            {
                "name": "Child Care",
                "description": "Child care and family support services",
            },
            {
                "name": "Veterans Services",
                "description": "Services specifically for veterans",
            },
            {
                "name": "Domestic Violence",
                "description": "Domestic violence prevention and support",
            },
            {
                "name": "Substance Abuse",
                "description": "Addiction treatment and recovery services",
            },
            {
                "name": "Emergency Services",
                "description": "Emergency and crisis intervention services",
            },
            {
                "name": "Financial Assistance",
                "description": "Financial aid and benefit programs",
            },
        ]

        created_count = 0
        for service_type_data in service_types:
            service_type, created = ServiceType.objects.get_or_create(
                name=service_type_data["name"],
                defaults={"description": service_type_data["description"]},
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created service type: "{service_type.name}"'
                    )
                )
            else:
                self.stdout.write(
                    f'Service type already exists: "{service_type.name}"'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} new service types"
            )
        )
