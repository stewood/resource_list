"""
Tests for the directory application.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Resource, ResourceVersion, TaxonomyCategory


class VersionComparisonTestCase(TestCase):
    """Test cases for version comparison functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.category = TaxonomyCategory.objects.create(
            name="Test Category", slug="test-category"
        )

        self.resource = Resource.objects.create(
            name="Test Resource",
            category=self.category,
            description="Initial description",
            city="Test City",
            state="CA",
            phone="555-1234",  # Add contact method to pass validation
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_version_comparison_view(self):
        """Test that version comparison view works."""
        # Get the existing version created by the signal
        version = ResourceVersion.objects.get(resource=self.resource, version_number=1)

        # Test the view
        url = reverse(
            "directory:version_comparison", args=[self.resource.pk, version.pk]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Version Comparison")
        self.assertContains(response, "Test Resource")

    def test_version_history_view(self):
        """Test that version history view works."""
        # Test the view with the existing resource (which already has a version from setUp)
        url = reverse("directory:version_history", args=[self.resource.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Version History")
        self.assertContains(response, "Test Resource")

    def test_compare_versions_utility(self):
        """Test the compare_versions utility function."""
        from .utils import compare_versions

        snapshot1 = {
            "name": "Old Name",
            "description": "Old description",
            "city": "Old City",
        }

        snapshot2 = {
            "name": "New Name",
            "description": "New description",
            "state": "CA",
        }

        differences = compare_versions(snapshot1, snapshot2)

        # Should have 4 differences: name, description, city (removed), state (added)
        self.assertEqual(len(differences), 4)

        # Check specific differences
        self.assertIn("name", differences)
        self.assertEqual(differences["name"]["old_value"], "Old Name")
        self.assertEqual(differences["name"]["new_value"], "New Name")
        self.assertEqual(differences["name"]["diff_type"], "changed")

        self.assertIn("city", differences)
        self.assertEqual(differences["city"]["diff_type"], "removed")

        self.assertIn("state", differences)
        self.assertEqual(differences["state"]["diff_type"], "added")
