"""
Workflow Integration Tests

This module contains integration tests for resource workflow functionality
including creation, review, and publishing processes.

Features:
    - Complete workflow testing from draft to published
    - Workflow validation testing
    - Status transition testing
    - Permission-based workflow testing

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.tests.test_workflows import WorkflowTestCase
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from directory.models import Resource
from .base_test_case import BaseTestCase


class WorkflowTestCase(BaseTestCase):
    """Integration test cases for workflow functionality."""

    def test_complete_workflow(self):
        """Test complete resource workflow from draft to published."""
        self.client.login(username="editor", password="testpass123")
        
        # 1. Create a draft resource
        create_url = reverse("directory:resource_create")
        create_data = {
            "name": "Integration Test Resource",
            "phone": "555-1234",
            "status": "draft",
        }
        
        response = self.client.post(create_url, create_data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Get the created resource
        resource = Resource.objects.get(name="Integration Test Resource")
        self.assertEqual(resource.status, "draft")
        
        # 2. Update to meet review requirements
        update_url = reverse("directory:resource_update", args=[resource.pk])
        update_data = {
            "name": "Integration Test Resource",
            "description": "This is a detailed description with enough characters",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "draft",
        }
        
        response = self.client.post(update_url, update_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Submit for review
        self.client.login(username="editor", password="testpass123")
        submit_url = reverse("directory:submit_for_review", args=[resource.pk])
        response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 200)
        
        resource.refresh_from_db()
        self.assertEqual(resource.status, "needs_review")
        
        # 4. Publish the resource
        self.client.login(username="reviewer", password="testpass123")
        publish_url = reverse("directory:publish_resource", args=[resource.pk])
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 200)
        
        resource.refresh_from_db()
        self.assertEqual(resource.status, "published")
        self.assertIsNotNone(resource.last_verified_at)
        self.assertIsNotNone(resource.last_verified_by)

    def test_workflow_validation_integration(self):
        """Test workflow validation integration."""
        self.client.login(username="editor", password="testpass123")
        
        # Create a resource
        resource = self.create_test_resource(
            name="Validation Test Resource",
            phone="5551234",
            status="draft",
        )
        
        # Try to submit for review without required fields (should fail)
        submit_url = reverse("directory:submit_for_review", args=[resource.pk])
        response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 400)  # Validation error
        
        # Add required fields
        resource.city = "Test City"
        resource.state = "CA"
        resource.description = "This is a detailed description with enough characters"
        resource.source = "Test Source"
        resource.save()
        
        # Now submit for review (should succeed)
        response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 200)
        
        resource.refresh_from_db()
        self.assertEqual(resource.status, "needs_review")
        
        # Try to publish without verification (should fail)
        self.client.login(username="reviewer", password="testpass123")
        publish_url = reverse("directory:publish_resource", args=[resource.pk])
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 200)  # Should succeed and auto-verify
