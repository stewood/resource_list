"""
Search and Filter Integration Tests

This module contains integration tests for search and filtering functionality
including performance testing and data consistency.

Features:
    - Search functionality testing
    - Filter integration testing
    - Search performance testing
    - Data consistency testing

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.tests.test_search_filter import SearchFilterTestCase
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from directory.models import Resource
from .base_test_case import BaseTestCase


class SearchFilterTestCase(BaseTestCase):
    """Integration test cases for search and filtering functionality."""

    def test_search_and_filter_integration(self):
        """Test search and filtering integration."""
        self.client.login(username="testuser", password="testpass123")
        
        # Create multiple resources for testing
        self.create_test_resource(
            name="Food Bank",
            description="Provides food assistance with comprehensive support services.",
            city="Test City",
            state="CA",
            phone="5551111",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        self.create_test_resource(
            name="Shelter",
            description="Emergency shelter with comprehensive support services.",
            city="Other City",
            state="CA",
            phone="5552222",
            status="draft",
        )
        
        # Test search with filters
        url = reverse("directory:resource_list")
        response = self.client.get(url, {
            "q": "Food",
            "status": "published",
            "city": "Test City"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Food Bank")
        self.assertNotContains(response, "Shelter")

    def test_search_performance_integration(self):
        """Test search performance with multiple resources."""
        # Create many resources for performance testing
        for i in range(50):
            self.create_test_resource(
                name=f"Resource {i}",
                description=f"Description for resource {i} with comprehensive details",
                city=f"City {i % 5}",
                state="CA",
                phone=f"555{i:04d}",
                status="published" if i % 3 == 0 else "draft",
                last_verified_at=timezone.now() - timedelta(days=30) if i % 3 == 0 else None,
                last_verified_by=self.reviewer if i % 3 == 0 else None,
                source="Test Source" if i % 3 == 0 else "",
            )
        
        self.client.login(username="testuser", password="testpass123")
        
        # Test search performance
        url = reverse("directory:resource_list")
        
        # Test basic search
        response = self.client.get(url, {"q": "Resource"})
        self.assertEqual(response.status_code, 200)
        
        # Test filtered search
        response = self.client.get(url, {
            "q": "Resource",
            "status": "published",
            "city": "City 0"
        })
        self.assertEqual(response.status_code, 200)
        
        # Test pagination
        response = self.client.get(url, {"page": "2"})
        self.assertEqual(response.status_code, 200)

    def test_data_consistency_integration(self):
        """Test data consistency across different views."""
        # Create a resource
        resource = self.create_test_resource(
            name="Consistency Test Resource",
            description="Test description with enough characters",
            city="Test City",
            state="CA",
            phone="5551234",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        self.client.login(username="testuser", password="testpass123")
        
        # Test consistency across different views
        views_to_test = [
            reverse("directory:resource_list"),
            reverse("directory:resource_detail", args=[resource.pk]),
            reverse("directory:dashboard"),
        ]
        
        for url in views_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Consistency Test Resource")
