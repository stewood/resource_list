"""
Tests for form functionality.
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone

from directory.forms import ResourceForm
from directory.models import ServiceType, TaxonomyCategory


class FormTestCase(TestCase):
    """Test cases for forms."""

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
        
        # Make reviewer a staff user so it can be selected as verifier
        self.reviewer.is_staff = True
        self.reviewer.save()

        # Create categories and service types
        self.category = TaxonomyCategory.objects.create(
            name="Test Category", slug="test-category"
        )
        
        self.service_type = ServiceType.objects.create(
            name="Test Service", slug="test-service"
        )

    def test_resource_form_valid_draft(self):
        """Test ResourceForm with valid draft data."""
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "draft",
        }
        
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_invalid_draft_no_contact(self):
        """Test ResourceForm with invalid draft data (no contact)."""
        form_data = {
            "name": "Test Resource",
            "status": "draft",
        }
        
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_resource_form_valid_needs_review(self):
        """Test ResourceForm with valid needs_review data."""
        form_data = {
            "name": "Test Resource",
            "description": "This is a detailed description with enough characters",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "needs_review",
        }
        
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_invalid_needs_review_short_description(self):
        """Test ResourceForm with invalid needs_review data (short description)."""
        form_data = {
            "name": "Test Resource",
            "description": "Too short",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "needs_review",
        }
        
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_resource_form_valid_published(self):
        """Test ResourceForm with valid published data."""
        form_data = {
            "name": "Test Resource",
            "description": "This is a detailed description with enough characters",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "5551234",  # No dashes - will be normalized
            "status": "published",
            "last_verified_at": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "last_verified_by": self.reviewer.pk,
        }
        
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_invalid_published_no_verification(self):
        """Test ResourceForm with invalid published data (no verification)."""
        form_data = {
            "name": "Test Resource",
            "description": "This is a detailed description with enough characters",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "published",
        }
        
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_verified_at", form.errors)

    def test_resource_form_with_category(self):
        """Test ResourceForm with category selection."""
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "draft",
            "category": self.category.pk,
        }
        
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_with_service_types(self):
        """Test ResourceForm with service type selection."""
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "draft",
            "service_types": [self.service_type.pk],
        }
        
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_contact_methods(self):
        """Test ResourceForm with different contact methods."""
        # Test with phone
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test with email
        form_data = {
            "name": "Test Resource",
            "email": "test@example.com",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test with website
        form_data = {
            "name": "Test Resource",
            "website": "https://example.com",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test with multiple contact methods
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "email": "test@example.com",
            "website": "https://example.com",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_postal_code_validation(self):
        """Test ResourceForm postal code validation."""
        # Valid postal codes
        valid_codes = ["12345", "12345-6789"]
        for code in valid_codes:
            form_data = {
                "name": "Test Resource",
                "phone": "555-1234",
                "state": "CA",
                "postal_code": code,
                "status": "draft",
            }
            form = ResourceForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Postal code {code} should be valid")
        
        # Invalid postal codes
        invalid_codes = ["1234", "123456", "12345-123", "12345-12345"]
        for code in invalid_codes:
            form_data = {
                "name": "Test Resource",
                "phone": "555-1234",
                "state": "CA",
                "postal_code": code,
                "status": "draft",
            }
            form = ResourceForm(data=form_data)
            self.assertFalse(form.is_valid(), f"Postal code {code} should be invalid")
            self.assertIn("postal_code", form.errors)

    def test_resource_form_initial_data(self):
        """Test ResourceForm initial data."""
        form = ResourceForm()
        self.assertEqual(form.fields["status"].initial, "draft")

    def test_resource_form_field_required_validation(self):
        """Test ResourceForm field required validation."""
        # Test without name
        form_data = {
            "phone": "555-1234",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_resource_form_email_validation(self):
        """Test ResourceForm email validation."""
        # Valid email
        form_data = {
            "name": "Test Resource",
            "email": "test@example.com",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid email
        form_data = {
            "name": "Test Resource",
            "email": "invalid-email",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_resource_form_website_validation(self):
        """Test ResourceForm website validation."""
        # Valid website
        form_data = {
            "name": "Test Resource",
            "website": "https://example.com",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid website
        form_data = {
            "name": "Test Resource",
            "website": "not-a-url",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_resource_form_state_validation(self):
        """Test ResourceForm state validation."""
        # Valid state
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "state": "CA",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid state (too long)
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "state": "CALIFORNIA",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("state", form.errors)

    def test_resource_form_phone_validation(self):
        """Test ResourceForm phone validation."""
        # Valid phone
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Phone with non-digits (should be normalized)
        form_data = {
            "name": "Test Resource",
            "phone": "(555) 123-4567",
            "status": "draft",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_description_length_validation(self):
        """Test ResourceForm description length validation for needs_review status."""
        # Short description for needs_review
        form_data = {
            "name": "Test Resource",
            "description": "Too short",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "needs_review",
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        
        # Long enough description for needs_review
        form_data = {
            "name": "Test Resource",
            "description": "This is a detailed description with enough characters to meet the minimum requirement",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "needs_review",
        }
        form = ResourceForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_resource_form_status_transition_validation(self):
        """Test ResourceForm validation for status transitions."""
        # Draft to needs_review without required fields
        form_data = {
            "name": "Test Resource",
            "phone": "555-1234",
            "status": "needs_review",  # Missing description, source
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("source", form.errors)
        
        # Needs review to published without verification
        form_data = {
            "name": "Test Resource",
            "description": "This is a detailed description with enough characters",
            "city": "Test City",
            "state": "CA",
            "source": "Test Source",
            "phone": "555-1234",
            "status": "published",  # Missing verification
        }
        form = ResourceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_verified_at", form.errors)
        self.assertIn("last_verified_by", form.errors)
