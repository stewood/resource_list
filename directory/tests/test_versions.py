"""
Tests for version control functionality.
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from directory.models import Resource, ResourceVersion, ServiceType, TaxonomyCategory
from directory.utils import compare_versions


class VersionTestCase(TestCase):
    """Test cases for version control functionality."""

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

    def test_version_creation_on_save(self):
        """Test that versions are created when resources are saved."""
        resource = Resource.objects.create(
            name="Test Resource",
            phone="555-123-4567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should have one version created
        versions = ResourceVersion.objects.filter(resource=resource)
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().version_number, 1)

    def test_version_creation_on_update(self):
        """Test that new versions are created when resources are updated."""
        resource = Resource.objects.create(
            name="Test Resource",
            phone="555-123-4567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Update the resource
        resource.name = "Updated Test Resource"
        resource.save()
        
        # Should have two versions
        versions = ResourceVersion.objects.filter(resource=resource)
        self.assertEqual(versions.count(), 2)
        # Use first() since ordering is by -version_number (descending)
        self.assertEqual(versions.first().version_number, 2)

    def test_version_data_snapshot(self):
        """Test that version snapshots contain correct data."""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            description="Test description",
            city="Test City",
            state="CA",
            phone="5551234567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get the version
        version = ResourceVersion.objects.get(resource=resource, version_number=1)
        
        # Check that snapshot contains the correct data
        snapshot = version.snapshot
        self.assertEqual(snapshot["name"], "Test Resource")
        self.assertEqual(snapshot["description"], "Test description")
        self.assertEqual(snapshot["city"], "Test City")
        self.assertEqual(snapshot["state"], "CA")
        self.assertEqual(snapshot["phone"], "5551234567")  # Normalized phone number
        self.assertEqual(snapshot["status"], "draft")

    def test_version_comparison_utility(self):
        """Test the compare_versions utility function."""
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

    def test_version_comparison_no_changes(self):
        """Test version comparison with no changes."""
        snapshot1 = {
            "name": "Test Resource",
            "description": "Test description",
        }
        
        snapshot2 = {
            "name": "Test Resource",
            "description": "Test description",
        }
        
        differences = compare_versions(snapshot1, snapshot2)
        self.assertEqual(len(differences), 0)

    def test_version_comparison_empty_snapshots(self):
        """Test version comparison with empty snapshots."""
        differences = compare_versions({}, {})
        self.assertEqual(len(differences), 0)
        
        differences = compare_versions({"name": "Test"}, {})
        self.assertEqual(len(differences), 1)
        self.assertEqual(differences["name"]["diff_type"], "removed")
        
        differences = compare_versions({}, {"name": "Test"})
        self.assertEqual(len(differences), 1)
        self.assertEqual(differences["name"]["diff_type"], "added")

    def test_version_comparison_complex_changes(self):
        """Test version comparison with complex changes."""
        snapshot1 = {
            "name": "Old Name",
            "description": "Old description",
            "city": "Old City",
            "state": "CA",
            "phone": "555-1234",
            "email": "old@example.com",
        }
        
        snapshot2 = {
            "name": "New Name",
            "description": "New description",
            "city": "New City",
            "state": "NY",
            "phone": "555-5678",
            "website": "https://new.example.com",
        }
        
        differences = compare_versions(snapshot1, snapshot2)
        
        # Should have 7 differences
        self.assertEqual(len(differences), 7)
        
        # Check changed fields
        self.assertEqual(differences["name"]["diff_type"], "changed")
        self.assertEqual(differences["description"]["diff_type"], "changed")
        self.assertEqual(differences["city"]["diff_type"], "changed")
        self.assertEqual(differences["state"]["diff_type"], "changed")
        self.assertEqual(differences["phone"]["diff_type"], "changed")
        
        # Check removed field
        self.assertEqual(differences["email"]["diff_type"], "removed")
        
        # Check added field
        self.assertEqual(differences["website"]["diff_type"], "added")

    def test_version_ordering(self):
        """Test that versions are ordered correctly."""
        resource = Resource.objects.create(
            name="Test Resource",
            phone="555-123-4567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Make several updates
        resource.name = "Updated 1"
        resource.save()
        
        resource.name = "Updated 2"
        resource.save()
        
        resource.name = "Updated 3"
        resource.save()
        
        # Check version ordering
        versions = ResourceVersion.objects.filter(resource=resource).order_by('version_number')
        self.assertEqual(versions.count(), 4)
        
        # Check version numbers
        for i, version in enumerate(versions, 1):
            self.assertEqual(version.version_number, i)

    def test_version_metadata(self):
        """Test version metadata fields."""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            description="Test description",
            city="Test City",
            state="CA",
            phone="5551234567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get the version
        version = ResourceVersion.objects.get(resource=resource, version_number=1)
        
        # Check metadata fields
        self.assertEqual(version.resource, resource)
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.change_type, "create")
        self.assertEqual(version.changed_by, self.user)
        self.assertIsNotNone(version.changed_at)
        self.assertIsNotNone(version.snapshot_json)
        self.assertIsNotNone(version.changed_fields)

    def test_version_str_representation(self):
        """Test version string representation."""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            description="Test description",
            city="Test City",
            state="CA",
            phone="5551234567",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get the version
        version = ResourceVersion.objects.get(resource=resource, version_number=1)
        
        # Check string representation
        expected_str = "Test Resource v1"
        self.assertEqual(str(version), expected_str)

    def test_version_with_related_objects(self):
        """Test version creation with related objects."""
        # Create a resource with related objects
        resource = Resource.objects.create(
            name="Test Resource",
            description="Test description",
            city="Test City",
            state="CA",
            phone="5551234567",
            status="draft",
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Add service types
        resource.service_types.add(self.service_type)
        
        # Get the version
        version = ResourceVersion.objects.get(resource=resource, version_number=1)
        
        # Check that snapshot contains related object data
        snapshot = version.snapshot
        self.assertEqual(snapshot["name"], "Test Resource")
        self.assertEqual(snapshot["category_id"], self.category.id)

    def test_version_with_null_fields(self):
        """Test version creation with null fields."""
        # Create a resource with null fields but required contact method
        resource = Resource.objects.create(
            name="Test Resource",
            description="Test description",
            phone="5551234567",  # Required for draft
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get the version
        version = ResourceVersion.objects.get(resource=resource, version_number=1)
        
        # Check that snapshot handles null fields correctly
        snapshot = version.snapshot
        self.assertEqual(snapshot["name"], "Test Resource")
        self.assertEqual(snapshot.get("city"), "")  # Empty string for blank fields
        self.assertEqual(snapshot.get("state"), "")  # Empty string for blank fields

    def test_version_comparison_with_none_values(self):
        """Test version comparison with None values."""
        snapshot1 = {
            "name": "Test Resource",
            "description": None,
            "city": "",
        }
        
        snapshot2 = {
            "name": "Test Resource",
            "description": "New description",
            "city": "New City",
        }
        
        differences = compare_versions(snapshot1, snapshot2)
        
        # Should have 2 differences
        self.assertEqual(len(differences), 2)
        self.assertEqual(differences["description"]["diff_type"], "changed")
        self.assertEqual(differences["city"]["diff_type"], "changed")

    def test_version_comparison_with_boolean_values(self):
        """Test version comparison with boolean values."""
        snapshot1 = {
            "name": "Test Resource",
            "is_emergency_service": False,
            "is_24_hour_service": True,
        }
        
        snapshot2 = {
            "name": "Test Resource",
            "is_emergency_service": True,
            "is_24_hour_service": False,
        }
        
        differences = compare_versions(snapshot1, snapshot2)
        
        # Should have 2 differences
        self.assertEqual(len(differences), 2)
        self.assertEqual(differences["is_emergency_service"]["diff_type"], "changed")
        self.assertEqual(differences["is_24_hour_service"]["diff_type"], "changed")
        self.assertEqual(differences["is_emergency_service"]["old_value"], False)
        self.assertEqual(differences["is_emergency_service"]["new_value"], True)
