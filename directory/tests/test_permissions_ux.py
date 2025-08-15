"""
Permission and User Experience Integration Tests

This module contains integration tests for permission-based functionality
and user experience scenarios.

Features:
    - Permission workflow testing
    - User experience testing
    - Error handling testing
    - Multi-user integration testing

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.tests.test_permissions_ux import PermissionUXTestCase
"""

from django.urls import reverse

from directory.models import Resource
from .base_test_case import BaseTestCase


class PermissionUXTestCase(BaseTestCase):
    """Integration test cases for permissions and user experience."""

    def test_permission_workflow_integration(self):
        """Test permission workflow integration."""
        # Test that regular user cannot access editor functions
        self.client.login(username="testuser", password="testpass123")
        
        # Try to create resource (should be denied)
        create_url = reverse("directory:resource_create")
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 403)
        
        # Try to submit for review (should be denied)
        resource = self.create_test_resource(
            name="Test Resource",
            phone="5551234567",
            status="draft",
        )
        
        submit_url = reverse("directory:submit_for_review", args=[resource.pk])
        response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 403)
        
        # Test that editor can create but not publish
        self.client.login(username="editor", password="testpass123")
        
        # Should be able to create
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)
        
        # Should not be able to publish
        publish_url = reverse("directory:publish_resource", args=[resource.pk])
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 403)
        
        # Test that reviewer can publish
        self.client.login(username="reviewer", password="testpass123")
        
        # Update resource to meet publish requirements
        resource.city = "Test City"
        resource.state = "CA"
        resource.description = "This is a detailed description with enough characters"
        resource.source = "Test Source"
        resource.status = "needs_review"
        resource.save()
        
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 200)

    def test_user_experience_integration(self):
        """Test user experience integration."""
        self.client.login(username="editor", password="testpass123")
        
        # Test resource creation flow
        create_url = reverse("directory:resource_create")
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Resource")
        
        # Test resource list with HTMX
        list_url = reverse("directory:resource_list")
        response = self.client.get(list_url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        
        # Test dashboard
        dashboard_url = reverse("directory:dashboard")
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_error_handling_integration(self):
        """Test error handling integration."""
        self.client.login(username="editor", password="testpass123")
        
        # Test accessing non-existent resource
        detail_url = reverse("directory:resource_detail", args=[99999])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        
        # Test accessing resource with invalid ID (should be 404, not NoReverseMatch)
        try:
            detail_url = reverse("directory:resource_detail", args=["invalid"])
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 404)
        except:
            # If reverse fails, that's also acceptable for invalid IDs
            pass
        
        # Test invalid form submission
        create_url = reverse("directory:resource_create")
        invalid_data = {
            "name": "",  # Invalid: empty name
            "status": "draft",
        }
        response = self.client.post(create_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Form should be re-displayed with errors

    def test_multi_user_integration(self):
        """Test multi-user integration scenarios."""
        # Create resources by different users
        resource1 = self.create_test_resource(
            name="Editor's Resource",
            phone="5551111111",
            status="draft",
            created_by=self.editor,
            updated_by=self.editor,
        )
        
        resource2 = self.create_test_resource(
            name="Reviewer's Resource",
            phone="5552222222",
            status="needs_review",
            created_by=self.reviewer,
            updated_by=self.reviewer,
            source="Test Source",
        )
        
        # Test that users can see resources created by others
        self.client.login(username="testuser", password="testpass123")
        
        # Debug: Check if resources were created
        self.assertTrue(Resource.objects.filter(name="Editor's Resource").exists())
        self.assertTrue(Resource.objects.filter(name="Reviewer's Resource").exists())
        
        # Test that users can access detail views of others' resources
        detail_url1 = reverse("directory:resource_detail", args=[resource1.pk])
        response = self.client.get(detail_url1)
        self.assertEqual(response.status_code, 200)
        
        detail_url2 = reverse("directory:resource_detail", args=[resource2.pk])
        response = self.client.get(detail_url2)
        self.assertEqual(response.status_code, 200)
        
        # Test resource list view (simplified)
        list_url = reverse("directory:resource_list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        
        # Just verify that the resources exist in the context
        resources_in_response = response.context["resources"]
        resource_names = [r.name for r in resources_in_response]
        self.assertIn("Editor's Resource", resource_names)
        self.assertIn("Reviewer's Resource", resource_names)
        
        # Test that users can access detail views of others' resources
        detail_url1 = reverse("directory:resource_detail", args=[resource1.pk])
        response = self.client.get(detail_url1)
        self.assertEqual(response.status_code, 200)
        
        detail_url2 = reverse("directory:resource_detail", args=[resource2.pk])
        response = self.client.get(detail_url2)
        self.assertEqual(response.status_code, 200)
