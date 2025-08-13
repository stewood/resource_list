#!/usr/bin/env python
"""
Simple test to debug archive functionality.
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
from django.utils import timezone

def test_archive_basic():
    """Test basic archive functionality."""
    print("Testing Basic Archive Functionality...")
    
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
        name='Test Resource for Basic Archive',
        defaults={
            'description': 'This is a test resource for basic archive testing.',
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
    print(f"Resource is_deleted: {resource.is_deleted}")
    
    # Test 1: Check ResourceManager methods
    print(f"\nTest 1: ResourceManager methods")
    active_resources = Resource.objects.all()
    archived_resources = Resource.objects.archived()
    all_including_archived = Resource.objects.all_including_archived()
    
    print(f"Active resources count: {active_resources.count()}")
    print(f"Archived resources count: {archived_resources.count()}")
    print(f"All resources count: {all_including_archived.count()}")
    
    # Test 2: Archive the resource manually
    print(f"\nTest 2: Archive resource manually")
    resource.is_archived = True
    resource.archived_at = timezone.now()
    resource.archived_by = admin_user
    resource.archive_reason = "Testing basic archive functionality"
    resource.updated_by = admin_user
    
    try:
        resource.save()
        print("✓ Resource saved successfully")
    except Exception as e:
        print(f"✗ Error saving resource: {e}")
        return
    
    # Refresh from database
    resource.refresh_from_db()
    print(f"Resource archived: {resource.is_archived}")
    print(f"Archive reason: {resource.archive_reason}")
    
    # Test 3: Check ResourceManager after archiving
    print(f"\nTest 3: ResourceManager after archiving")
    active_resources = Resource.objects.all()
    archived_resources = Resource.objects.archived()
    all_including_archived = Resource.objects.all_including_archived()
    
    print(f"Active resources count: {active_resources.count()}")
    print(f"Archived resources count: {archived_resources.count()}")
    print(f"All resources count: {all_including_archived.count()}")
    
    # Test 4: Unarchive the resource
    print(f"\nTest 4: Unarchive resource")
    resource.is_archived = False
    resource.archived_at = None
    resource.archived_by = None
    resource.archive_reason = ""
    resource.updated_by = admin_user
    
    try:
        resource.save()
        print("✓ Resource unarchived successfully")
    except Exception as e:
        print(f"✗ Error unarchiving resource: {e}")
        return
    
    # Refresh from database
    resource.refresh_from_db()
    print(f"Resource unarchived: {not resource.is_archived}")
    
    print(f"\n🎉 Basic archive functionality test passed!")

if __name__ == '__main__':
    test_archive_basic()
