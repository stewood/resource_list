#!/usr/bin/env python3
"""
Resource Verification Finder

This script finds the next resource that needs verification and displays
all available information to help with the verification process.

⚠️  PREREQUISITE: VIRTUAL ENVIRONMENT REQUIRED ⚠️
Before running this script, activate the virtual environment:
    source venv/bin/activate

⚠️  REMINDER: APPROVAL REQUIRED BEFORE MAKING CHANGES ⚠️
After finding a resource, you MUST present changes for approval before updating.

The script prioritizes:
1. Resources that have never been verified (no last_verified_at)
2. Resources with expired verification (past verification_frequency_days)
3. Resources with the lowest ID (for systematic coverage)

Usage:
    python find_next_verification.py

Author: Resource Directory Team
Created: 2025-01-15
"""

import os
import sys
import django
from datetime import datetime
from typing import Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource


def find_next_resource_for_verification() -> Optional[Resource]:
    """
    Find the next resource that needs verification.
    
    Priority order:
    1. Never verified (no last_verified_at)
    2. Expired verification (past verification_frequency_days)
    3. Lowest ID for systematic coverage
    
    Returns:
        Resource: The next resource to verify, or None if no resources need verification
    """
    # First, try to find resources that have never been verified
    never_verified = Resource.objects.filter(
        last_verified_at__isnull=True,
        status='published',
        is_deleted=False,
        is_archived=False
    ).order_by('id').first()
    
    if never_verified:
        return never_verified
    
    # If no never-verified resources, find expired verifications
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    expired_resources = []
    
    # Get all published resources with verification dates
    verified_resources = Resource.objects.filter(
        last_verified_at__isnull=False,
        status='published',
        is_deleted=False,
        is_archived=False
    )
    
    for resource in verified_resources:
        if resource.needs_verification:
            expired_resources.append(resource)
    
    # Sort by ID and return the lowest
    if expired_resources:
        return min(expired_resources, key=lambda r: r.id)
    
    return None


def display_resource_info(resource: Resource) -> None:
    """
    Display comprehensive resource information for verification.
    
    Args:
        resource: The Resource object to display
    """
    print("=" * 80)
    print(f"RESOURCE VERIFICATION - {resource.name.upper()}")
    print("=" * 80)
    print()
    
    # Basic Information
    print("📋 BASIC INFORMATION")
    print("-" * 40)
    print(f"ID: {resource.id}")
    print(f"Name: {resource.name}")
    print(f"Status: {resource.status}")
    print(f"Category: {resource.category.name if resource.category else 'None'}")
    print(f"Description: {resource.description[:200]}{'...' if len(resource.description) > 200 else ''}")
    print()
    
    # Contact Information
    print("📞 CONTACT INFORMATION")
    print("-" * 40)
    # Format phone for display
    phone_display = resource.phone
    if phone_display:
        import re
        digits = re.sub(r'\D', '', phone_display)
        if len(digits) == 10:
            phone_display = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            phone_display = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    print(f"Phone: {phone_display or 'Not provided'}")
    print(f"Email: {resource.email or 'Not provided'}")
    print(f"Website: {resource.website or 'Not provided'}")
    print()
    
    # Location
    print("📍 LOCATION")
    print("-" * 40)
    print(f"Address: {resource.address1 or 'Not provided'}")
    if resource.address2:
        print(f"         {resource.address2}")
    print(f"City: {resource.city or 'Not provided'}")
    print(f"State: {resource.state or 'Not provided'}")
    print(f"County: {resource.county or 'Not provided'}")
    print(f"Postal Code: {resource.postal_code or 'Not provided'}")
    print()
    
    # Service Details
    print("🛠️ SERVICE DETAILS")
    print("-" * 40)
    print(f"Hours of Operation: {resource.hours_of_operation or 'Not provided'}")
    print(f"Emergency Service: {'Yes' if resource.is_emergency_service else 'No'}")
    print(f"24-Hour Service: {'Yes' if resource.is_24_hour_service else 'No'}")
    print(f"Eligibility Requirements: {resource.eligibility_requirements or 'Not provided'}")
    print(f"Populations Served: {resource.populations_served or 'Not provided'}")
    print(f"Insurance Accepted: {resource.insurance_accepted or 'Not provided'}")
    print(f"Cost Information: {resource.cost_information or 'Not provided'}")
    print(f"Languages Available: {resource.languages_available or 'Not provided'}")
    print(f"Capacity: {resource.capacity or 'Not provided'}")
    print()
    
    # Service Types
    if resource.service_types.exists():
        print("🏷️ SERVICE TYPES")
        print("-" * 40)
        for service_type in resource.service_types.all():
            print(f"  • {service_type.name}")
        print()
    
    # Coverage Areas
    if resource.coverage_areas.exists():
        print("🗺️ COVERAGE AREAS")
        print("-" * 40)
        for coverage in resource.coverage_areas.all():
            print(f"  • {coverage.name}")
        print()
    
    # Verification Information
    print("✅ VERIFICATION INFORMATION")
    print("-" * 40)
    if resource.last_verified_at:
        print(f"Last Verified: {resource.last_verified_at.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"Verified By: {resource.last_verified_by.get_full_name() if resource.last_verified_by else 'Unknown'}")
        print(f"Verification Frequency: {resource.verification_frequency_days} days")
        if resource.next_verification_date:
            print(f"Next Verification Due: {resource.next_verification_date.strftime('%B %d, %Y')}")
    else:
        print("Last Verified: Never verified")
        print("Verification Frequency: 180 days (default)")
    print(f"Needs Verification: {'Yes' if resource.needs_verification else 'No'}")
    print()
    
    # Source and Notes
    print("📝 SOURCE & NOTES")
    print("-" * 40)
    print(f"Source: {resource.source or 'Not provided'}")
    if resource.notes:
        print(f"Notes: {resource.notes}")
    else:
        print("Notes: No internal notes")
    print()
    
    # Metadata
    print("📊 METADATA")
    print("-" * 40)
    print(f"Created: {resource.created_at.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"Created By: {resource.created_by.get_full_name() if resource.created_by else 'Unknown'}")
    print(f"Last Updated: {resource.updated_at.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"Updated By: {resource.updated_by.get_full_name() if resource.updated_by else 'Unknown'}")
    print()
    
    # Verification Priority
    print("🎯 VERIFICATION PRIORITY")
    print("-" * 40)
    if not resource.last_verified_at:
        print("🔴 HIGH PRIORITY: Never verified")
    elif resource.needs_verification:
        days_overdue = (datetime.now().replace(tzinfo=resource.last_verified_at.tzinfo) - resource.next_verification_date).days
        print(f"🟡 MEDIUM PRIORITY: Verification overdue by {days_overdue} days")
    else:
        print("🟢 LOW PRIORITY: Recently verified")
    print()
    
    print("=" * 80)
    print("VERIFICATION CHECKLIST")
    print("=" * 80)
    print("Use this information to verify the resource following the process in VERIFICATION.md:")
    print()
    print("1. ✅ Contact Information")
    print("   - [ ] Phone number: Call to verify")
    print("   - [ ] Email: Check website contact page")
    print("   - [ ] Website: Test link functionality")
    print("   - [ ] Address: Verify with Google Maps/geocoding")
    print()
    print("2. ✅ Service Information")
    print("   - [ ] Description: Compare with official materials")
    print("   - [ ] Hours: Check website or call")
    print("   - [ ] Eligibility: Review official requirements")
    print("   - [ ] Populations served: Verify target demographics")
    print("   - [ ] Cost: Get current pricing information")
    print("   - [ ] Languages: Confirm available languages")
    print()
    print("3. ✅ Categorization")
    print("   - [ ] Review current category assignment")
    print("   - [ ] Verify it matches primary service")
    print("   - [ ] Suggest better category if needed")
    print()
    print("4. ✅ Documentation")
    print("   - [ ] Document all verification sources")
    print("   - [ ] Create verification summary")
    print("   - [ ] Update resource record")
    print("   - [ ] Set next verification date")
    print()


def main():
    """Main function to find and display the next resource for verification."""
    print("🔍 Finding next resource for verification...")
    print()
    
    resource = find_next_resource_for_verification()
    
    if not resource:
        print("✅ No resources need verification at this time!")
        print()
        print("All published resources are either:")
        print("  • Recently verified and within verification period")
        print("  • Not yet published (draft/needs_review status)")
        print("  • Archived or deleted")
        return
    
    display_resource_info(resource)
    
    # Provide quick commands for next steps
    print("🚀 QUICK COMMANDS")
    print("=" * 80)
    print("To extract this resource's data for analysis:")
    print(f"python manage.py shell -c \"from directory.models import Resource; import json; resource = Resource.objects.get(id={resource.id}); data = {{'id': resource.id, 'name': resource.name, 'category': resource.category.name if resource.category else None, 'description': resource.description, 'phone': resource.phone, 'email': resource.email, 'website': resource.website, 'address1': resource.address1, 'address2': resource.address2, 'city': resource.city, 'state': resource.state, 'county': resource.county, 'postal_code': resource.postal_code, 'hours_of_operation': resource.hours_of_operation, 'eligibility_requirements': resource.eligibility_requirements, 'populations_served': resource.populations_served, 'cost_information': resource.cost_information, 'languages_available': resource.languages_available, 'source': resource.source, 'notes': resource.notes}}; print(json.dumps(data, indent=2))\"")
    print()
    print("To find another resource for verification:")
    print("python find_next_verification.py")
    print()
    print("To view the complete verification process:")
    print("cat VERIFICATION.md")
    print()
    print("⚠️  REMINDER: APPROVAL REQUIRED ⚠️")
    print("After researching and preparing changes, you MUST present them for approval")
    print("before using update_resource_verification.py. See VERIFICATION.md Step 7.")


if __name__ == "__main__":
    main()
