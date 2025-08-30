"""
Tests for AI Auto Verification API

This module contains tests for the automated AI verification functionality
that applies AI-suggested changes and marks resources for review.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock

from ..models import Resource, TaxonomyCategory, ServiceType


class AIAutoVerificationAPITest(TestCase):
    """Test cases for AI Auto Verification API."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
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
        
        # Create test resource
        self.resource = Resource.objects.create(
            name='Test Resource',
            description='A test resource for AI verification',
            category=self.category,
            phone='555-123-4567',
            email='test@resource.com',
            website='https://testresource.com',
            address1='123 Test St',
            city='Test City',
            state='KY',
            postal_code='12345',
            status='draft',
            source='Test source',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add service type to resource
        self.resource.service_types.add(self.service_type)
        
        # Set up client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_ai_auto_verification_api_requires_authentication(self):
        """Test that AI auto verification API requires authentication."""
        # Create client without authentication
        client = Client()
        
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        response = client.post(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_ai_auto_verification_api_with_nonexistent_resource(self):
        """Test AI auto verification API with nonexistent resource."""
        url = reverse('directory:api_ai_auto_verification', args=[99999])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['status'], 'not_found')
    
    @patch('directory.services.ai.core.review_service.AIReviewService')
    def test_ai_auto_verification_api_success(self, mock_ai_service):
        """Test successful AI auto verification."""
        # Mock AI service
        mock_service_instance = MagicMock()
        mock_ai_service.return_value = mock_service_instance
        mock_service_instance.is_available.return_value = True
        
        # Mock AI verification result
        mock_verification_result = {
            'verified_data': {
                'name': 'Updated Test Resource',
                'phone': '555-987-6543',
                'email': 'updated@resource.com',
                'website': 'https://updatedresource.com',
                'description': 'An updated test resource description'
            },
            'confidence_scores': {
                'name': 90.0,
                'phone': 85.0,
                'email': 95.0,
                'website': 88.0,
                'description': 92.0
            },
            'report': 'AI verification completed successfully',
            'ai_response': 'Mock AI response'
        }
        mock_service_instance.verify_resource_data.return_value = mock_verification_result
        
        # Make API request
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['resource_id'], self.resource.pk)
        self.assertEqual(response_data['new_status'], 'needs_review')
        self.assertGreater(response_data['changes_applied'], 0)
        self.assertIn('verification_report', response_data)
        self.assertIn('audit_log_id', response_data)
        
        # Check that resource was updated
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, 'needs_review')
        self.assertEqual(self.resource.name, 'Updated Test Resource')
        self.assertEqual(self.resource.phone, '555-987-6543')
        self.assertEqual(self.resource.email, 'updated@resource.com')
        self.assertEqual(self.resource.website, 'https://updatedresource.com')
        self.assertEqual(self.resource.description, 'An updated test resource description')
    
    @patch('directory.services.ai.core.review_service.AIReviewService')
    def test_ai_auto_verification_api_service_unavailable(self, mock_ai_service):
        """Test AI auto verification when AI service is unavailable."""
        # Mock AI service as unavailable
        mock_service_instance = MagicMock()
        mock_ai_service.return_value = mock_service_instance
        mock_service_instance.is_available.return_value = False
        
        # Make API request
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, 503)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'unavailable')
        self.assertIn('error', response_data)
        self.assertIn('OPENROUTER_API_KEY', response_data['details'])
        
        # Check that resource was not changed
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, 'draft')  # Should remain unchanged
    
    @patch('directory.services.ai.core.review_service.AIReviewService')
    def test_ai_auto_verification_api_no_changes(self, mock_ai_service):
        """Test AI auto verification when no changes are needed."""
        # Mock AI service
        mock_service_instance = MagicMock()
        mock_ai_service.return_value = mock_service_instance
        mock_service_instance.is_available.return_value = True
        
        # Mock AI verification result with no changes
        mock_verification_result = {
            'verified_data': {
                'name': self.resource.name,  # Same as current
                'phone': self.resource.phone,  # Same as current
                'email': self.resource.email,  # Same as current
            },
            'confidence_scores': {
                'name': 95.0,
                'phone': 90.0,
                'email': 92.0,
            },
            'report': 'No changes needed - data is already accurate',
            'ai_response': 'Mock AI response'
        }
        mock_service_instance.verify_resource_data.return_value = mock_verification_result
        
        # Make API request
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['changes_applied'], 0)  # No changes applied
        self.assertEqual(response_data['new_status'], 'needs_review')
        
        # Check that resource status was updated even with no changes
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, 'needs_review')
    
    @patch('directory.services.ai.core.review_service.AIReviewService')
    def test_ai_auto_verification_api_verification_fails(self, mock_ai_service):
        """Test AI auto verification when AI verification fails."""
        # Mock AI service
        mock_service_instance = MagicMock()
        mock_ai_service.return_value = mock_service_instance
        mock_service_instance.is_available.return_value = True
        
        # Mock AI verification failure
        mock_service_instance.verify_resource_data.return_value = None
        
        # Make API request
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('error', response_data)
        
        # Check that resource was not changed
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.status, 'draft')  # Should remain unchanged
    
    def test_ai_auto_verification_api_url_pattern(self):
        """Test that AI auto verification URL pattern is correctly configured."""
        url = reverse('directory:api_ai_auto_verification', args=[self.resource.pk])
        expected_url = f'/manage/api/resources/{self.resource.pk}/ai-auto-verify/'
        self.assertEqual(url, expected_url)
