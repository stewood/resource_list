#!/usr/bin/env python3
"""
Service Area Management CLI Tool

This script provides command-line interface for managing service areas for resources
in the resource directory system.

Usage:
    python manage_service_areas.py add <resource_id> <coverage_area_id>
    python manage_service_areas.py remove <resource_id> <coverage_area_id>
    python manage_service_areas.py list <resource_id>
    python manage_service_areas.py find-without-areas
    python manage_service_areas.py details <resource_id>
    python manage_service_areas.py list-coverage-areas [--kind KIND]

Author: Resource Directory Team
Created: 2025-08-20
"""

import os
import sys
import argparse
import django
from typing import Optional, List

# Setup Django
import sys
# Add the parent directory to the path so Django can find the project
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.chdir(project_root)  # Change to project root for database access
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, CoverageArea, ResourceCoverage
from django.contrib.auth.models import User


class ServiceAreaManager:
    """CLI tool for managing service areas."""
    
    def __init__(self):
        self.user = self._get_default_user()
    
    def _get_default_user(self) -> Optional[User]:
        """Get the first available user for audit trail."""
        return User.objects.first()
    
    def add_service_area(self, resource_id: int, coverage_area_id: int) -> bool:
        """Add a service area to a resource.
        
        Args:
            resource_id: ID of the resource
            coverage_area_id: ID of the coverage area
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the resource
            resource = Resource.objects.get(id=resource_id)
            print(f"Resource: {resource.name} (ID: {resource.id})")
            
            # Get the coverage area
            coverage_area = CoverageArea.objects.get(id=coverage_area_id)
            print(f"Coverage Area: {coverage_area.name} ({coverage_area.kind})")
            
            # Check if association already exists
            existing = ResourceCoverage.objects.filter(
                resource=resource,
                coverage_area=coverage_area
            ).first()
            
            if existing:
                print(f"❌ Service area already assigned to this resource!")
                return False
            
            # Create the association
            resource_coverage = ResourceCoverage.objects.create(
                resource=resource,
                coverage_area=coverage_area,
                created_by=self.user,
                notes='Added via CLI tool'
            )
            
            print(f"✅ Successfully added {coverage_area.name} to {resource.name}")
            print(f"   Association created at: {resource_coverage.created_at}")
            return True
            
        except Resource.DoesNotExist:
            print(f"❌ Resource with ID {resource_id} not found!")
            return False
        except CoverageArea.DoesNotExist:
            print(f"❌ Coverage area with ID {coverage_area_id} not found!")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def remove_service_area(self, resource_id: int, coverage_area_id: int) -> bool:
        """Remove a service area from a resource.
        
        Args:
            resource_id: ID of the resource
            coverage_area_id: ID of the coverage area
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the resource
            resource = Resource.objects.get(id=resource_id)
            print(f"Resource: {resource.name} (ID: {resource.id})")
            
            # Get the coverage area
            coverage_area = CoverageArea.objects.get(id=coverage_area_id)
            print(f"Coverage Area: {coverage_area.name} ({coverage_area.kind})")
            
            # Find and delete the association
            association = ResourceCoverage.objects.filter(
                resource=resource,
                coverage_area=coverage_area
            ).first()
            
            if not association:
                print(f"❌ Service area not assigned to this resource!")
                return False
            
            association.delete()
            print(f"✅ Successfully removed {coverage_area.name} from {resource.name}")
            return True
            
        except Resource.DoesNotExist:
            print(f"❌ Resource with ID {resource_id} not found!")
            return False
        except CoverageArea.DoesNotExist:
            print(f"❌ Coverage area with ID {coverage_area_id} not found!")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def list_service_areas(self, resource_id: int) -> bool:
        """List all service areas for a resource.
        
        Args:
            resource_id: ID of the resource
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the resource
            resource = Resource.objects.get(id=resource_id)
            print(f"Resource: {resource.name} (ID: {resource.id})")
            print(f"Status: {resource.status}")
            print(f"Category: {resource.category}")
            print(f"Phone: {resource.phone}")
            print(f"Location: {resource.city}, {resource.state}")
            print()
            
            # Get service areas
            service_areas = resource.coverage_areas.all()
            
            if not service_areas.exists():
                print("No service areas assigned to this resource.")
                return True
            
            print(f"Service Areas ({service_areas.count()}):")
            print("-" * 50)
            
            for area in service_areas:
                print(f"ID: {area.id}")
                print(f"Name: {area.name}")
                print(f"Type: {area.kind}")
                if area.radius_m:
                    print(f"Radius: {area.radius_m}m")
                if area.ext_ids:
                    print(f"External IDs: {area.ext_ids}")
                print()
            
            return True
            
        except Resource.DoesNotExist:
            print(f"❌ Resource with ID {resource_id} not found!")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def find_resource_without_areas(self) -> bool:
        """Find and display a resource that doesn't have service areas.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find a resource without service areas
            resource = Resource.objects.filter(coverage_areas__isnull=True).first()
            
            if not resource:
                print("❌ No resources found without service areas!")
                return False
            
            print("=== RESOURCE WITHOUT SERVICE AREAS ===")
            print(f"ID: {resource.id}")
            print(f"Name: {resource.name}")
            print(f"Status: {resource.status}")
            print(f"Category: {resource.category}")
            print(f"Phone: {resource.phone}")
            print(f"Email: {resource.email}")
            print(f"Website: {resource.website}")
            print(f"Address: {resource.address1}")
            if resource.address2:
                print(f"         {resource.address2}")
            print(f"Location: {resource.city}, {resource.state} {resource.postal_code}")
            print(f"County: {resource.county}")
            print(f"Hours: {resource.hours_of_operation}")
            print(f"Emergency Service: {resource.is_emergency_service}")
            print(f"24-Hour Service: {resource.is_24_hour_service}")
            print(f"Eligibility: {resource.eligibility_requirements}")
            print(f"Populations Served: {resource.populations_served}")
            print(f"Insurance Accepted: {resource.insurance_accepted}")
            print(f"Description: {resource.description}")
            print(f"Notes: {resource.notes}")
            print(f"Source: {resource.source}")
            print(f"Created: {resource.created_at}")
            print(f"Updated: {resource.updated_at}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_resource_details(self, resource_id: int) -> bool:
        """Get detailed information about a specific resource.
        
        Args:
            resource_id: ID of the resource
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the resource
            resource = Resource.objects.get(id=resource_id)
            
            print("=== RESOURCE DETAILS ===")
            print(f"ID: {resource.id}")
            print(f"Name: {resource.name}")
            print(f"Status: {resource.status}")
            print(f"Category: {resource.category}")
            print(f"Service Types: {', '.join([st.name for st in resource.service_types.all()])}")
            print(f"Phone: {resource.phone}")
            print(f"Email: {resource.email}")
            print(f"Website: {resource.website}")
            print(f"Address: {resource.address1}")
            if resource.address2:
                print(f"         {resource.address2}")
            print(f"Location: {resource.city}, {resource.state} {resource.postal_code}")
            print(f"County: {resource.county}")
            print(f"Hours: {resource.hours_of_operation}")
            print(f"Emergency Service: {resource.is_emergency_service}")
            print(f"24-Hour Service: {resource.is_24_hour_service}")
            print(f"Eligibility: {resource.eligibility_requirements}")
            print(f"Populations Served: {resource.populations_served}")
            print(f"Insurance Accepted: {resource.insurance_accepted}")
            print(f"Description: {resource.description}")
            print(f"Notes: {resource.notes}")
            print(f"Source: {resource.source}")
            print(f"Created: {resource.created_at}")
            print(f"Updated: {resource.updated_at}")
            
            # Service areas
            service_areas = resource.coverage_areas.all()
            print(f"\nService Areas ({service_areas.count()}):")
            if service_areas.exists():
                for area in service_areas:
                    print(f"  - {area.name} ({area.kind})")
            else:
                print("  None assigned")
            
            return True
            
        except Resource.DoesNotExist:
            print(f"❌ Resource with ID {resource_id} not found!")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def list_coverage_areas(self, kind: Optional[str] = None, limit: int = 20) -> bool:
        """List available coverage areas.
        
        Args:
            kind: Filter by coverage area kind (CITY, COUNTY, STATE, etc.)
            limit: Maximum number of results to show
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            queryset = CoverageArea.objects.all()
            
            if kind:
                queryset = queryset.filter(kind=kind.upper())
                print(f"Coverage Areas (kind: {kind.upper()}):")
            else:
                print("All Coverage Areas:")
            
            areas = queryset[:limit]
            total = queryset.count()
            
            print(f"Showing {len(areas)} of {total} coverage areas")
            print("-" * 60)
            
            for area in areas:
                print(f"ID: {area.id:4} | {area.name:30} | {area.kind:8}")
            
            if total > limit:
                print(f"\n... and {total - limit} more. Use --limit to see more results.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Service Area Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_service_areas.py add 54 27                    # Add Kentucky to kynect
  python manage_service_areas.py remove 54 27                 # Remove Kentucky from kynect
  python manage_service_areas.py list 54                      # List service areas for resource 54
  python manage_service_areas.py find-without-areas           # Find a resource without service areas
  python manage_service_areas.py details 54                   # Get detailed info about resource 54
  python manage_service_areas.py list-coverage-areas --kind STATE  # List all state coverage areas
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a service area to a resource')
    add_parser.add_argument('resource_id', type=int, help='Resource ID')
    add_parser.add_argument('coverage_area_id', type=int, help='Coverage Area ID')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a service area from a resource')
    remove_parser.add_argument('resource_id', type=int, help='Resource ID')
    remove_parser.add_argument('coverage_area_id', type=int, help='Coverage Area ID')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List service areas for a resource')
    list_parser.add_argument('resource_id', type=int, help='Resource ID')
    
    # Find without areas command
    subparsers.add_parser('find-without-areas', help='Find a resource without service areas')
    
    # Details command
    details_parser = subparsers.add_parser('details', help='Get detailed information about a resource')
    details_parser.add_argument('resource_id', type=int, help='Resource ID')
    
    # List coverage areas command
    list_ca_parser = subparsers.add_parser('list-coverage-areas', help='List available coverage areas')
    list_ca_parser.add_argument('--kind', help='Filter by coverage area kind (CITY, COUNTY, STATE, etc.)')
    list_ca_parser.add_argument('--limit', type=int, default=20, help='Maximum number of results to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize the manager
    manager = ServiceAreaManager()
    
    # Execute the command
    if args.command == 'add':
        success = manager.add_service_area(args.resource_id, args.coverage_area_id)
    elif args.command == 'remove':
        success = manager.remove_service_area(args.resource_id, args.coverage_area_id)
    elif args.command == 'list':
        success = manager.list_service_areas(args.resource_id)
    elif args.command == 'find-without-areas':
        success = manager.find_resource_without_areas()
    elif args.command == 'details':
        success = manager.get_resource_details(args.resource_id)
    elif args.command == 'list-coverage-areas':
        success = manager.list_coverage_areas(args.kind, args.limit)
    else:
        print(f"Unknown command: {args.command}")
        return
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
