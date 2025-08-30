#!/usr/bin/env python3
"""
Test Script for AI Auto Verification API

This script demonstrates how to use the new AI Auto Verification API
to automatically apply AI-suggested changes to resources.

Usage:
    python scripts/development/test_ai_auto_verification.py [resource_id]

Example:
    python scripts/development/test_ai_auto_verification.py 123
"""

import os
import sys
import django
import requests
import json
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource


def test_ai_auto_verification_api(resource_id: int, base_url: str = "http://localhost:8000") -> None:
    """
    Test the AI Auto Verification API for a specific resource.
    
    Args:
        resource_id: The ID of the resource to test
        base_url: The base URL of the Django application
    """
    print(f"🤖 Testing AI Auto Verification API for Resource {resource_id}")
    print("=" * 60)
    
    # Check if resource exists
    try:
        resource = Resource.objects.get(pk=resource_id, is_deleted=False)
        print(f"✅ Found resource: {resource.name}")
        print(f"   Current status: {resource.status}")
        print(f"   Current data:")
        print(f"     - Name: {resource.name}")
        print(f"     - Phone: {resource.phone}")
        print(f"     - Email: {resource.email}")
        print(f"     - Website: {resource.website}")
        print()
    except Resource.DoesNotExist:
        print(f"❌ Resource {resource_id} not found")
        return
    
    # API endpoint
    api_url = f"{base_url}/api/resources/{resource_id}/ai-auto-verify/"
    
    print(f"🌐 Making API request to: {api_url}")
    print()
    
    try:
        # Make the API request
        response = requests.post(
            api_url,
            headers={
                'Content-Type': 'application/json',
                # Note: In a real scenario, you'd need proper authentication
                # For testing, you might need to handle authentication differently
            },
            timeout=30  # 30 second timeout
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            # Success response
            result = response.json()
            print("✅ AI Auto Verification Successful!")
            print()
            print("📊 Results:")
            print(f"   - Changes Applied: {result.get('changes_applied', 0)}")
            print(f"   - New Status: {result.get('new_status', 'unknown')}")
            print(f"   - Audit Log ID: {result.get('audit_log_id', 'N/A')}")
            print(f"   - Timestamp: {result.get('verification_timestamp', 'N/A')}")
            print()
            
            # Show confidence scores if available
            confidence_scores = result.get('confidence_scores', {})
            if confidence_scores:
                print("🎯 Confidence Scores:")
                for field, score in confidence_scores.items():
                    print(f"   - {field}: {score}")
                print()
            
            # Show verification report if available
            verification_report = result.get('verification_report', '')
            if verification_report:
                print("📋 Verification Report:")
                print(verification_report[:500] + "..." if len(verification_report) > 500 else verification_report)
                print()
            
            # Refresh resource data to show changes
            resource.refresh_from_db()
            print("🔄 Updated Resource Data:")
            print(f"   - Name: {resource.name}")
            print(f"   - Phone: {resource.phone}")
            print(f"   - Email: {resource.email}")
            print(f"   - Website: {resource.website}")
            print(f"   - Status: {resource.status}")
            
        elif response.status_code == 503:
            # AI service unavailable
            error_data = response.json()
            print("❌ AI Service Unavailable")
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
            print(f"   Details: {error_data.get('details', 'No details provided')}")
            print()
            print("💡 To fix this:")
            print("   1. Set the OPENROUTER_API_KEY environment variable")
            print("   2. Ensure the AI service is properly configured")
            
        elif response.status_code == 404:
            # Resource not found
            error_data = response.json()
            print("❌ Resource Not Found")
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
            
        elif response.status_code == 403:
            # Permission denied
            print("❌ Permission Denied")
            print("   You need to be authenticated to use this API")
            print()
            print("💡 To fix this:")
            print("   1. Log in to the application")
            print("   2. Ensure you have appropriate permissions")
            
        else:
            # Other error
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error")
        print("   Could not connect to the Django application")
        print()
        print("💡 To fix this:")
        print("   1. Ensure the Django development server is running")
        print("   2. Check that the base URL is correct")
        print("   3. Run: python manage.py runserver")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout Error")
        print("   The request timed out (AI verification took too long)")
        print()
        print("💡 This might be normal for the first AI verification")
        print("   as the AI service needs to warm up.")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")


def list_resources_for_testing() -> None:
    """List available resources for testing."""
    print("📋 Available Resources for Testing:")
    print("=" * 40)
    
    resources = Resource.objects.filter(is_deleted=False).order_by('id')[:10]
    
    if not resources:
        print("No resources found in the database.")
        print("Create some resources first using the Django admin interface.")
        return
    
    for resource in resources:
        print(f"   ID: {resource.id} | Name: {resource.name} | Status: {resource.status}")
    
    print()
    print("💡 Use one of these IDs to test the AI Auto Verification API")


def main():
    """Main function to run the test script."""
    print("🚀 AI Auto Verification API Test Script")
    print("=" * 50)
    print()
    
    # Check if resource ID was provided
    if len(sys.argv) > 1:
        try:
            resource_id = int(sys.argv[1])
            test_ai_auto_verification_api(resource_id)
        except ValueError:
            print("❌ Invalid resource ID. Please provide a valid integer.")
            print(f"   Usage: python {sys.argv[0]} [resource_id]")
    else:
        # No resource ID provided, show available resources
        list_resources_for_testing()
        print()
        print("💡 To test the API, run:")
        print(f"   python {sys.argv[0]} [resource_id]")
        print()
        print("   Example:")
        print(f"   python {sys.argv[0]} 1")


if __name__ == "__main__":
    main()
