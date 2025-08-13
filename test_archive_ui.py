#!/usr/bin/env python
"""
Test script to verify archive UI functionality.
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

def test_archive_ui():
    """Test the archive UI functionality."""
    print("Testing Archive UI Functionality...")
    
    # Create test admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@example.com'
        }
    )
    # Always set the password to ensure we know it
    admin_user.set_password('adminpass123')
    admin_user.save()
    if created:
        print(f"Created admin user: {admin_user.username}")
    else:
        print(f"Using existing admin user: {admin_user.username}")
    
    # Create admin group and assign user
    admin_group, created = Group.objects.get_or_create(name='Admin')
    admin_user.groups.add(admin_group)
    
    # Create test category
    category, created = TaxonomyCategory.objects.get_or_create(
        name='Test Category',
        defaults={'slug': 'test-category'}
    )
    if created:
        print(f"Created test category: {category.name}")
    
    # Create test service type
    service_type, created = ServiceType.objects.get_or_create(
        name='Test Service',
        defaults={'slug': 'test-service'}
    )
    if created:
        print(f"Created test service type: {service_type.name}")
    
    # Create test resource
    resource, created = Resource.objects.get_or_create(
        name='Test Resource for Archive UI',
        defaults={
            'description': 'This is a test resource for testing archive UI functionality.',
            'city': 'Test City',
            'state': 'CA',
            'phone': '5551234',
            'status': 'draft',
            'category': category,
            'created_by': admin_user,
            'updated_by': admin_user,
        }
    )
    if created:
        resource.service_types.add(service_type)
        print(f"Created test resource: {resource.name}")
    else:
        print(f"Using existing test resource: {resource.name}")
    
    # Debug: Check resource status
    print(f"Resource ID: {resource.pk}")
    print(f"Resource is_archived: {resource.is_archived}")
    print(f"Resource is_deleted: {resource.is_deleted}")
    print(f"Resource status: {resource.status}")
    
    # Create test client
    client = Client()
    
    # Test 1: Login as admin
    print(f"\nTest 1: Login as admin")
    login_successful = client.login(username='admin', password='adminpass123')
    print(f"Login successful: {login_successful}")
    assert login_successful, "Admin login should be successful"
    
    # Test 2: Archive the resource directly via POST
    print(f"\nTest 2: Archive resource via POST")
    archive_url = reverse('directory:archive_resource', args=[resource.pk])
    print(f"Archive URL: {archive_url}")
    response = client.post(archive_url, {
        'archive_reason': 'Testing archive UI functionality'
    })
    print(f"Archive POST status code: {response.status_code}")
    print(f"Archive response: {response.content.decode('utf-8')}")
    assert response.status_code == 200, "Archive POST should be successful"
    
    # Refresh resource from database
    resource.refresh_from_db()
    print(f"Resource archived: {resource.is_archived}")
    assert resource.is_archived, "Resource should be archived"
    
    # Test 3: Access archive list page
    print(f"\nTest 3: Access archive list page")
    archive_list_url = reverse('directory:archive_list')
    response = client.get(archive_list_url)
    print(f"Archive list page status code: {response.status_code}")
    assert response.status_code == 200, "Archive list page should be accessible"
    
    # Check that resource appears in archive list
    content = response.content.decode('utf-8')
    resource_in_archive = resource.name in content
    print(f"Resource in archive list: {resource_in_archive}")
    assert resource_in_archive, "Resource should appear in archive list"
    
    # Test 4: Unarchive the resource
    print(f"\nTest 4: Unarchive resource")
    unarchive_url = reverse('directory:unarchive_resource', args=[resource.pk])
    response = client.post(unarchive_url)
    print(f"Unarchive POST status code: {response.status_code}")
    print(f"Unarchive response: {response.content.decode('utf-8')}")
    assert response.status_code == 200, "Unarchive POST should be successful"
    
    # Refresh resource from database
    resource.refresh_from_db()
    print(f"Resource unarchived: {not resource.is_archived}")
    assert not resource.is_archived, "Resource should be unarchived"
    
    print(f"\n🎉 All archive UI tests passed!")
    
    # Clean up
    print(f"\nCleaning up test data...")
    try:
        resource.is_deleted = True
        resource.save()
        print("✓ Test resource marked as deleted")
    except Exception as e:
        print(f"Note: Could not delete resource: {e}")
    
    try:
        category.delete()
        print("✓ Test category deleted")
    except Exception as e:
        print(f"Note: Could not delete category: {e}")
    
    try:
        service_type.delete()
        print("✓ Test service type deleted")
    except Exception as e:
        print(f"Note: Could not delete service type: {e}")
    
    try:
        admin_user.delete()
        print("✓ Admin user deleted")
    except Exception as e:
        print(f"Note: Could not delete admin user: {e}")
    
    try:
        admin_group.delete()
        print("✓ Admin group deleted")
    except Exception as e:
        print(f"Note: Could not delete admin group: {e}")
    
    print("✓ Test data cleanup completed")

if __name__ == '__main__':
    test_archive_ui()
