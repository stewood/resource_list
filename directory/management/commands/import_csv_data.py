"""
Management command to import CSV data.
"""

import csv
import os
from typing import Any, Dict

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from directory.models import Resource, TaxonomyCategory, ServiceType


class Command(BaseCommand):
    """Import CSV data."""

    help = "Import resources from CSV file"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the CSV file to import",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing resources before importing",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        csv_file = options["csv_file"]
        clear_existing = options["clear"]

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_file}"))
            return

        # Clear existing resources if requested
        if clear_existing:
            self.stdout.write("Clearing existing resources...")
            Resource.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing resources cleared"))

        # Create default categories and service types
        self.stdout.write("Setting up categories and service types...")

        # Create default categories
        categories = {
            "Hotlines": "Emergency and crisis hotlines",
            "Food Assistance": "Food banks, pantries, and meal programs",
            "Housing": "Shelters, housing assistance, and transitional housing",
            "Mental Health": "Mental health and substance abuse services",
            "Medical": "Healthcare and medical services",
            "Legal": "Legal assistance and advocacy",
            "Education": "Educational programs and services",
            "Transportation": "Transportation assistance",
            "Utilities": "Utility assistance programs",
            "Child Care": "Child care and family services",
            "Veterans": "Veterans services and support",
            "Other": "Other services and resources",
        }

        category_objects = {}
        for name, description in categories.items():
            category, created = TaxonomyCategory.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            category_objects[name] = category
            if created:
                self.stdout.write(f"Created category: {name}")

        # Create default service types
        service_types = {
            "Hotlines": "Crisis and emergency hotlines",
            "Food Pantry": "Food assistance and meal programs",
            "Emergency Shelter": "Emergency and temporary housing",
            "Transitional Housing": "Long-term transitional housing",
            "Mental Health Counseling": "Mental health and counseling services",
            "Substance Abuse Treatment": "Addiction recovery and treatment",
            "Medical Care": "Healthcare and medical services",
            "Legal Aid": "Legal assistance and representation",
            "Job Training": "Employment and job training services",
            "Transportation": "Transportation assistance",
            "Utility Assistance": "Help with utility bills",
            "Child Care": "Child care and family support",
            "Veterans Services": "Services for veterans",
            "Domestic Violence": "Domestic violence support and shelter",
            "Education": "Educational programs and GED services",
        }

        service_type_objects = {}
        for name, description in service_types.items():
            service_type, created = ServiceType.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            service_type_objects[name] = service_type
            if created:
                self.stdout.write(f"Created service type: {name}")

        # Get or create a default user for importing
        default_user, created = User.objects.get_or_create(
            username="csv_importer",
            defaults={
                "email": "importer@example.com",
                "first_name": "CSV",
                "last_name": "Importer",
            },
        )
        if created:
            self.stdout.write("Created default user for importing")

        # Import CSV data
        self.stdout.write(f"Importing data from {csv_file}...")

        imported_count = 0
        error_count = 0
        skipped_count = 0

        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 to account for header
                try:
                    # Extract data from CSV
                    name = row.get("Organization", "").strip()
                    address = row.get("Address", "").strip()
                    phone = row.get("Phone", "").strip()
                    url = row.get("URL", "").strip()
                    description = row.get("Description", "").strip()

                    if not name:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Row {row_num}: Skipping - no organization name"
                            )
                        )
                        error_count += 1
                        continue

                    # Check if resource already exists
                    if Resource.objects.filter(name=name).exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f"Row {row_num}: Skipping - resource already exists: {name}"
                            )
                        )
                        skipped_count += 1
                        continue

                    # Determine category based on description or name
                    category = self._determine_category(
                        name, description, category_objects
                    )

                    # Determine service types based on description or name
                    service_types_list = self._determine_service_types(
                        name, description, service_type_objects
                    )

                    # Parse address into components
                    address_parts = self._parse_address(address)

                    # Create resource
                    resource = Resource.objects.create(
                        name=name,
                        category=category,
                        description=description,
                        phone=phone,
                        website=url,
                        address1=address_parts.get("address1", ""),
                        city=address_parts.get("city", ""),
                        state=address_parts.get("state", ""),
                        county=address_parts.get("county", ""),
                        postal_code=address_parts.get("postal_code", ""),
                        source="CSV Import",
                        status="draft",
                        created_by=default_user,
                        updated_by=default_user,
                    )

                    # Add service types
                    if service_types_list:
                        resource.service_types.set(service_types_list)

                    imported_count += 1

                    if imported_count % 50 == 0:
                        self.stdout.write(f"Imported {imported_count} resources...")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Row {row_num}: Error importing {name}: {str(e)}"
                        )
                    )
                    error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed! Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}"
            )
        )

    def _determine_category(
        self, name: str, description: str, category_objects: Dict
    ) -> TaxonomyCategory:
        """Determine the appropriate category based on name and description."""
        text = f"{name} {description}".lower()

        # Define category keywords
        category_keywords = {
            "Hotlines": ["hotline", "crisis", "emergency", "988", "suicide"],
            "Food Assistance": ["food", "pantry", "meal", "hunger", "nutrition"],
            "Housing": ["shelter", "housing", "homeless", "rent", "apartment"],
            "Mental Health": [
                "mental",
                "counseling",
                "therapy",
                "psychiatric",
                "substance",
                "addiction",
                "recovery",
            ],
            "Medical": ["medical", "health", "hospital", "clinic", "doctor", "nurse"],
            "Legal": ["legal", "attorney", "law", "court", "advocacy"],
            "Education": ["education", "school", "ged", "training", "learning"],
            "Transportation": ["transport", "bus", "ride", "travel"],
            "Utilities": ["utility", "electric", "gas", "water", "bill"],
            "Child Care": ["child", "daycare", "family", "parent", "children"],
            "Veterans": ["veteran", "vfw", "military", "combat"],
        }

        for category_name, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category_objects.get(category_name, category_objects["Other"])

        return category_objects["Other"]

    def _determine_service_types(
        self, name: str, description: str, service_type_objects: Dict
    ) -> list:
        """Determine service types based on name and description."""
        text = f"{name} {description}".lower()
        service_types = []

        # Define service type keywords
        service_keywords = {
            "Hotlines": ["hotline", "crisis", "emergency", "988", "suicide"],
            "Food Pantry": ["food", "pantry", "meal", "hunger"],
            "Emergency Shelter": ["emergency shelter", "homeless shelter"],
            "Transitional Housing": ["transitional", "housing", "apartment"],
            "Mental Health Counseling": ["counseling", "therapy", "mental health"],
            "Substance Abuse Treatment": [
                "substance",
                "addiction",
                "recovery",
                "rehab",
                "detox",
            ],
            "Medical Care": ["medical", "health", "hospital", "clinic"],
            "Legal Aid": ["legal", "attorney", "law"],
            "Job Training": ["job", "employment", "training", "career"],
            "Transportation": ["transport", "bus", "ride"],
            "Utility Assistance": ["utility", "electric", "gas", "water"],
            "Child Care": ["child care", "daycare", "childcare"],
            "Veterans Services": ["veteran", "vfw", "military"],
            "Domestic Violence": ["domestic violence", "battered", "abuse"],
            "Education": ["education", "ged", "school", "learning"],
        }

        for service_name, keywords in service_keywords.items():
            if any(keyword in text for keyword in keywords):
                service_type = service_type_objects.get(service_name)
                if service_type and service_type not in service_types:
                    service_types.append(service_type)

        return service_types

    def _parse_address(self, address: str) -> Dict[str, str]:
        """Parse address string into components."""
        if not address:
            return {}

        # Simple address parsing - this could be enhanced
        parts = address.split(",")
        result = {}

        if len(parts) >= 1:
            result["address1"] = parts[0].strip()

        if len(parts) >= 2:
            city_part = parts[1].strip()
            # Check if it contains state and zip
            if " KY " in city_part:
                city_state_zip = city_part.split(" KY ")
                result["city"] = city_state_zip[0].strip()
                result["state"] = "KY"
                if len(city_state_zip) > 1:
                    result["postal_code"] = city_state_zip[1].strip()
            else:
                result["city"] = city_part

        return result
