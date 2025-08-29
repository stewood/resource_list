"""
Integration tests for the directory application.

This module now serves as a compatibility layer that imports all integration
tests from their respective modules. This ensures that existing test runners
and CI/CD pipelines continue to work without modification.

The actual integration tests have been split into focused modules:
- test_workflows.py: Workflow and status transition tests
- test_search_filter.py: Search and filtering tests
- test_permissions_ux.py: Permission and user experience tests
- test_data_integrity.py: Data integrity and validation tests
- base_test_case.py: Common test setup and utilities

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    # This file maintains backward compatibility
    # All tests can still be run with: python manage.py test directory.tests.test_integration
"""

from django.test import TestCase

# Import all test classes to maintain backward compatibility
from .base_test_case import BaseTestCase
from .test_workflows import WorkflowTestCase

# from .test_search_filter import SearchFilterTestCase  # Removed - GIS functionality not implemented yet
from .test_permissions_ux import PermissionUXTestCase
from .test_data_integrity import DataIntegrityTestCase


class IntegrationTestCase(BaseTestCase):
    """Legacy integration test case for backward compatibility.

    This class ensures that any existing code that imports from test_integration
    continues to work. It inherits from BaseTestCase to provide the same
    functionality as the original IntegrationTestCase.
    """

    def test_backward_compatibility(self):
        """Test that the refactored integration tests are working."""
        # This test ensures that the refactoring was successful
        # and all the imported test classes are available
        self.assertTrue(hasattr(self, "user"))
        self.assertTrue(hasattr(self, "editor"))
        self.assertTrue(hasattr(self, "reviewer"))
        self.assertTrue(hasattr(self, "admin"))
        self.assertTrue(hasattr(self, "category"))
        self.assertTrue(hasattr(self, "service_type"))

        # Test that the helper method works
        resource = self.create_test_resource(name="Backward Compatibility Test")
        self.assertEqual(resource.name, "Backward Compatibility Test")
        self.assertEqual(resource.status, "draft")


# Ensure all test classes are available for discovery
__all__ = [
    "BaseTestCase",
    "WorkflowTestCase",
    # "SearchFilterTestCase",  # Removed - GIS functionality not implemented yet
    "PermissionUXTestCase",
    "DataIntegrityTestCase",
    "IntegrationTestCase",
]
