#!/usr/bin/env python3
"""
Non-Interactive Resource Update Script

This script allows updating resource fields and transitioning status without user interaction.
It's designed for AI automation and batch processing.
"""

import os
import sys
import django
import argparse
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, TaxonomyCategory, ServiceType
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def update_resource_from_dict(resource, update_data):
    """Update resource fields from a dictionary."""
    
    # Basic Information
    if 'name' in update_data:
        resource.name = update_data['name']
    if 'description' in update_data:
        resource.description = update_data['description']
    if 'source' in update_data:
        resource.source = update_data['source']
    
    # Category
    if 'category_id' in update_data:
        try:
            resource.category = TaxonomyCategory.objects.get(id=update_data['category_id'])
        except TaxonomyCategory.DoesNotExist:
            print(f"Warning: Category ID {update_data['category_id']} not found")
    
    # Contact Information
    if 'phone' in update_data:
        resource.phone = update_data['phone']
    if 'email' in update_data:
        resource.email = update_data['email']
    if 'website' in update_data:
        resource.website = update_data['website']
    
    # Location
    if 'address1' in update_data:
        resource.address1 = update_data['address1']
    if 'address2' in update_data:
        resource.address2 = update_data['address2']
    if 'city' in update_data:
        resource.city = update_data['city']
    if 'state' in update_data:
        resource.state = update_data['state']
    if 'county' in update_data:
        resource.county = update_data['county']
    if 'postal_code' in update_data:
        resource.postal_code = update_data['postal_code']
    
    # Service Types
    if 'service_type_ids' in update_data:
        resource.service_types.clear()
        for service_type_id in update_data['service_type_ids']:
            try:
                service_type = ServiceType.objects.get(id=service_type_id)
                resource.service_types.add(service_type)
            except ServiceType.DoesNotExist:
                print(f"Warning: Service Type ID {service_type_id} not found")
    
    # Operational Details
    if 'hours_of_operation' in update_data:
        resource.hours_of_operation = update_data['hours_of_operation']
    if 'is_emergency_service' in update_data:
        resource.is_emergency_service = update_data['is_emergency_service']
    if 'is_24_hour_service' in update_data:
        resource.is_24_hour_service = update_data['is_24_hour_service']
    if 'capacity' in update_data:
        resource.capacity = update_data['capacity']
    
    # Service Information
    if 'eligibility_requirements' in update_data:
        resource.eligibility_requirements = update_data['eligibility_requirements']
    if 'populations_served' in update_data:
        resource.populations_served = update_data['populations_served']
    if 'insurance_accepted' in update_data:
        resource.insurance_accepted = update_data['insurance_accepted']
    if 'cost_information' in update_data:
        resource.cost_information = update_data['cost_information']
    if 'languages_available' in update_data:
        resource.languages_available = update_data['languages_available']
    
    # Notes
    if 'notes' in update_data:
        resource.notes = update_data['notes']


def validate_for_review(resource):
    """Validate that resource meets requirements for 'needs review' status."""
    
    errors = []
    
    # Check required fields for needs_review status
    if not resource.city:
        errors.append("City is required for review")
    
    if not resource.state:
        errors.append("State is required for review")
    
    if len(resource.description) < 20:
        errors.append("Description must be at least 20 characters for review")
    
    if not resource.source:
        errors.append("Source is required for review")
    
    return errors


def transition_to_review(resource, user):
    """Transition resource to 'needs review' status."""
    
    # Validate requirements
    errors = validate_for_review(resource)
    
    if errors:
        print("❌ Cannot transition to 'needs review' status. Please fix the following issues:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    # Update status and user
    old_status = resource.status
    resource.status = "needs_review"
    resource.updated_by = user
    
    try:
        resource.full_clean()
        resource.save()
        print(f"✅ Successfully transitioned from '{old_status}' to 'needs_review' status!")
        return True
    except ValidationError as e:
        print("❌ Validation error occurred:")
        for field, errors_list in e.message_dict.items():
            for error in errors_list:
                print(f"  • {field}: {error}")
        return False


def main():
    """Main function for non-interactive resource updates."""
    
    parser = argparse.ArgumentParser(description='Non-interactive resource update and status transition')
    parser.add_argument('resource_id', type=int, help='ID of the resource to update')
    parser.add_argument('--user', type=str, default='admin', help='Username for the update (default: admin)')
    parser.add_argument('--transition', choices=['draft', 'needs_review', 'published'], 
                       help='Transition to this status after update')
    parser.add_argument('--data', type=str, help='JSON string with update data')
    parser.add_argument('--data-file', type=str, help='Path to JSON file with update data')
    
    args = parser.parse_args()
    
    try:
        # Get the resource
        resource = Resource.objects.get(id=args.resource_id)
    except Resource.DoesNotExist:
        print(f"❌ Resource with ID {args.resource_id} not found!")
        return
    
    # Get the user
    try:
        user = User.objects.get(username=args.user)
    except User.DoesNotExist:
        print(f"❌ User '{args.user}' not found!")
        return
    
    # Load update data
    update_data = {}
    
    if args.data:
        try:
            update_data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON data: {e}")
            return
    
    elif args.data_file:
        try:
            with open(args.data_file, 'r') as f:
                update_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error reading data file: {e}")
            return
    
    else:
        print("❌ No update data provided. Use --data or --data-file")
        return
    
    # Display current resource
    print(f"\n📋 CURRENT RESOURCE - ID: {resource.id}")
    print("=" * 60)
    print(f"Name: {resource.name}")
    print(f"Status: {resource.status.upper()}")
    print(f"Phone: {resource.phone or 'Not provided'}")
    print(f"Website: {resource.website or 'Not provided'}")
    print(f"City: {resource.city or 'Not provided'}")
    print(f"State: {resource.state or 'Not provided'}")
    print("=" * 60)
    
    # Update resource
    print(f"\n🔄 UPDATING RESOURCE {resource.id}")
    print("=" * 60)
    
    update_resource_from_dict(resource, update_data)
    
    # Display updated summary
    print(f"\n📋 UPDATED RESOURCE SUMMARY")
    print("=" * 60)
    print(f"Name: {resource.name}")
    print(f"Status: {resource.status.upper()}")
    print(f"Phone: {resource.phone or 'Not provided'}")
    print(f"Website: {resource.website or 'Not provided'}")
    print(f"City: {resource.city or 'Not provided'}")
    print(f"State: {resource.state or 'Not provided'}")
    print("=" * 60)
    
    # Save the resource
    try:
        resource.full_clean()
        resource.save()
        print("✅ Resource updated successfully!")
    except ValidationError as e:
        print("❌ Validation error occurred:")
        for field, errors_list in e.message_dict.items():
            for error in errors_list:
                print(f"  • {field}: {error}")
        return
    
    # Transition status if requested
    if args.transition:
        if args.transition == "needs_review":
            success = transition_to_review(resource, user)
            if success:
                print(f"\n🎉 Resource {resource.id} has been updated and moved to 'needs_review' status!")
                print(f"Admin URL: http://localhost:8000/admin/directory/resource/{resource.id}/change/")
            else:
                print("\n⚠️  Resource was updated but could not be transitioned to 'needs_review' status.")
        else:
            # Simple status transition
            old_status = resource.status
            resource.status = args.transition
            resource.updated_by = user
            resource.save()
            print(f"\n✅ Resource {resource.id} has been updated and moved to '{args.transition}' status!")
            print(f"Admin URL: http://localhost:8000/admin/directory/resource/{resource.id}/change/")
    else:
        print("\n✅ Resource updated successfully (status unchanged).")


if __name__ == "__main__":
    main()
