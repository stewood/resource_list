"""
Tests for Resource model functionality.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
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
        # Most tests won't need additional setup
        pass


class ResourceModelTestCase(BaseTestCase):
    """Test cases for Resource model."""

    def test_resource_creation(self):
        """Test basic resource creation."""
        resource = Resource.objects.create(
            name="Test Resource",
            category=self.category,
            description="Test description",
            city="Test City",
            state="CA",
            phone="555-123-4567",  # Valid phone number
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(resource.name, "Test Resource")
        self.assertEqual(resource.status, "draft")
        self.assertFalse(resource.is_deleted)

    def test_draft_validation_success(self):
        """Test draft validation with valid data."""
        resource = Resource(
            name="Test Resource",
            phone="555-123-4567",  # Valid phone number
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should not raise validation error
        resource.full_clean()

    def test_draft_validation_failure_no_name(self):
        """Test draft validation fails without name."""
        resource = Resource(
            phone="555-1234",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValidationError) as cm:
            resource.full_clean()
        
        self.assertIn("name", cm.exception.error_dict)

    def test_draft_validation_failure_no_contact(self):
        """Test draft validation fails without contact method."""
        resource = Resource(
            name="Test Resource",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValidationError) as cm:
            resource.full_clean()
        
        self.assertIn("phone", cm.exception.error_dict)

    def test_needs_review_validation_success(self):
        """Test needs_review validation with valid data."""
        resource = Resource(
            name="Test Resource",
            description="This is a detailed description with enough characters",
            city="Test City",
            state="CA",
            source="Test Source",
            phone="555-1234",
            status="needs_review",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should not raise validation error
        resource.full_clean()

    def test_needs_review_validation_success_no_city_state(self):
        """Test needs_review validation passes without city/state."""
        resource = Resource(
            name="Test Resource",
            description="This is a detailed description with enough characters",
            source="Test Source",
            phone="555-1234",
            status="needs_review",
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should not raise validation error since city/state are now optional
        resource.full_clean()

    def test_needs_review_validation_failure_short_description(self):
        """Test needs_review validation fails with short description."""
        resource = Resource(
            name="Test Resource",
            description="Too short",
            city="Test City",
            state="CA",
            source="Test Source",
            phone="555-1234",
            status="needs_review",
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValidationError) as cm:
            resource.full_clean()
        
        self.assertIn("description", cm.exception.error_dict)

    def test_published_validation_success(self):
        """Test published validation with valid data."""
        resource = Resource(
            name="Test Resource",
            description="This is a detailed description with enough characters",
            city="Test City",
            state="CA",
            source="Test Source",
            phone="555-1234",
            status="published",
            last_verified_at=timezone.now(),
            last_verified_by=self.user,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should not raise validation error
        resource.full_clean()

    def test_published_validation_failure_no_verification(self):
        """Test published validation fails without verification."""
        resource = Resource(
            name="Test Resource",
            description="This is a detailed description with enough characters",
            city="Test City",
            state="CA",
            source="Test Source",
            phone="555-1234",
            status="published",
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValidationError) as cm:
            resource.full_clean()
        
        self.assertIn("last_verified_at", cm.exception.error_dict)

    def test_data_normalization(self):
        """Test data normalization on save."""
        resource = Resource.objects.create(
            name="Test Resource",
            state="ca",  # Should be normalized to CA
            phone="(555) 123-4567",  # Should be normalized to digits only
            website="example.com",  # Should get https:// prefix
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(resource.state, "CA")
        self.assertEqual(resource.phone, "5551234567")
        self.assertEqual(resource.website, "https://example.com")

    def test_postal_code_validation(self):
        """Test postal code validation."""
        # Valid postal codes
        valid_codes = ["12345", "12345-6789"]
        for code in valid_codes:
            resource = Resource(
                name="Test Resource",
                state="CA",
                postal_code=code,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            resource.full_clean()  # Should not raise error

        # Invalid postal codes
        invalid_codes = ["1234", "123456", "12345-123", "12345-12345"]
        for code in invalid_codes:
            resource = Resource(
                name="Test Resource",
                state="CA",
                postal_code=code,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            with self.assertRaises(ValidationError) as cm:
                resource.full_clean()
            self.assertIn("postal_code", cm.exception.error_dict)

    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "test+tag@example.org"]
        for email in valid_emails:
            resource = Resource(
                name="Test Resource",
                email=email,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            resource.full_clean()  # Should not raise error

        # Invalid emails
        invalid_emails = ["invalid-email", "@example.com", "test@", "test..test@example.com"]
        for email in invalid_emails:
            resource = Resource(
                name="Test Resource",
                email=email,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            with self.assertRaises(ValidationError) as cm:
                resource.full_clean()
            self.assertIn("email", cm.exception.error_dict)

    def test_website_validation(self):
        """Test website URL validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://www.example.org",
            "https://subdomain.example.co.uk/path",
            "https://example.com?param=value"
        ]
        for url in valid_urls:
            resource = Resource(
                name="Test Resource",
                website=url,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            resource.full_clean()  # Should not raise error

        # Invalid URLs
        invalid_urls = ["not-a-url", "javascript:alert('xss')", "ftp://", "http://"]
        for url in invalid_urls:
            resource = Resource(
                name="Test Resource",
                website=url,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            with self.assertRaises(ValidationError) as cm:
                resource.full_clean()
            self.assertIn("website", cm.exception.error_dict)

    def test_phone_validation(self):
        """Test phone number validation."""
        # Valid phone numbers
        valid_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "5551234567",
            "1-555-123-4567",
            "+1-555-123-4567"
        ]
        for phone in valid_phones:
            resource = Resource(
                name="Test Resource",
                phone=phone,
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            resource.full_clean()  # Should not raise error

        # Invalid phone numbers
        invalid_phones = ["123", "123456789012", "2-555-123-4567"]  # Too short, too long, invalid country code
        for phone in invalid_phones:
            resource = Resource(
                name="Test Resource",
                phone=phone,
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            with self.assertRaises(ValidationError) as cm:
                resource.full_clean()
            self.assertIn("phone", cm.exception.error_dict)

    def test_state_validation(self):
        """Test state code validation."""
        # Valid states
        valid_states = ["CA", "NY", "TX", "KY", "DC"]
        for state in valid_states:
            resource = Resource(
                name="Test Resource",
                state=state,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            resource.full_clean()  # Should not raise error

        # Invalid states
        invalid_states = ["XX", "ABC", "123"]
        for state in invalid_states:
            resource = Resource(
                name="Test Resource",
                state=state,
                phone="555-123-4567",  # Valid phone number
                status="draft",
                created_by=self.user,
                updated_by=self.user,
            )
            with self.assertRaises(ValidationError) as cm:
                resource.full_clean()
            self.assertIn("state", cm.exception.error_dict)

    def test_validation_methods(self):
        """Test individual validation methods."""
        resource = Resource()
        
        # Test phone validation
        self.assertEqual(resource._validate_phone_number("555-123-4567"), "")
        self.assertIn("at least 10 digits", resource._validate_phone_number("123"))
        
        # Test state validation
        self.assertEqual(resource._validate_state_code("CA"), "")
        self.assertIn("not a valid US state", resource._validate_state_code("XX"))
        
        # Test postal code validation
        self.assertEqual(resource._validate_postal_code("12345"), "")
        self.assertEqual(resource._validate_postal_code("12345-6789"), "")
        self.assertIn("must be 5 digits", resource._validate_postal_code("1234"))

    def test_needs_verification_property(self):
        """Test needs_verification property."""
        # Create resource with valid verification date
        resource = Resource.objects.create(
            name="Test Resource",
            phone="5551234",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),  # Valid
            last_verified_by=self.reviewer,
            source="Test Source",
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertFalse(resource.needs_verification)

        # Update to expired verification using raw SQL to bypass validation
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE directory_resource SET last_verified_at = %s WHERE id = %s",
                [timezone.now() - timedelta(days=200), resource.id]
            )
        
        # Refresh from database
        resource.refresh_from_db()
        
        self.assertTrue(resource.needs_verification)

    def test_has_contact_info_property(self):
        """Test has_contact_info property."""
        # Create a resource with contact info
        resource = Resource.objects.create(
            name="Test Resource",
            phone="5551234",  # Need at least one contact method for draft
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(resource.has_contact_info)

        # Test the property logic directly without saving invalid data
        # Create a new resource instance to test different contact scenarios
        resource_no_contact = Resource(
            name="Test Resource",
            phone="",
            email="",
            website="",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertFalse(resource_no_contact.has_contact_info)

        # Test with phone
        resource_with_phone = Resource(
            name="Test Resource",
            phone="5551234",
            email="",
            website="",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(resource_with_phone.has_contact_info)

        # Test with email
        resource_with_email = Resource(
            name="Test Resource",
            phone="",
            email="test@example.com",
            website="",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(resource_with_email.has_contact_info)

        # Test with website
        resource_with_website = Resource(
            name="Test Resource",
            phone="",
            email="",
            website="https://example.com",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(resource_with_website.has_contact_info)


class ServiceTypeModelTestCase(BaseTestCase):
    """Test cases for ServiceType model."""

    def test_service_type_creation(self):
        """Test basic service type creation."""
        service_type = ServiceType.objects.create(
            name="Mental Health Services",
            slug="mental-health",
            description="Mental health and counseling services"
        )
        
        self.assertEqual(service_type.name, "Mental Health Services")
        self.assertEqual(service_type.slug, "mental-health")
        self.assertEqual(str(service_type), "Mental Health Services")

    def test_service_type_with_resources(self):
        """Test service type relationship with resources."""
        service_type = ServiceType.objects.create(
            name="Food Assistance",
            slug="food-assistance"
        )
        
        resource = Resource.objects.create(
            name="Food Bank",
            phone="555-1234",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        resource.service_types.add(service_type)
        
        self.assertIn(service_type, resource.service_types.all())
        self.assertIn(resource, service_type.resources.all())


class ResourceManagerTestCase(BaseTestCase):
    """Test cases for ResourceManager."""

    def setUp(self):
        """Set up test data for manager tests."""
        super().setUp()
        
        # Create some test resources
        self.resource1 = Resource.objects.create(
            name="Crisis Intervention Center",
            description="24/7 crisis intervention services",
            phone="555-123-4567",  # Valid phone number
            city="London",
            state="KY",
            status="published",
            last_verified_at=timezone.now(),  # Required for published
            last_verified_by=self.user,  # Required for published
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.resource2 = Resource.objects.create(
            name="Mental Health Services",
            description="Mental health counseling and therapy",
            phone="555-567-8901",  # Valid phone number
            city="Corbin",
            state="KY",
            status="published",
            last_verified_at=timezone.now(),  # Required for published
            last_verified_by=self.user,  # Required for published
            created_by=self.user,
            updated_by=self.user,
        )

    def test_escape_fts_query_safe_input(self):
        """Test FTS query escaping with safe input."""
        manager = Resource.objects.__class__()
        
        # Safe queries should pass through
        safe_queries = ["mental health", "crisis intervention", "food assistance"]
        for query in safe_queries:
            escaped = manager._escape_fts_query(query)
            self.assertEqual(escaped, query)

    def test_escape_fts_query_dangerous_patterns(self):
        """Test FTS query escaping with dangerous patterns."""
        manager = Resource.objects.__class__()
        
        # Dangerous patterns should raise ValueError
        dangerous_queries = [
            "mental health; DROP TABLE resources;",
            "crisis intervention -- comment",
            "food assistance UNION ALL SELECT * FROM users",
            "mental health /* comment */",
            "crisis intervention; DELETE FROM resources;",
        ]
        
        for query in dangerous_queries:
            with self.assertRaises(ValueError) as cm:
                manager._escape_fts_query(query)
            self.assertIn("dangerous pattern", str(cm.exception))

    def test_escape_fts_query_too_long(self):
        """Test FTS query escaping with overly long queries."""
        manager = Resource.objects.__class__()
        
        # Query longer than 1000 characters should raise ValueError
        long_query = "a" * 1001
        with self.assertRaises(ValueError) as cm:
            manager._escape_fts_query(long_query)
        self.assertIn("too long", str(cm.exception))

    def test_escape_fts_query_quote_escaping(self):
        """Test FTS query escaping with quotes."""
        manager = Resource.objects.__class__()
        
        # Quotes should be properly escaped
        query_with_quotes = 'mental "health" services'
        escaped = manager._escape_fts_query(query_with_quotes)
        self.assertEqual(escaped, 'mental ""health"" services')

    def test_default_queryset_excludes_archived_deleted(self):
        """Test that default queryset excludes archived and deleted resources."""
        # Create archived and deleted resources
        archived_resource = Resource.objects.create(
            name="Archived Resource",
            phone="555-999-9999",  # Valid phone number
            status="published",
            last_verified_at=timezone.now(),  # Required for published
            last_verified_by=self.user,  # Required for published
            is_archived=True,
            archived_at=timezone.now(),  # Required for archived
            archived_by=self.user,  # Required for archived
            archive_reason="Test archiving",  # Required for archived
            created_by=self.user,
            updated_by=self.user,
        )
        
        deleted_resource = Resource.objects.create(
            name="Deleted Resource",
            phone="555-888-8888",  # Valid phone number
            status="published",
            last_verified_at=timezone.now(),  # Required for published
            last_verified_by=self.user,  # Required for published
            is_deleted=True,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Default queryset should exclude both
        all_resources = Resource.objects.all()
        self.assertNotIn(archived_resource, all_resources)
        self.assertNotIn(deleted_resource, all_resources)
        
        # But they should be included in the all_including_archived method
        all_including_archived = Resource.objects.all_including_archived()
        self.assertIn(archived_resource, all_including_archived)
        self.assertNotIn(deleted_resource, all_including_archived)  # Still excludes deleted


class TaxonomyCategoryModelTestCase(BaseTestCase):
    """Test cases for TaxonomyCategory model."""

    def test_category_creation(self):
        """Test basic category creation."""
        category = TaxonomyCategory.objects.create(
            name="Housing",
            slug="housing",
            description="Housing and shelter services"
        )
        
        self.assertEqual(category.name, "Housing")
        self.assertEqual(category.slug, "housing")
        self.assertEqual(str(category), "Housing")

    def test_category_with_resources(self):
        """Test category relationship with resources."""
        category = TaxonomyCategory.objects.create(
            name="Emergency Services",
            slug="emergency-services"
        )
        
        resource = Resource.objects.create(
            name="Emergency Shelter",
            category=category,
            phone="555-1234",
            status="draft",
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(resource.category, category)
        self.assertIn(resource, category.resources.all())
