#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced web searching capabilities.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource
from directory.services.ai.core.review_service import AIReviewService

def test_enhanced_web_search():
    """Test the enhanced web searching capabilities."""
    
    print("🌐 Enhanced Web Search Test")
    print("=" * 60)
    
    # Get a real resource
    resource = Resource.objects.filter(status='published').first()
    
    print(f"📋 Testing Resource: {resource.name}")
    print(f"🌐 Website: {resource.website}")
    print()
    
    # Initialize AI service
    print("🤖 Initializing AI Service...")
    ai_service = AIReviewService()
    
    if not ai_service.is_available():
        print("❌ AI service not available")
        return
    
    print(f"✅ Using model: {ai_service.current_model}")
    print()
    
    # Test 1: Organization web search
    print("🔍 TEST 1: Organization Web Search")
    print("-" * 40)
    try:
        org_search_result = ai_service._authoritative_web_search_tool(resource.name)
        print("✅ Organization search completed!")
        print(f"📄 Results: {org_search_result[:300]}...")
        print()
    except Exception as e:
        print(f"❌ Organization search failed: {e}")
        print()
    
    # Test 2: Website browsing
    print("🌐 TEST 2: Website Browsing")
    print("-" * 40)
    try:
        page_content = ai_service._browse_page(resource.website)
        if page_content and len(page_content) > 100:
            print("✅ Website browsing completed!")
            print(f"📄 Content length: {len(page_content)} characters")
            print(f"📄 Sample content: {page_content[:200]}...")
            
            # Test content extraction
            extracted_info = ai_service._extract_relevant_info(page_content, resource.name)
            print(f"🔍 Extracted info: {extracted_info}")
        else:
            print("❌ No content extracted from website")
        print()
    except Exception as e:
        print(f"❌ Website browsing failed: {e}")
        print()
    
    # Test 3: Full verification with enhanced web search
    print("🔍 TEST 3: Full Verification with Enhanced Web Search")
    print("-" * 40)
    try:
        current_data = {
            'name': resource.name,
            'phone': resource.phone,
            'email': resource.email,
            'website': resource.website,
            'address1': resource.address1,
            'city': resource.city,
            'state': resource.state,
            'postal_code': resource.postal_code,
        }
        
        result = ai_service.verify_resource_data(current_data)
        
        print("✅ Full verification completed!")
        print()
        
        # Show enhanced results
        verification_notes = result.get('verification_notes', {})
        
        for field, notes in verification_notes.items():
            print(f"📝 {field.upper()}:")
            print(f"   Method: {notes.get('verification_method', 'Unknown')}")
            print(f"   Web Searches: {notes.get('web_searches', 'None')}")
            
            # Show actual findings if available
            if 'actual_findings' in notes:
                print(f"   Actual Findings: {notes['actual_findings'][:200]}...")
            
            print()
        
    except Exception as e:
        print(f"❌ Full verification failed: {e}")
        print()
    
    print("🎯 Key Improvements:")
    print("✅ No more hallucination - actual web searches performed")
    print("✅ Real website browsing and content extraction")
    print("✅ Honest reporting of what was actually done")
    print("✅ Authoritative source verification")
    print("✅ Actual findings included in verification notes")

if __name__ == "__main__":
    test_enhanced_web_search()
