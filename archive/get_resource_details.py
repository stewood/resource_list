#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource

def get_resource_details(resource_id):
    try:
        resource = Resource.objects.get(id=resource_id)
        
        print("=== RESOURCE DETAILS ===")
        print(f"ID: {resource.id}")
        print(f"Name: {resource.name}")
        print(f"Description: {resource.description}")
        print(f"Category: {resource.category.name if resource.category else 'None'}")
        print(f"Phone: {resource.phone}")
        print(f"Email: {resource.email}")
        print(f"Website: {resource.website}")
        print(f"Address1: {resource.address1}")
        print(f"Address2: {resource.address2}")
        print(f"City: {resource.city}")
        print(f"State: {resource.state}")
        print(f"Postal Code: {resource.postal_code}")
        print(f"County: {resource.county}")
        print(f"Hours: {resource.hours_of_operation}")
        print(f"Eligibility: {resource.eligibility_requirements}")
        print(f"Populations Served: {resource.populations_served}")
        print(f"Cost Info: {resource.cost_information}")
        print(f"Languages: {resource.languages_available}")
        print(f"Status: {resource.status}")
        print(f"Created: {resource.created_at}")
        print(f"Updated: {resource.updated_at}")
        
        print("\n=== SERVICE TYPES ===")
        for st in resource.service_types.all():
            print(f"  - {st.name}")
        
        print("\n=== COVERAGE AREAS ===")
        for ca in resource.coverage_areas.all():
            print(f"  - {ca.name}")
            
        return resource
        
    except Resource.DoesNotExist:
        print(f"Resource with ID {resource_id} not found")
        return None

if __name__ == "__main__":
    resource_id = int(sys.argv[1]) if len(sys.argv) > 1 else 344
    get_resource_details(resource_id)

