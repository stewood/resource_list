"""
Location Search Test Suite

This module contains comprehensive tests for the location search functionality,
including address geocoding, spatial filtering, autocomplete, and analytics.

Test Coverage:
    - Address geocoding with valid/invalid addresses
    - Spatial filtering with different radius values
    - Autocomplete functionality
    - Advanced filtering (coverage area types, distance ranges)
    - Search analytics tracking
    - Integration with existing features
    - Edge cases and error handling
"""

import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, MultiPolygon
from django.utils import timezone

from ..models import (
    Resource, TaxonomyCategory, ServiceType, CoverageArea,
    LocationSearchLog, SearchAnalytics
)
from ..services.geocoding import GeocodingResult


class LocationSearchTestCase(TestCase):
    """Base test case for location search functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test categories
        self.category = TaxonomyCategory.objects.create(
            name='Test Category',
            description='Test category for testing'
        )
        
        # Create test service types
        self.service_type = ServiceType.objects.create(
            name='Test Service',
            description='Test service type'
        )
        
        # Create test coverage areas
        self.state_area = CoverageArea.objects.create(
            name='Kentucky',
            kind='STATE',
            geom=MultiPolygon(Point(-84.5, 37.5).buffer(2.0)),
            ext_ids={'state_fips': '21', 'state_name': 'Kentucky'},
            created_by=self.user,
            updated_by=self.user
        )
        
        self.county_area = CoverageArea.objects.create(
            name='Laurel County',
            kind='COUNTY',
            geom=MultiPolygon(Point(-84.1, 37.1).buffer(0.5)),
            ext_ids={'state_fips': '21', 'county_fips': '125', 'county_name': 'Laurel County'},
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city_area = CoverageArea.objects.create(
            name='London',
            kind='CITY',
            geom=MultiPolygon(Point(-84.08, 37.13).buffer(0.1)),
            ext_ids={'state_fips': '21', 'city_name': 'London', 'state_name': 'Kentucky'},
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test resources
        self.resource1 = Resource.objects.create(
            name='Test Resource 1',
            description='Test resource in London, KY',
            city='London',
            state='KY',
            status='published',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
            last_verified_by=self.user,
            last_verified_at=timezone.now()
        )
        self.resource1.coverage_areas.add(self.state_area, self.county_area, self.city_area)
        self.resource1.service_types.add(self.service_type)
        
        self.resource2 = Resource.objects.create(
            name='Test Resource 2',
            description='Test resource in Lexington, KY',
            city='Lexington',
            state='KY',
            status='published',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
            last_verified_by=self.user,
            last_verified_at=timezone.now()
        )
        self.resource2.coverage_areas.add(self.state_area)
        
        self.resource3 = Resource.objects.create(
            name='Test Resource 3',
            description='Test resource in Louisville, KY',
            city='Louisville',
            state='KY',
            status='published',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
            last_verified_by=self.user,
            last_verified_at=timezone.now()
        )
        self.resource3.coverage_areas.add(self.state_area)
        
        # Create client
        self.client = Client()


class LocationSearchFunctionalTests(LocationSearchTestCase):
    """Test location search functional features."""
    
    @patch('directory.services.geocoding.NominatimGeocoder.geocode')
    def test_valid_address_search(self, mock_geocode):
        """Test location search with valid addresses."""
        # Mock geocoding response
        mock_geocode.return_value = GeocodingResult(
            address="London, KY",
            latitude=37.1283343,
            longitude=-84.0835576,
            provider="nominatim"
        )
        
        # Test city search
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
        self.assertContains(response, 'London, KY')
        
        # Verify search was logged
        self.assertEqual(LocationSearchLog.objects.count(), 1)
        log = LocationSearchLog.objects.first()
        self.assertEqual(log.address, 'London, KY')
        self.assertEqual(log.results_count, 1)
        self.assertTrue(log.geocoding_success)
    
    @patch('directory.services.geocoding.NominatimGeocoder.geocode')
    def test_invalid_address_search(self, mock_geocode):
        """Test location search with invalid addresses."""
        # Mock geocoding failure
        mock_geocode.return_value = None
        
        response = self.client.get('/resources/', {
            'address': 'Invalid Address XYZ',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should fall back to text-based search
        self.assertContains(response, 'Invalid Address XYZ')
        
        # Verify search was logged
        self.assertEqual(LocationSearchLog.objects.count(), 1)
        log = LocationSearchLog.objects.first()
        self.assertEqual(log.address, 'Invalid Address XYZ')
        self.assertFalse(log.geocoding_success)
    
    def test_different_radius_values(self):
        """Test location search with different radius values."""
        # Test with coordinates (no geocoding needed)
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Test with larger radius
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '50'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_edge_cases(self):
        """Test location search with edge cases."""
        # Test with rural area coordinates
        response = self.client.get('/resources/', {
            'address': 'Rural Area',
            'lat': '37.0',
            'lon': '-84.0',
            'radius_miles': '100'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Test with international coordinates (should still work)
        response = self.client.get('/resources/', {
            'address': 'International Location',
            'lat': '51.5074',
            'lon': '-0.1278',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)


class LocationSearchIntegrationTests(LocationSearchTestCase):
    """Test location search integration with existing features."""
    
    def test_location_text_search_combination(self):
        """Test combining location search with text search."""
        response = self.client.get('/resources/', {
            'q': 'Test Resource',
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
    
    def test_location_category_filtering(self):
        """Test combining location search with category filtering."""
        response = self.client.get('/resources/', {
            'category': str(self.category.id),
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
    
    def test_location_service_type_filtering(self):
        """Test combining location search with service type filtering."""
        response = self.client.get('/resources/', {
            'service_type': str(self.service_type.id),
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
    
    def test_location_emergency_filtering(self):
        """Test combining location search with emergency service filtering."""
        # Make resource1 an emergency service
        self.resource1.is_emergency_service = True
        self.resource1.save()
        
        response = self.client.get('/resources/', {
            'emergency': 'true',
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')


class AdvancedFilteringTests(LocationSearchTestCase):
    """Test advanced location filtering features."""
    
    def test_coverage_area_type_filtering(self):
        """Test filtering by coverage area type."""
        # Test county-level filtering
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10',
            'coverage_area_type': 'COUNTY'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
        
        # Test state-level filtering
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10',
            'coverage_area_type': 'STATE'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resource 1')
        self.assertContains(response, 'Test Resource 2')
        self.assertContains(response, 'Test Resource 3')
    
    def test_distance_range_filtering(self):
        """Test distance range filtering."""
        # Test maximum distance filtering
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10',
            'max_distance': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Test minimum distance filtering
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10',
            'min_distance': '1'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Test both min and max distance
        response = self.client.get('/resources/', {
            'address': 'London, KY',
            'lat': '37.1283343',
            'lon': '-84.0835576',
            'radius_miles': '10',
            'min_distance': '1',
            'max_distance': '5'
        })
        
        self.assertEqual(response.status_code, 200)


class AutocompleteTests(LocationSearchTestCase):
    """Test autocomplete functionality."""
    
    def test_autocomplete_suggestions(self):
        """Test address autocomplete suggestions."""
        response = self.client.get('/api/search/by-location/', {
            'address': 'London',
            'suggestions': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        self.assertGreater(len(data['suggestions']), 0)
        
        # Check that London, KY is in suggestions
        addresses = [s['address'] for s in data['suggestions']]
        self.assertIn('London, KY', addresses)
    
    def test_autocomplete_with_no_matches(self):
        """Test autocomplete with no matching suggestions."""
        response = self.client.get('/api/search/by-location/', {
            'address': 'XYZ123',
            'suggestions': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        # Should return empty suggestions list


class SearchAnalyticsTests(LocationSearchTestCase):
    """Test search analytics functionality."""
    
    def test_search_logging(self):
        """Test that searches are properly logged."""
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
    
    def test_popular_locations(self):
        """Test popular locations analytics."""
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
        """Test geocoding statistics."""
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


class APITests(LocationSearchTestCase):
    """Test location search API endpoints."""
    
    def test_location_search_api(self):
        """Test the location search API endpoint."""
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
        
        # Check results
        results = data['results']
        self.assertGreater(len(results), 0)
        
        # Check pagination
        pagination = data['pagination']
        self.assertIn('page', pagination)
        self.assertIn('page_size', pagination)
        self.assertIn('total_count', pagination)
        self.assertIn('total_pages', pagination)
    
    def test_location_search_api_with_suggestions(self):
        """Test the location search API with suggestions."""
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
    
    def test_location_search_api_error_handling(self):
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


class PerformanceTests(LocationSearchTestCase):
    """Test location search performance."""
    
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
    
    def test_large_result_set_performance(self):
        """Test performance with large result sets."""
        # Create many resources to test performance
        for i in range(50):
            resource = Resource.objects.create(
                name=f'Test Resource {i}',
                description=f'Test resource {i}',
                city='London',
                state='KY',
                status='published',
                category=self.category
            )
            resource.coverage_areas.add(self.state_area, self.county_area)
        
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
        # Should still complete within reasonable time
        self.assertLess(duration, 3.0)
