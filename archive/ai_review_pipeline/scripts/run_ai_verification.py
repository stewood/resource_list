#!/usr/bin/env python3
import os
import sys
import django

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

# Now import Django modules
import json
import requests
from django.test import RequestFactory
from django.contrib.auth.models import User

from directory.models import Resource
from directory.services.ai.core.review_service import AIReviewService

def run_ai_verification(resource_id):
    try:
        # Get the resource
        resource = Resource.objects.get(id=resource_id)
        
        print(f"Running AI verification on resource: {resource.name}")
        print("=" * 60)
        
        # Prepare resource data for AI verification
        resource_data = {
            'name': resource.name,
            'description': resource.description,
            'category': resource.category.name if resource.category else None,
            'phone': resource.phone,
            'email': resource.email,
            'website': resource.website,
            'address1': resource.address1,
            'address2': resource.address2,
            'city': resource.city,
            'state': resource.state,
            'postal_code': resource.postal_code,
            'county': resource.county,
            'hours_of_operation': resource.hours_of_operation,
            'eligibility_requirements': resource.eligibility_requirements,
            'populations_served': resource.populations_served,
            'cost_information': resource.cost_information,
            'languages_available': resource.languages_available,
        }
        
        # Initialize AI service
        ai_service = AIReviewService()
        
        # Check if AI service is available
        if not ai_service.is_available():
            print("❌ AI service not available. Please check your OpenRouter API key configuration.")
            return None
        
        print("✅ AI service is available")
        print("🔄 Running AI verification...")
        
        # Run AI verification
        result = ai_service.verify_resource_data(resource_data)
        
        if result and result.get('verified_data'):
            print("✅ AI verification completed successfully!")
            print("\n" + "=" * 60)
            print("AI VERIFICATION RESULTS")
            print("=" * 60)
            
            # Print the full result
            print(json.dumps(result, indent=2, default=str))
            
            return result
        else:
            print("❌ AI verification failed or returned no results")
            if result:
                print(f"Error: {result.get('error', 'Unknown error')}")
            return None
            
    except Resource.DoesNotExist:
        print(f"❌ Resource with ID {resource_id} not found")
        return None
    except Exception as e:
        print(f"❌ Error during AI verification: {str(e)}")
        return None

if __name__ == "__main__":
    resource_id = int(sys.argv[1]) if len(sys.argv) > 1 else 344
    run_ai_verification(resource_id)
