"""
Tests for views.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from directory.models import Resource, ServiceType, TaxonomyCategory


class BaseTestCase(TestCase):
    """Base test case with common setup."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        
        self.editor = User.objects.create_user(
            username="editor",
            password="testpass123",
            first_name="Test",
            last_name="Editor",
        )
        
        self.reviewer = User.objects.create_user(
            username="reviewer",
            password="testpass123",
            first_name="Test",
            last_name="Reviewer",
        )
        
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            first_name="Test",
            last_name="Admin",
        )

        # Create groups
        self.editor_group = Group.objects.create(name="Editor")
        self.reviewer_group = Group.objects.create(name="Reviewer")
        self.admin_group = Group.objects.create(name="Admin")

        # Assign users to groups
        self.editor.groups.add(self.editor_group)
        self.reviewer.groups.add(self.reviewer_group)
        self.admin.groups.add(self.admin_group)

        # Create categories and service types
        self.category = TaxonomyCategory.objects.create(
            name="Test Category", slug="test-category"
        )
        
        self.service_type = ServiceType.objects.create(
            name="Test Service", slug="test-service"
        )

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
        
        return Resource.objects.create(**defaults)


class ViewTestCase(BaseTestCase):
    """Test cases for views."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create a test resource
        self.resource = self.create_test_resource(
            name="Test Resource",
            description="This is a test resource with a description that meets the minimum length requirement.",
            city="Test City",
            state="CA",
            phone="5551234",
            status="draft",
        )

    def test_resource_list_view(self):
        """Test resource list view."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:resource_list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Resource")

    def test_resource_list_view_with_search(self):
        """Test resource list view with search."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:resource_list")
        response = self.client.get(url, {"q": "Test"})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Resource")

    def test_resource_list_view_with_filters(self):
        """Test resource list view with filters."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:resource_list")
        response = self.client.get(url, {
            "status": "draft",
            "city": "Test City"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Resource")

    def test_resource_detail_view(self):
        """Test resource detail view."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:resource_detail", args=[self.resource.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Resource")

    def test_resource_create_view(self):
        """Test resource create view."""
        self.client.login(username="editor", password="testpass123")
        
        url = reverse("directory:resource_create")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_resource_update_view(self):
        """Test resource update view."""
        self.client.login(username="editor", password="testpass123")
        
        url = reverse("directory:resource_update", args=[self.resource.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Resource")

    def test_submit_for_review_view_success(self):
        """Test submit for review view with valid data."""
        self.client.login(username="editor", password="testpass123")
        
        # Update resource to meet review requirements
        self.resource.city = "Test City"
        self.resource.state = "CA"
        self.resource.description = "This is a detailed description with enough characters"
        self.resource.source = "Test Source"
        self.resource.save()
        
        url = reverse("directory:submit_for_review", args=[self.resource.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, "needs_review")

    def test_submit_for_review_view_permission_denied(self):
        """Test submit for review view with insufficient permissions."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:submit_for_review", args=[self.resource.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)

    def test_publish_resource_view_success(self):
        """Test publish resource view with valid data."""
        self.client.login(username="reviewer", password="testpass123")
        
        # Update resource to meet publish requirements
        self.resource.city = "Test City"
        self.resource.state = "CA"
        self.resource.description = "This is a detailed description with enough characters"
        self.resource.source = "Test Source"
        self.resource.status = "needs_review"
        self.resource.save()
        
        url = reverse("directory:publish_resource", args=[self.resource.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, "published")
        self.assertIsNotNone(self.resource.last_verified_at)
        self.assertEqual(self.resource.last_verified_by, self.reviewer)

    def test_publish_resource_view_permission_denied(self):
        """Test publish resource view with insufficient permissions."""
        self.client.login(username="editor", password="testpass123")
        
        url = reverse("directory:publish_resource", args=[self.resource.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)

    def test_unpublish_resource_view(self):
        """Test unpublish resource view."""
        self.client.login(username="reviewer", password="testpass123")
        
        # Set resource to published with required fields
        self.resource.status = "published"
        self.resource.last_verified_at = timezone.now() - timedelta(days=30)
        self.resource.last_verified_by = self.reviewer
        self.resource.source = "Test Source"
        self.resource.save()
        
        url = reverse("directory:unpublish_resource", args=[self.resource.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, "needs_review")

    def test_dashboard_view(self):
        """Test dashboard view."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:dashboard")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_view_counts(self):
        """Test dashboard view resource counts."""
        self.client.login(username="testuser", password="testpass123")
        
        # Create additional resources for testing counts
        self.create_test_resource(
            name="Published Resource",
            phone="5555678",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        self.create_test_resource(
            name="Review Resource",
            phone="5559999",
            status="needs_review",
            source="Test Source",
        )
        
        url = reverse("directory:dashboard")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check that context contains the expected counts
        self.assertIn("draft_count", response.context)
        self.assertIn("review_count", response.context)
        self.assertIn("published_count", response.context)

    def test_resource_list_view_pagination(self):
        """Test resource list view pagination."""
        self.client.login(username="testuser", password="testpass123")
        
        # Create multiple resources to test pagination
        for i in range(25):
            self.create_test_resource(
                name=f"Resource {i}",
                phone=f"555{i:04d}",
                status="draft",
            )
        
        url = reverse("directory:resource_list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check that pagination is working
        self.assertIn("is_paginated", response.context)
        self.assertTrue(response.context["is_paginated"])

    def test_resource_list_view_sorting(self):
        """Test resource list view sorting."""
        self.client.login(username="testuser", password="testpass123")
        
        # Create resources with different names for sorting
        self.create_test_resource(
            name="Alpha Resource",
            phone="5551111",
            status="draft",
        )
        
        self.create_test_resource(
            name="Beta Resource",
            phone="5552222",
            status="draft",
        )
        
        # Test ascending sort
        url = reverse("directory:resource_list")
        response = self.client.get(url, {"sort": "name"})
        
        self.assertEqual(response.status_code, 200)
        resources = response.context["resources"]
        self.assertEqual(resources[0].name, "Alpha Resource")
        self.assertEqual(resources[1].name, "Beta Resource")
        
        # Test descending sort
        response = self.client.get(url, {"sort": "-name"})
        
        self.assertEqual(response.status_code, 200)
        resources = response.context["resources"]
        self.assertEqual(resources[0].name, "Beta Resource")
        self.assertEqual(resources[1].name, "Alpha Resource")

    def test_resource_list_view_htmx(self):
        """Test resource list view with HTMX requests."""
        self.client.login(username="testuser", password="testpass123")
        
        url = reverse("directory:resource_list")
        response = self.client.get(url, HTTP_HX_REQUEST="true")
        
        self.assertEqual(response.status_code, 200)
        # HTMX requests should return partial content
        self.assertContains(response, "Test Resource")

    def test_resource_detail_view_permissions(self):
        """Test resource detail view with different user permissions."""
        # Test with regular user
        self.client.login(username="testuser", password="testpass123")
        url = reverse("directory:resource_detail", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test with editor
        self.client.login(username="editor", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test with reviewer
        self.client.login(username="reviewer", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_resource_create_view_permissions(self):
        """Test resource create view with different user permissions."""
        # Test with regular user (should be denied)
        self.client.login(username="testuser", password="testpass123")
        url = reverse("directory:resource_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Test with editor (should be allowed)
        self.client.login(username="editor", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test with reviewer (should be allowed)
        self.client.login(username="reviewer", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_resource_update_view_permissions(self):
        """Test resource update view with different user permissions."""
        # Test with regular user (should be denied)
        self.client.login(username="testuser", password="testpass123")
        url = reverse("directory:resource_update", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Test with editor (should be allowed)
        self.client.login(username="editor", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test with reviewer (should be allowed)
        self.client.login(username="reviewer", password="testpass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_authentication_required(self):
        """Test that views require authentication."""
        # Test resource list without login
        url = reverse("directory:resource_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test resource detail without login
        url = reverse("directory:resource_detail", args=[self.resource.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test dashboard without login
        url = reverse("directory:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
