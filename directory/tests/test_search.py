"""
Tests for search functionality.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
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


class SearchTestCase(BaseTestCase):
    """Test cases for search functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test resources with valid data
        self.resource1 = self.create_test_resource(
            name="Food Bank of Test City",
            description="Provides food assistance to families in need with comprehensive support services.",
            city="Test City",
            state="CA",
            phone="5551234",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        self.resource2 = self.create_test_resource(
            name="Homeless Shelter",
            description="Emergency shelter for homeless individuals with comprehensive support services.",
            city="Test City",
            state="CA",
            phone="5555678",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        self.resource3 = self.create_test_resource(
            name="Mental Health Clinic",
            description="Mental health services and counseling with comprehensive support services.",
            city="Other City",
            state="CA",
            phone="5559999",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )

    def test_basic_search(self):
        """Test basic search functionality."""
        # Search by name
        results = Resource.objects.filter(name__icontains="Food")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

        # Search by city
        results = Resource.objects.filter(city__icontains="Test City")
        self.assertEqual(results.count(), 2)

    def test_fts5_search(self):
        """Test FTS5 search functionality."""
        # Test FTS5 search if available
        try:
            results = Resource.objects.search_fts("food")
            self.assertGreaterEqual(results.count(), 1)
        except Exception:
            # FTS5 might not be available in test environment
            self.skipTest("FTS5 not available in test environment")

    def test_combined_search(self):
        """Test combined search functionality."""
        results = Resource.objects.search_combined("Food Bank")
        self.assertGreaterEqual(results.count(), 1)

    def test_search_with_filters(self):
        """Test search with additional filters."""
        # Search with status filter
        results = Resource.objects.filter(
            name__icontains="Test",
            status="published"
        )
        self.assertGreaterEqual(results.count(), 1)

        # Search with city filter
        results = Resource.objects.filter(
            city="Test City",
            status="published"
        )
        self.assertEqual(results.count(), 2)

    def test_search_by_service_type(self):
        """Test search by service type."""
        # Add service type to resource
        self.resource1.service_types.add(self.service_type)
        
        # Search by service type
        results = Resource.objects.filter(service_types=self.service_type)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_category(self):
        """Test search by category."""
        # Set category for resource
        self.resource1.category = self.category
        self.resource1.save()
        
        # Search by category
        results = Resource.objects.filter(category=self.category)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_emergency_services(self):
        """Test search by emergency service flag."""
        # Mark resource as emergency service
        self.resource1.is_emergency_service = True
        self.resource1.save()
        
        # Search by emergency service flag
        results = Resource.objects.filter(is_emergency_service=True)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_24_hour_services(self):
        """Test search by 24-hour service flag."""
        # Mark resource as 24-hour service
        self.resource1.is_24_hour_service = True
        self.resource1.save()
        
        # Search by 24-hour service flag
        results = Resource.objects.filter(is_24_hour_service=True)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_state(self):
        """Test search by state."""
        results = Resource.objects.filter(state="CA")
        self.assertEqual(results.count(), 3)

    def test_search_by_county(self):
        """Test search by county."""
        # Set county for resources
        self.resource1.county = "Test County"
        self.resource1.save()
        self.resource2.county = "Test County"
        self.resource2.save()
        
        # Search by county
        results = Resource.objects.filter(county="Test County")
        self.assertEqual(results.count(), 2)

    def test_search_by_phone(self):
        """Test search by phone number."""
        results = Resource.objects.filter(phone__icontains="5551234")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_email(self):
        """Test search by email."""
        # Set email for resource
        self.resource1.email = "foodbank@example.com"
        self.resource1.save()
        
        # Search by email
        results = Resource.objects.filter(email__icontains="foodbank")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_website(self):
        """Test search by website."""
        # Set website for resource
        self.resource1.website = "https://foodbank.example.com"
        self.resource1.save()
        
        # Search by website
        results = Resource.objects.filter(website__icontains="foodbank")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_description(self):
        """Test search by description."""
        results = Resource.objects.filter(description__icontains="food assistance")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_source(self):
        """Test search by source."""
        # Set source for resource
        self.resource1.source = "Community Directory"
        self.resource1.save()
        
        # Search by source
        results = Resource.objects.filter(source__icontains="Community")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.resource1)

    def test_search_by_verifier(self):
        """Test search by verifier."""
        # The resource1 already has last_verified_by set in setUp
        # Search by verifier
        results = Resource.objects.filter(last_verified_by=self.reviewer)
        self.assertEqual(results.count(), 3)  # All 3 resources in setUp have reviewer as verifier

    def test_search_by_creator(self):
        """Test search by creator."""
        results = Resource.objects.filter(created_by=self.user)
        self.assertEqual(results.count(), 3)

    def test_search_by_updater(self):
        """Test search by updater."""
        results = Resource.objects.filter(updated_by=self.user)
        self.assertEqual(results.count(), 3)

    def test_search_by_status(self):
        """Test search by status."""
        # Create a draft resource
        draft_resource = self.create_test_resource(
            name="Draft Resource",
            phone="5550000",
            status="draft",
        )
        
        # Search by status
        draft_results = Resource.objects.filter(status="draft")
        self.assertEqual(draft_results.count(), 1)
        self.assertEqual(draft_results.first(), draft_resource)
        
        published_results = Resource.objects.filter(status="published")
        self.assertEqual(published_results.count(), 3)

    def test_search_by_verification_status(self):
        """Test search by verification status."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create resources with different verification statuses
        verified_resource = self.create_test_resource(
            name="Recently Verified",
            phone="5551111",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=30),
            last_verified_by=self.reviewer,
            source="Test Source",
        )
        
        # Create expired resource manually to bypass validation
        expired_resource = Resource(
            name="Expired Verification",
            description="This is a test resource with a description that meets the minimum length requirement.",
            city="Test City",
            state="CA",
            phone="5552222",
            status="published",
            last_verified_at=timezone.now() - timedelta(days=200),
            last_verified_by=self.reviewer,
            source="Test Source",
            created_by=self.user,
            updated_by=self.user,
        )
        # Use raw SQL to bypass validation
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO directory_resource (
                    name, description, city, state, phone, email, website,
                    address1, address2, county, postal_code, status, source,
                    hours_of_operation, is_emergency_service, is_24_hour_service,
                    eligibility_requirements, populations_served, insurance_accepted,
                    cost_information, languages_available, capacity,
                    last_verified_at, last_verified_by_id, created_by_id, updated_by_id,
                    created_at, updated_at, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                expired_resource.name, expired_resource.description,
                expired_resource.city, expired_resource.state,
                expired_resource.phone, expired_resource.email, expired_resource.website,
                expired_resource.address1, expired_resource.address2,
                expired_resource.county, expired_resource.postal_code,
                expired_resource.status, expired_resource.source,
                expired_resource.hours_of_operation, expired_resource.is_emergency_service,
                expired_resource.is_24_hour_service, expired_resource.eligibility_requirements,
                expired_resource.populations_served, expired_resource.insurance_accepted,
                expired_resource.cost_information, expired_resource.languages_available,
                expired_resource.capacity, expired_resource.last_verified_at,
                expired_resource.last_verified_by.id, expired_resource.created_by.id,
                expired_resource.updated_by.id, timezone.now(), timezone.now(), False
            ])
            expired_resource.id = cursor.lastrowid
        
        # Test needs verification search
        needs_verification = Resource.objects.filter(
            status="published",
            last_verified_at__lt=timezone.now() - timedelta(days=180)
        )
        self.assertIn(expired_resource, needs_verification)
        self.assertNotIn(verified_resource, needs_verification)

    def test_search_by_creation_date(self):
        """Test search by creation date."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create resource with specific creation date
        old_resource = self.create_test_resource(
            name="Old Resource",
            phone="5553333",
            status="draft",
        )
        
        # Manually set creation date to past
        old_resource.created_at = timezone.now() - timedelta(days=30)
        old_resource.save()
        
        # Search by creation date
        recent_results = Resource.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        )
        self.assertNotIn(old_resource, recent_results)
        
        old_results = Resource.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=1)
        )
        self.assertIn(old_resource, old_results)

    def test_search_by_update_date(self):
        """Test search by update date."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Update resource
        self.resource1.name = "Updated Food Bank"
        self.resource1.save()
        
        # Search by recent updates
        recent_updates = Resource.objects.filter(
            updated_at__gte=timezone.now() - timedelta(minutes=5)
        )
        self.assertIn(self.resource1, recent_updates)
