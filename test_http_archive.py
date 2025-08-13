#!/usr/bin/env python
"""
Test HTTP request handling for archive functionality.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from django.contrib.auth.models import User, Group
from directory.models import Resource, TaxonomyCategory, ServiceType
from django.test import Client
from django.urls import reverse

def test_http_archive():
    """Test HTTP request handling for archive functionality."""
    print("Testing HTTP Archive Functionality...")
    
    # Create test admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@example.com'
        }
    )
    admin_user.set_password('adminpass123')
    admin_user.save()
    
    # Create admin group and assign user
    admin_group, created = Group.objects.get_or_create(name='Admin')
    admin_user.groups.add(admin_group)
    
    # Create test category
    category, created = TaxonomyCategory.objects.get_or_create(
        name='Test Category',
        defaults={'slug': 'test-category'}
    )
    
    # Create test resource
    resource, created = Resource.objects.get_or_create(
        name='Test Resource for HTTP Archive',
        defaults={
            'description': 'This is a test resource for HTTP archive testing.',
            'city': 'Test City',
            'state': 'CA',
            'phone': '5551234',
            'status': 'draft',
            'category': category,
            'created_by': admin_user,
            'updated_by': admin_user,
        }
    )
    
    print(f"Resource ID: {resource.pk}")
    print(f"Resource is_archived: {resource.is_archived}")
    
    # Create test client
    client = Client()
    
    # Test 1: Login as admin
    print(f"\nTest 1: Login as admin")
    login_successful = client.login(username='admin', password='adminpass123')
    print(f"Login successful: {login_successful}")
    assert login_successful, "Admin login should be successful"
    
    # Test 2: Test archive URL pattern
    print(f"\nTest 2: Test archive URL pattern")
    archive_url = reverse('directory:archive_resource', args=[resource.pk])
    print(f"Archive URL: {archive_url}")
    
    # Test 3: Test GET request to archive URL (should fail)
    print(f"\nTest 3: Test GET request to archive URL")
    response = client.get(archive_url)
    print(f"GET request status code: {response.status_code}")
    # Should be 405 Method Not Allowed since we only allow POST
    
    # Test 4: Test POST request without CSRF token (should fail)
    print(f"\nTest 4: Test POST request without CSRF token")
    response = client.post(archive_url, {
        'archive_reason': 'Testing HTTP archive functionality'
    }, follow=False)
    print(f"POST without CSRF status code: {response.status_code}")
    
    # Test 5: Test POST request with CSRF token
    print(f"\nTest 5: Test POST request with CSRF token")
    # First get a page to get CSRF token
    response = client.get('/admin/')
    csrf_token = response.cookies.get('csrftoken')
    print(f"CSRF token: {csrf_token}")
    
    if csrf_token:
        response = client.post(archive_url, {
            'archive_reason': 'Testing HTTP archive functionality'
        }, HTTP_X_CSRFTOKEN=csrf_token.value)
        print(f"POST with CSRF status code: {response.status_code}")
        print(f"POST with CSRF response: {response.content.decode('utf-8')}")
    else:
        print("No CSRF token found")
    
    # Test 6: Test with proper Django test client (which handles CSRF automatically)
    print(f"\nTest 6: Test with proper Django test client")
    response = client.post(archive_url, {
        'archive_reason': 'Testing HTTP archive functionality'
    })
    print(f"Proper POST status code: {response.status_code}")
    print(f"Proper POST response: {response.content.decode('utf-8')}")
    
    # Refresh resource from database
    resource.refresh_from_db()
    print(f"Resource archived: {resource.is_archived}")
    
    print(f"\n🎉 HTTP archive functionality test completed!")

if __name__ == '__main__':
    test_http_archive()
