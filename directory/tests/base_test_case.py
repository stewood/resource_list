"""
Base Test Case - Common Test Setup and Utilities

This module contains the BaseTestCase class which provides common setup
and utility functions for all integration tests.

Features:
    - Common user and group creation
    - Test data setup (categories, service types)
    - Helper functions for creating test resources
    - Reusable test utilities

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.tests.base_test_case import BaseTestCase
    
    class MyTestCase(BaseTestCase):
        def test_something(self):
            resource = self.create_test_resource(name="Test")
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone

from directory.models import Resource, ServiceType, TaxonomyCategory


class BaseTestCase(TestCase):
    """Base test case with common setup."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data once for the entire test class."""
        # Create users
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        
        cls.editor = User.objects.create_user(
            username="editor",
            password="testpass123",
            first_name="Test",
            last_name="Editor",
        )
        
        cls.reviewer = User.objects.create_user(
            username="reviewer",
            password="testpass123",
            first_name="Test",
            last_name="Reviewer",
        )
        
        cls.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            first_name="Test",
            last_name="Admin",
        )

        # Create groups
        cls.editor_group = Group.objects.create(name="Editor")
        cls.reviewer_group = Group.objects.create(name="Reviewer")
        cls.admin_group = Group.objects.create(name="Admin")

        # Assign users to groups
        cls.editor.groups.add(cls.editor_group)
        cls.reviewer.groups.add(cls.reviewer_group)
        cls.admin.groups.add(cls.admin_group)

        # Create categories and service types
        cls.category = TaxonomyCategory.objects.create(
            name="Test Category", slug="test-category"
        )
        
        cls.service_type = ServiceType.objects.create(
            name="Test Service", slug="test-service"
        )

    def setUp(self):
        """Set up test-specific data (runs for each test)."""
        # Any test-specific setup can go here
        pass

    def create_test_resource(self, **kwargs):
        """Helper function to create a valid test resource."""
        defaults = {
            "name": "Test Resource",
            "description": "This is a test resource with a description that meets the minimum length requirement of twenty characters.",
            "city": "Test City",
            "state": "CA",
            "phone": "5551234",  # No dashes - will be normalized
            "status": "draft",
            "created_by": self.user,
            "updated_by": self.user,
        }
        
        # Update with provided kwargs
        defaults.update(kwargs)
        
        # Handle published status requirements
        if defaults.get("status") == "published":
            defaults.setdefault("last_verified_at", timezone.now() - timedelta(days=30))
            defaults.setdefault("last_verified_by", self.reviewer)
            defaults.setdefault("source", "Test Source")
        
        # Handle needs_review status requirements
        elif defaults.get("status") == "needs_review":
            defaults.setdefault("source", "Test Source")
            defaults.setdefault("description", "This is a detailed description with enough characters")
            defaults.setdefault("city", "Test City")
            defaults.setdefault("state", "CA")
        
        return Resource.objects.create(**defaults)
