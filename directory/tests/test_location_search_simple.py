"""
Simple Location Search Tests

This module contains simplified tests for the location search functionality
that focus on core features without complex spatial data setup.
"""

import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone

from ..models import (
    Resource, TaxonomyCategory, ServiceType, CoverageArea,
    LocationSearchLog, SearchAnalytics
)
from ..services.geocoding import GeocodingResult


class SimpleLocationSearchTests(TestCase):
    """Simple tests for location search functionality."""
    
    def setUp(self):
        """Set up basic test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = TaxonomyCategory.objects.create(
            name='Test Category',
            description='Test category for testing'
        )
        
        # Create test service type
        self.service_type = ServiceType.objects.create(
            name='Test Service',
            description='Test service type'
        )
        
        # Create a simple coverage area (without complex geometry)
        self.coverage_area = CoverageArea.objects.create(
            name='Test Coverage Area',
            kind='STATE',
            ext_ids={'state_fips': '21', 'state_name': 'Kentucky'},
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test resource
        self.resource = Resource.objects.create(
            name='Test Resource',
            description='Test resource for testing',
            city='London',
            state='KY',
            status='published',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
            last_verified_by=self.user,
            last_verified_at=timezone.now()
        )
        
        # Create client
        self.client = Client()
    
    def test_search_analytics_logging(self):
        """Test that search analytics are properly logged."""
        initial_count = LocationSearchLog.objects.count()
        
        # Perform a search
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify search was logged
        self.assertEqual(LocationSearchLog.objects.count(), initial_count + 1)
        
        log = LocationSearchLog.objects.latest('created_at')
        self.assertEqual(log.address, 'London, KY')
        self.assertEqual(log.lat, 37.1283343)
        self.assertEqual(log.lon, -84.0835576)
        self.assertEqual(log.radius_miles, 10.0)
        self.assertTrue(log.geocoding_success)
        self.assertGreater(log.results_count, 0)
        self.assertGreater(log.search_duration_ms, 0)
    
    def test_popular_locations_analytics(self):
        """Test popular locations analytics functionality."""
        # Create multiple searches for the same location
        for _ in range(5):
            LocationSearchLog.log_search(
                address='London, KY',
                lat=37.1283343,
                lon=-84.0835576,
                radius_miles=10.0,
                results_count=1
            )
        
        # Create searches for another location
        for _ in range(3):
            LocationSearchLog.log_search(
                address='Lexington, KY',
                lat=38.0406,
                lon=-84.5037,
                radius_miles=10.0,
                results_count=1
            )
        
        # Get popular locations
        popular = LocationSearchLog.get_popular_locations(days=30, limit=5)
        
        self.assertGreater(len(popular), 0)
        # London, KY should be more popular than Lexington, KY
        london_count = next((item['count'] for item in popular if item['address'] == 'London, KY'), 0)
        lexington_count = next((item['count'] for item in popular if item['address'] == 'Lexington, KY'), 0)
        self.assertGreater(london_count, lexington_count)
    
    def test_geocoding_stats(self):
        """Test geocoding statistics functionality."""
        # Create successful searches
        for _ in range(8):
            LocationSearchLog.log_search(
                address='London, KY',
                lat=37.1283343,
                lon=-84.0835576,
                geocoding_success=True
            )
        
        # Create failed searches
        for _ in range(2):
            LocationSearchLog.log_search(
                address='Invalid Address',
                geocoding_success=False
            )
        
        # Get geocoding stats
        stats = LocationSearchLog.get_geocoding_stats(days=30)
        
        self.assertEqual(stats['total_searches'], 10)
        self.assertEqual(stats['successful_geocoding'], 8)
        self.assertEqual(stats['failed_geocoding'], 2)
        self.assertEqual(stats['success_rate'], 80.0)
    
    def test_location_search_api_basic(self):
        """Test basic location search API functionality."""
        response = self.client.get('/api/search/by-location/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('location', data)
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        
        # Check location data
        location = data['location']
        self.assertEqual(location['address'], 'London, KY')
        self.assertEqual(location['coordinates'], [37.1283343, -84.0835576])
        self.assertFalse(location['geocoded'])  # We provided coordinates
    
    def test_autocomplete_suggestions(self):
        """Test autocomplete suggestions functionality."""
        response = self.client.get('/api/search/by-location/', {
            'address': 'London',
            'suggestions': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('suggestions', data)
        suggestions = data['suggestions']
        self.assertIsInstance(suggestions, list)
        
        # Check that suggestions have required fields
        if suggestions:
            suggestion = suggestions[0]
            self.assertIn('address', suggestion)
            self.assertIn('type', suggestion)
    
    def test_search_performance(self):
        """Test that searches complete within reasonable time."""
        import time
        
        start_time = time.time()
        
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Search should complete within 2 seconds
        self.assertLess(duration, 2.0)
        
        # Verify performance was logged
        log = LocationSearchLog.objects.latest('created_at')
        self.assertGreater(log.search_duration_ms, 0)
        self.assertLess(log.search_duration_ms, 2000)  # Less than 2 seconds
    
    def test_invalid_address_handling(self):
        """Test handling of invalid addresses."""
        response = self.client.get('/resources/', {
            'address': 'Invalid Address XYZ',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should handle gracefully without crashing
        
        # Verify search was logged
        log = LocationSearchLog.objects.latest('created_at')
        self.assertEqual(log.address, 'Invalid Address XYZ')
        self.assertFalse(log.geocoding_success)
    
    def test_different_radius_values(self):
        """Test location search with different radius values."""
        # Test with small radius
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Test with large radius
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '50'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_text_filter(self):
        """Test combining location search with text search."""
        response = self.client.get('/resources/', {
            'q': 'Test Resource',
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource')
    
    def test_search_with_category_filter(self):
        """Test combining location search with category filtering."""
        response = self.client.get('/resources/', {
            'category': str(self.category.id),
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource')
    
    def test_api_error_handling(self):
        """Test API error handling."""
        # Test with invalid coordinates
        response = self.client.get('/api/search/by-location/', {
            'lat': '999',  # Invalid latitude
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        
        # Test with missing required parameters
        response = self.client.get('/api/search/by-location/', {
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
