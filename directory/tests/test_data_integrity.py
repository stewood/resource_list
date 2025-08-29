"""
Data Integrity Integration Tests

This module contains integration tests for data integrity and validation
across the application.

Features:
    - Data integrity testing
    - Field validation testing
    - Related object testing
    - Data consistency testing

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.tests.test_data_integrity import DataIntegrityTestCase
"""

from django.urls import reverse

from directory.models import Resource
from .base_test_case import BaseTestCase


class DataIntegrityTestCase(BaseTestCase):
    """Integration test cases for data integrity."""

    def test_data_integrity_integration(self):
        """Test data integrity across the application."""
        # Create a resource with all fields
        resource = self.create_test_resource(
            name="Complete Test Resource",
            description="A comprehensive test resource with detailed information",
            city="Test City",
            state="CA",
            county="Test County",
            postal_code="12345",
            phone="5551234567",
            email="test@example.com",
            website="https://example.com",
            status="draft",
            category=self.category,
            source="Integration Test",
            hours_of_operation="Monday-Friday 9AM-5PM",
            is_emergency_service=True,
            is_24_hour_service=False,
            eligibility_requirements="Must be homeless",
            populations_served="Adults, Veterans",
            insurance_accepted="None",
            cost_information="Free",
            languages_available="English, Spanish",
            capacity="50 people per day",
        )

        # Verify data integrity
        self.assertEqual(resource.name, "Complete Test Resource")
        self.assertEqual(resource.phone, "5551234567")  # Normalized phone number
        self.assertEqual(resource.website, "https://example.com")  # Normalized URL
        self.assertEqual(resource.state, "CA")  # Normalized state

        # Add service type
        resource.service_types.add(self.service_type)

        # Test that all data is preserved
        resource.refresh_from_db()

        self.assertEqual(resource.name, "Complete Test Resource")
        self.assertEqual(
            resource.description,
            "A comprehensive test resource with detailed information",
        )
        self.assertEqual(resource.city, "Test City")
        self.assertEqual(resource.state, "CA")
        self.assertEqual(resource.county, "Test County")
        self.assertEqual(resource.postal_code, "12345")
        self.assertEqual(resource.phone, "5551234567")  # Normalized phone number
        self.assertEqual(resource.email, "test@example.com")
        self.assertEqual(resource.website, "https://example.com")
        self.assertEqual(resource.category, self.category)
        self.assertEqual(resource.status, "draft")
        self.assertEqual(resource.source, "Integration Test")
        self.assertEqual(resource.hours_of_operation, "Monday-Friday 9AM-5PM")
        self.assertTrue(resource.is_emergency_service)
        self.assertFalse(resource.is_24_hour_service)
        self.assertEqual(resource.eligibility_requirements, "Must be homeless")
        self.assertEqual(resource.populations_served, "Adults, Veterans")
        self.assertEqual(resource.insurance_accepted, "None")
        self.assertEqual(resource.cost_information, "Free")
        self.assertEqual(resource.languages_available, "English, Spanish")
        self.assertEqual(resource.capacity, "50 people per day")
        self.assertEqual(resource.created_by, self.user)
        self.assertEqual(resource.updated_by, self.user)

        # Test related objects
        self.assertIn(self.service_type, resource.service_types.all())
        self.assertEqual(resource.category, self.category)
