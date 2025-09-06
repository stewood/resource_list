"""
Resource Management CLI Tool

This module provides a comprehensive command-line interface for managing resources
in the Community Resource Directory. It supports full CRUD operations with JSON
output for easy parsing by AI/scripts.

Commands:
    - list: List resources with filtering and pagination
    - show: Display detailed information about a specific resource
    - create: Create new resources interactively or from JSON
    - update: Update existing resources with field-level changes
    - search: Search resources using FTS5 and filters

Usage:
    python manage.py resource_cli <command> [options]

Examples:
    python manage.py resource_cli list --status=published --limit=10
    python manage.py resource_cli show 123
    python manage.py resource_cli create
    python manage.py resource_cli update 123 --status=published
    python manage.py resource_cli search "mental health" --city="London"

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import argparse
import datetime
import json
import sys
from typing import Any, Dict, List, Optional, Union

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from directory.models import Resource, TaxonomyCategory, ServiceType


class Command(BaseCommand):
    """
    Main command class for resource management CLI operations.
    
    This command provides a comprehensive interface for managing resources through
    the command line, with support for all CRUD operations, search, and filtering.
    All output is formatted as JSON for easy parsing by other tools and scripts.
    
    Attributes:
        help: Command help text
        requires_migrations_checks: Whether to check migrations before running
        
    Subcommands:
        list: List resources with filtering and pagination
        show: Show detailed resource information
        create: Create new resources
        update: Update existing resources
        search: Search resources with advanced filters
    """

    help = """Manage resources through the command line interface

This CLI tool provides comprehensive resource management capabilities for the Community Resource Directory.
All operations output JSON for easy parsing by AI tools, scripts, and other applications.

AVAILABLE COMMANDS:
  list           List resources with filtering, pagination, and sorting
  show           Display detailed information about a specific resource
  create         Create new resources interactively or from JSON input
  update         Update existing resources with field-level changes
  search         Search resources using FTS5 full-text search and filters
  list-areas     List available service areas with filtering and pagination
  show-area      Show detailed information about a specific service area
  list-categories List available taxonomy categories with filtering and pagination
  show-category  Show detailed information about a specific taxonomy category
  list-services  List available service types with filtering and pagination
  show-service   Show detailed information about a specific service type
  create-service Create a new service type
  update-service Update an existing service type

EXAMPLES:
  # List all published resources with pagination
  python manage.py resource_cli list --status=published --limit=10 --offset=0

  # Show detailed information about resource ID 123
  python manage.py resource_cli show 123

  # Create a new resource interactively
  python manage.py resource_cli create

  # Create a resource from JSON input
  python manage.py resource_cli create --json='{"name":"Test Resource","city":"London"}'

  # Create a resource with service areas
  python manage.py resource_cli create --json='{"name":"Crisis Center"}' --service-areas="Kentucky,London KY"

  # Update resource status to published
  python manage.py resource_cli update 123 --status=published

  # Update resource service areas
  python manage.py resource_cli update 123 --add-areas="Kentucky" --remove-areas="London KY"

  # Update resource service types
  python manage.py resource_cli update 123 --add-service-types="Crisis Intervention,Case Management"
  python manage.py resource_cli update 123 --remove-service-types="Crisis Intervention"
  python manage.py resource_cli update 123 --set-service-types="Emergency Shelter,Food Assistance"
  python manage.py resource_cli update 123 --clear-service-types

  # Search for mental health resources in London
  python manage.py resource_cli search "mental health" --city="London" --status=published

  # List all available categories
  python manage.py resource_cli list-categories

  # Show details for a specific category
  python manage.py resource_cli show-category 5

  # List and manage service types
  python manage.py resource_cli list-services --search="Crisis"
  python manage.py resource_cli show-service 15
  python manage.py resource_cli create-service --json='{"name":"Emergency Shelter","description":"Temporary housing for homeless individuals"}'
  python manage.py resource_cli update-service 15 --description="Updated description for crisis intervention"

  # Get help for a specific command
  python manage.py resource_cli list --help
  python manage.py resource_cli search --help
  python manage.py resource_cli list-categories --help
  python manage.py resource_cli list-services --help
  python manage.py resource_cli create-service --help

OUTPUT FORMAT:
  All commands output JSON with consistent structure including:
  - success/error status
  - timestamp
  - command executed
  - results or error details
  - metadata and pagination info

For detailed help on any command, use: python manage.py resource_cli <command> --help"""
    requires_migrations_checks = True

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command arguments and subcommands.
        
        Args:
            parser: ArgumentParser instance to add arguments to
        """
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands",
            metavar="COMMAND"
        )

        # List command
        list_parser = subparsers.add_parser(
            "list",
            help="List resources with filtering, pagination, and sorting",
            description="""List resources with comprehensive filtering, pagination, and sorting options.
            
This command displays resources in a paginated format with optional filtering by status, category, 
location, and other criteria. Results can be sorted by various fields and ordered ascending or descending.

EXAMPLES:
  # List all resources (default: 50 per page)
  python manage.py resource_cli list

  # List only published resources
  python manage.py resource_cli list --status=published

  # List resources in London, KY with pagination
  python manage.py resource_cli list --city="London" --state="KY" --limit=25 --offset=0

  # List resources sorted by creation date (newest first)
  python manage.py resource_cli list --sort=created_at --order=desc

  # List mental health resources in Kentucky
  python manage.py resource_cli list --category="Mental Health" --state="KY"

OUTPUT: JSON with resources, pagination info, and applied filters."""
        )
        self._add_list_arguments(list_parser)

        # Show command
        show_parser = subparsers.add_parser(
            "show",
            help="Show detailed information about a specific resource",
            description="""Display comprehensive information about a specific resource by ID.
            
This command shows all resource details including contact information, location, services, 
coverage areas, and related data. The resource ID must be a valid integer.

EXAMPLES:
  # Show resource with ID 123
  python manage.py resource_cli show 123

  # Show resource with ID 456 (will show error if not found)
  python manage.py resource_cli show 456

OUTPUT: JSON with complete resource details, related data, and metadata."""
        )
        self._add_show_arguments(show_parser)

        # Create command
        create_parser = subparsers.add_parser(
            "create",
            help="Create new resources interactively or from JSON",
            description="""Create new resources with interactive prompts or JSON input.
            
This command supports two modes:
1. INTERACTIVE: Step-by-step prompts for each field (default)
2. JSON INPUT: Create from structured JSON data

Resources are created in 'draft' status by default and include validation for required fields.
Phone numbers are automatically formatted and validated. Service areas can be assigned during creation.

EXAMPLES:
  # Create resource interactively
  python manage.py resource_cli create

  # Create resource from JSON input
  python manage.py resource_cli create --json='{"name":"Test Resource","city":"London","state":"KY"}'

  # Create resource with service areas from JSON
  python manage.py resource_cli create --json='{"name":"Crisis Center","service_areas":["Kentucky","London KY"]}'

  # Create resource with service areas from command line
  python manage.py resource_cli create --json='{"name":"Test Resource"}' --service-areas="Kentucky,Laurel County"

  # Create resource without service area prompts
  python manage.py resource_cli create --no-interactive-areas

REQUIRED FIELDS: name, category (selected from available options)
SERVICE AREAS: Can be assigned interactively or via JSON/command line arguments
OUTPUT: JSON with created resource details and ID."""
        )
        self._add_create_arguments(create_parser)

        # Update command
        update_parser = subparsers.add_parser(
            "update",
            help="Update existing resources with field-level changes",
            description="""Update existing resources with individual field changes or bulk JSON updates.
            
This command supports two modes:
1. INDIVIDUAL FIELDS: Update specific fields using --field=value arguments
2. BULK UPDATE: Update multiple fields using --json with complete resource data

Status transitions follow workflow rules (draft → needs_review → published).
Phone numbers are validated during updates. Service areas can be managed with dedicated flags.

EXAMPLES:
  # Update resource status to published
  python manage.py resource_cli update 123 --status=published

  # Update multiple fields individually
  python manage.py resource_cli update 123 --phone="555-9876" --city="Lexington" --state="KY"

  # Bulk update with JSON
  python manage.py resource_cli update 123 --json='{"status":"published","phone":"555-1234","notes":"Updated contact info"}'

  # Update emergency service flag
  python manage.py resource_cli update 123 --is_emergency_service=true

  # Add service areas to resource
  python manage.py resource_cli update 123 --add-areas="Kentucky,Laurel County"

  # Remove specific service areas
  python manage.py resource_cli update 123 --remove-areas="London KY"

  # Replace all service areas
  python manage.py resource_cli update 123 --set-areas="Kentucky,Laurel County"

  # Clear all service areas
  python manage.py resource_cli update 123 --clear-areas

OUTPUT: JSON with updated resource details and confirmation."""
        )
        self._add_update_arguments(update_parser)

        # Search command
        search_parser = subparsers.add_parser(
            "search",
            help="Search resources using FTS5 and filters",
            description="""Search resources using FTS5 full-text search with advanced filtering.
            
This command performs comprehensive searches using SQLite FTS5 for full-text matching
combined with exact field matching. Results can be filtered by location, category, and status.

SEARCH METHODS:
- FTS5: Full-text search across names, descriptions, and content
- Exact: Phone, email, website, and postal code matching
- Combined: Results from both methods with deduplication

EXAMPLES:
  # Basic search for mental health resources
  python manage.py resource_cli search "mental health"

  # Search with city filter
  python manage.py resource_cli search "crisis intervention" --city="London"

  # Search with multiple filters
  python manage.py resource_cli search "addiction treatment" --city="Lexington" --state="KY" --status=published

  # Search with category and limit
  python manage.py resource_cli search "health services" --category="Mental Health" --limit=10

  # Search for emergency services
  python manage.py resource_cli search "emergency" --status=published --limit=5

OUTPUT: JSON with search results, applied filters, and search metadata."""
        )
        self._add_search_arguments(search_parser)

        # List Areas command
        list_areas_parser = subparsers.add_parser(
            "list-areas",
            help="List available service areas with filtering and pagination",
            description="""List available service areas (coverage areas) with comprehensive filtering and pagination.
            
This command displays coverage areas that define where resources provide services. Areas can be
filtered by type (STATE, COUNTY, CITY, POLYGON, RADIUS) and searched by name.

EXAMPLES:
  # List all service areas (default: 50 per page)
  python manage.py resource_cli list-areas

  # List only state-level areas
  python manage.py resource_cli list-areas --kind=STATE

  # List county areas with pagination
  python manage.py resource_cli list-areas --kind=COUNTY --limit=25 --offset=0

  # Search for areas containing "Kentucky"
  python manage.py resource_cli list-areas --search="Kentucky"

  # List areas sorted by creation date (newest first)
  python manage.py resource_cli list-areas --sort=created_at --order=desc

OUTPUT: JSON with coverage areas, pagination info, and applied filters."""
        )
        self._add_list_areas_arguments(list_areas_parser)

        # Show Area command
        show_area_parser = subparsers.add_parser(
            "show-area",
            help="Show detailed information about a specific service area",
            description="""Display comprehensive information about a specific service area by ID.
            
This command shows all coverage area details including type, geometry, external identifiers,
and associated resources. The area ID must be a valid integer.

EXAMPLES:
  # Show area with ID 27
  python manage.py resource_cli show-area 27

  # Show area with ID 42 (will show error if not found)
  python manage.py resource_cli show-area 42

OUTPUT: JSON with complete coverage area details, associated resources, and metadata."""
        )
        self._add_show_area_arguments(show_area_parser)

        # List Categories command
        list_categories_parser = subparsers.add_parser(
            "list-categories",
            help="List available taxonomy categories with filtering and pagination",
            description="""List available taxonomy categories with comprehensive filtering and pagination.
            
This command displays categories that define the types of services resources provide. Categories can be
filtered by name and searched by description.

EXAMPLES:
  # List all categories (default: 50 per page)
  python manage.py resource_cli list-categories

  # List categories with pagination
  python manage.py resource_cli list-categories --limit=25 --offset=0

  # Search for categories containing "Mental"
  python manage.py resource_cli list-categories --search="Mental"

  # List categories sorted by creation date (newest first)
  python manage.py resource_cli list-categories --sort=created_at --order=desc

OUTPUT: JSON with categories, pagination info, and applied filters."""
        )
        self._add_list_categories_arguments(list_categories_parser)

        # Show Category command
        show_category_parser = subparsers.add_parser(
            "show-category",
            help="Show detailed information about a specific taxonomy category",
            description="""Display comprehensive information about a specific taxonomy category by ID.
            
This command shows all category details including name, description, and associated resources.
The category ID must be a valid integer.

EXAMPLES:
  # Show category with ID 5
  python manage.py resource_cli show-category 5

  # Show category with ID 12 (will show error if not found)
  python manage.py resource_cli show-category 12

OUTPUT: JSON with complete category details, associated resources, and metadata."""
        )
        self._add_show_category_arguments(show_category_parser)

        # List Services command
        list_services_parser = subparsers.add_parser(
            "list-services",
            help="List available service types with filtering and pagination",
            description="""List available service types with comprehensive filtering and pagination.
            
This command displays service types that define the specific services resources offer. Service types can be
filtered by name and searched by description.

EXAMPLES:
  # List all service types (default: 50 per page)
  python manage.py resource_cli list-services

  # List service types with pagination
  python manage.py resource_cli list-services --limit=25 --offset=0

  # Search for service types containing "Crisis"
  python manage.py resource_cli list-services --search="Crisis"

  # List service types sorted by creation date (newest first)
  python manage.py resource_cli list-services --sort=created_at --order=desc

OUTPUT: JSON with service types, pagination info, and applied filters."""
        )
        self._add_list_services_arguments(list_services_parser)

        # Show Service command
        show_service_parser = subparsers.add_parser(
            "show-service",
            help="Show detailed information about a specific service type",
            description="""Display comprehensive information about a specific service type by ID.
            
This command shows all service type details including name, description, and associated resources.
The service type ID must be a valid integer.

EXAMPLES:
  # Show service type with ID 15
  python manage.py resource_cli show-service 15

  # Show service type with ID 23 (will show error if not found)
  python manage.py resource_cli show-service 23

OUTPUT: JSON with complete service type details, associated resources, and metadata."""
        )
        self._add_show_service_arguments(show_service_parser)

        # Create Service command
        create_service_parser = subparsers.add_parser(
            "create-service",
            help="Create a new service type",
            description="""Create a new service type with interactive prompts or JSON input.
            
This command supports two modes:
1. INTERACTIVE: Step-by-step prompts for each field (default)
2. JSON INPUT: Create from structured JSON data

Service types are used to categorize the specific services that resources offer.

EXAMPLES:
  # Create service type interactively
  python manage.py resource_cli create-service

  # Create service type from JSON input
  python manage.py resource_cli create-service --json='{"name":"Crisis Intervention","description":"Immediate assistance for crisis situations"}'

REQUIRED FIELDS: name
OUTPUT: JSON with created service type details and ID."""
        )
        self._add_create_service_arguments(create_service_parser)

        # Update Service command
        update_service_parser = subparsers.add_parser(
            "update-service",
            help="Update an existing service type",
            description="""Update existing service types with field-level changes.
            
This command supports both individual field updates and bulk updates from JSON input.

EXAMPLES:
  # Update service type description
  python manage.py resource_cli update-service 15 --description="Updated description"

  # Update service type name
  python manage.py resource_cli update-service 15 --name="New Service Name"

  # Bulk update with JSON
  python manage.py resource_cli update-service 15 --json='{"name":"Updated Name","description":"Updated description"}'

OUTPUT: JSON with updated service type details and confirmation."""
        )
        self._add_update_service_arguments(update_service_parser)

    def _add_list_categories_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the list-categories command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of results per page (default: 50, max: 1000)"
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Number of results to skip for pagination (default: 0)"
        )
        parser.add_argument(
            "--search",
            type=str,
            help="Search for categories containing this text in the name"
        )
        parser.add_argument(
            "--sort",
            choices=["name", "created_at", "updated_at"],
            default="name",
            help="Field to sort results by (default: name)"
        )
        parser.add_argument(
            "--order",
            choices=["asc", "desc"],
            default="asc",
            help="Sort order: ascending (asc) or descending (desc) (default: asc)"
        )

    def _add_show_category_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the show-category command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "category_id",
            type=int,
            help="Numeric ID of the taxonomy category to display (e.g., 5, 12)"
        )

    def _add_list_services_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the list-services command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of results per page (default: 50, max: 1000)"
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Number of results to skip for pagination (default: 0)"
        )
        parser.add_argument(
            "--search",
            type=str,
            help="Search for service types containing this text in the name"
        )
        parser.add_argument(
            "--sort",
            choices=["name", "created_at"],
            default="name",
            help="Field to sort results by (default: name)"
        )
        parser.add_argument(
            "--order",
            choices=["asc", "desc"],
            default="asc",
            help="Sort order: ascending (asc) or descending (desc) (default: asc)"
        )

    def _add_show_service_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the show-service command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "service_id",
            type=int,
            help="Numeric ID of the service type to display (e.g., 15, 23)"
        )

    def _add_create_service_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the create-service command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--json",
            type=str,
            help="JSON string containing service type data for non-interactive creation"
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            default=True,
            help="Enable interactive mode with prompts (default: True)"
        )

    def _add_update_service_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the update-service command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "service_id",
            type=int,
            help="Numeric ID of the service type to update (e.g., 15, 23)"
        )
        parser.add_argument(
            "--json",
            type=str,
            help="JSON string containing update data"
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Update the service type name"
        )
        parser.add_argument(
            "--description",
            type=str,
            help="Update the service type description"
        )

    def _add_list_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the list command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--status",
            choices=["draft", "needs_review", "published"],
            help="Filter by resource status (draft, needs_review, or published)"
        )
        parser.add_argument(
            "--category",
            type=str,
            help="Filter by category name (e.g., 'Mental Health', 'Housing')"
        )
        parser.add_argument(
            "--city",
            type=str,
            help="Filter by city name (e.g., 'London', 'Lexington')"
        )
        parser.add_argument(
            "--state",
            type=str,
            help="Filter by state using 2-letter code (e.g., 'KY', 'TN')"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of results per page (default: 50, max: 1000)"
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Number of results to skip for pagination (default: 0)"
        )
        parser.add_argument(
            "--sort",
            choices=["name", "created_at", "updated_at", "status"],
            default="name",
            help="Field to sort results by (default: name)"
        )
        parser.add_argument(
            "--order",
            choices=["asc", "desc"],
            default="asc",
            help="Sort order: ascending (asc) or descending (desc) (default: asc)"
        )

    def _add_show_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the show command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "resource_id",
            type=int,
            help="Numeric ID of the resource to display (e.g., 123, 456)"
        )

    def _add_create_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the create command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--json",
            type=str,
            help="JSON string with resource data for non-interactive creation (e.g., '{\"name\":\"Test\",\"city\":\"London\",\"service_areas\":[\"Kentucky\",\"London KY\"]}')"
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            default=True,
            help="Enable interactive mode with step-by-step prompts (default: True, use --no-interactive to disable)"
        )
        parser.add_argument(
            "--service-areas",
            type=str,
            help="Comma-separated list of service area names or IDs for JSON mode (e.g., 'Kentucky,London KY' or '27,42')"
        )
        parser.add_argument(
            "--no-interactive-areas",
            action="store_false",
            dest="interactive_areas",
            help="Disable interactive service area prompts in interactive mode (default: True)"
        )

    def _add_update_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the update command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "resource_id",
            type=int,
            help="Numeric ID of the resource to update (e.g., 123, 456)"
        )
        parser.add_argument(
            "--json",
            type=str,
            help="JSON string with update data for bulk updates (e.g., '{\"status\":\"published\",\"phone\":\"555-1234\"}')"
        )
        parser.add_argument(
            "--status",
            choices=["draft", "needs_review", "published"],
            help="Update resource status (follows workflow: draft → needs_review → published)"
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Update resource name"
        )
        parser.add_argument(
            "--description",
            type=str,
            help="Update resource description"
        )
        parser.add_argument(
            "--category",
            type=str,
            help="Update resource category (name or ID, e.g., 'Mental Health' or '5')"
        )
        parser.add_argument(
            "--phone",
            type=str,
            help="Update phone number"
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Update email address"
        )
        parser.add_argument(
            "--website",
            type=str,
            help="Update website URL"
        )
        parser.add_argument(
            "--address1",
            type=str,
            help="Update address line 1"
        )
        parser.add_argument(
            "--address2",
            type=str,
            help="Update address line 2"
        )
        parser.add_argument(
            "--city",
            type=str,
            help="Update city"
        )
        parser.add_argument(
            "--state",
            type=str,
            help="Update state (2-letter code)"
        )
        parser.add_argument(
            "--county",
            type=str,
            help="Update county"
        )
        parser.add_argument(
            "--postal_code",
            type=str,
            help="Update postal code"
        )
        parser.add_argument(
            "--hours_of_operation",
            type=str,
            help="Update hours of operation"
        )
        parser.add_argument(
            "--eligibility_requirements",
            type=str,
            help="Update eligibility requirements"
        )
        parser.add_argument(
            "--populations_served",
            type=str,
            help="Update populations served"
        )
        parser.add_argument(
            "--insurance_accepted",
            type=str,
            help="Update insurance accepted"
        )
        parser.add_argument(
            "--cost_information",
            type=str,
            help="Update cost information"
        )
        parser.add_argument(
            "--languages_available",
            type=str,
            help="Update languages available"
        )
        parser.add_argument(
            "--capacity",
            type=str,
            help="Update capacity information"
        )
        parser.add_argument(
            "--source",
            type=str,
            help="Update source information"
        )
        parser.add_argument(
            "--notes",
            type=str,
            help="Update notes"
        )
        parser.add_argument(
            "--is_emergency_service",
            type=str,
            choices=["true", "false", "yes", "no", "1", "0"],
            help="Update emergency service flag"
        )
        parser.add_argument(
            "--is_24_hour_service",
            type=str,
            choices=["true", "false", "yes", "no", "1", "0"],
            help="Update 24-hour service flag"
        )
        parser.add_argument(
            "--add-areas",
            type=str,
            help="Add service areas to the resource (comma-separated names or IDs, e.g., 'Kentucky,London KY')"
        )
        parser.add_argument(
            "--remove-areas",
            type=str,
            help="Remove service areas from the resource (comma-separated names or IDs, e.g., 'London KY')"
        )
        parser.add_argument(
            "--set-areas",
            type=str,
            help="Replace all service areas with the specified ones (comma-separated names or IDs, e.g., 'Kentucky,Laurel County')"
        )
        parser.add_argument(
            "--clear-areas",
            action="store_true",
            help="Remove all service areas from the resource"
        )
        parser.add_argument(
            "--add-service-types",
            type=str,
            help="Add service types to the resource (comma-separated names or IDs, e.g., 'Crisis Intervention,Case Management')"
        )
        parser.add_argument(
            "--remove-service-types",
            type=str,
            help="Remove service types from the resource (comma-separated names or IDs, e.g., 'Crisis Intervention')"
        )
        parser.add_argument(
            "--set-service-types",
            type=str,
            help="Replace all service types with the specified ones (comma-separated names or IDs, e.g., 'Crisis Intervention,Case Management')"
        )
        parser.add_argument(
            "--clear-service-types",
            action="store_true",
            help="Remove all service types from the resource"
        )

    def _add_search_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the search command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "query",
            type=str,
            help="Search query string for FTS5 full-text search (e.g., 'mental health', 'crisis intervention')"
        )
        parser.add_argument(
            "--city",
            type=str,
            help="Filter results by city name (e.g., 'London', 'Lexington')"
        )
        parser.add_argument(
            "--state",
            type=str,
            help="Filter results by state using 2-letter code (e.g., 'KY', 'TN')"
        )
        parser.add_argument(
            "--category",
            type=str,
            help="Filter results by category name (e.g., 'Mental Health', 'Housing')"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of search results to return (default: 50, max: 1000)"
        )
        parser.add_argument(
            "--status",
            choices=["draft", "needs_review", "published"],
            help="Filter results by resource status (draft, needs_review, or published)"
        )

    def _add_list_areas_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the list-areas command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--kind",
            choices=["CITY", "COUNTY", "STATE", "POLYGON", "RADIUS"],
            help="Filter by coverage area type (CITY, COUNTY, STATE, POLYGON, RADIUS)"
        )
        parser.add_argument(
            "--search",
            type=str,
            help="Search for areas containing this text in the name"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of results per page (default: 50, max: 1000)"
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Number of results to skip for pagination (default: 0)"
        )
        parser.add_argument(
            "--sort",
            choices=["name", "kind", "created_at", "updated_at"],
            default="name",
            help="Field to sort results by (default: name)"
        )
        parser.add_argument(
            "--order",
            choices=["asc", "desc"],
            default="asc",
            help="Sort order: ascending (asc) or descending (desc) (default: asc)"
        )

    def _add_show_area_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the show-area command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "area_id",
            type=int,
            help="Numeric ID of the coverage area to display (e.g., 27, 42)"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle the command execution.
        
        This method routes to the appropriate subcommand handler based on the
        command argument. It also handles authentication and permission checking.
        
        Args:
            *args: Positional arguments
            **options: Command options
            
        Raises:
            CommandError: If command execution fails
        """
        command = options.get("command")
        
        if not command:
            self.print_help("manage.py", "resource_cli")
            return

        # Check authentication for write operations
        if command in ["create", "update", "create-service", "update-service"]:
            if not self._check_authentication():
                raise CommandError("Authentication required for write operations")

        # Route to appropriate command handler
        try:
            if command == "list":
                self._handle_list(**options)
            elif command == "show":
                self._handle_show(**options)
            elif command == "create":
                self._handle_create(**options)
            elif command == "update":
                self._handle_update(**options)
            elif command == "search":
                self._handle_search(**options)
            elif command == "list-areas":
                self._handle_list_areas(**options)
            elif command == "show-area":
                self._handle_show_area(**options)
            elif command == "list-categories":
                self._handle_list_categories(**options)
            elif command == "show-category":
                self._handle_show_category(**options)
            elif command == "list-services":
                self._handle_list_services(**options)
            elif command == "show-service":
                self._handle_show_service(**options)
            elif command == "create-service":
                self._handle_create_service(**options)
            elif command == "update-service":
                self._handle_update_service(**options)
            else:
                raise CommandError(f"Unknown command: {command}")
        except Exception as e:
            self._output_error(str(e))
            sys.exit(1)

    def _check_authentication(self) -> bool:
        """
        Check if the current user is authenticated.
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        # For now, we'll assume the command is run by an authenticated user
        # In a production environment, you might want to check for specific
        # environment variables or other authentication mechanisms
        return True

    def _handle_list(self, **options: Any) -> None:
        """
        Handle the list command.
        
        This method implements the list command functionality, providing filtering,
        pagination, and sorting capabilities for resources. It uses the existing
        Resource model and manager to efficiently query the database.
        
        Args:
            **options: Command options including filters and pagination
        """
        try:
            # Extract options
            status = options.get("status")
            category = options.get("category")
            city = options.get("city")
            state = options.get("state")
            limit = options.get("limit", 50)
            offset = options.get("offset", 0)
            sort_field = options.get("sort", "name")
            sort_order = options.get("order", "asc")
            
            # Build queryset with filters
            queryset = Resource.objects.all()
            
            # Apply filters
            filters_applied = {}
            if status:
                queryset = queryset.filter(status=status)
                filters_applied["status"] = status
            
            if category:
                queryset = queryset.filter(category__name__icontains=category)
                filters_applied["category"] = category
            
            if city:
                queryset = queryset.filter(city__icontains=city)
                filters_applied["city"] = city
            
            if state:
                queryset = queryset.filter(state__iexact=state)
                filters_applied["state"] = state
            
            # Apply sorting
            if sort_order == "desc":
                sort_field = f"-{sort_field}"
            
            queryset = queryset.order_by(sort_field)
            
            # Get total count before pagination
            total_count = queryset.count()
            
            # Apply pagination
            page = (offset // limit) + 1
            queryset = queryset[offset:offset + limit]
            
            # Convert to list to avoid lazy evaluation issues
            resources = list(queryset)
            
            # Format response using utility function
            from .cli_utils import format_list_response
            response = format_list_response(
                resources=resources,
                total_count=total_count,
                page=page,
                page_size=limit,
                filters=filters_applied
            )
            
            # Output the response
            self._output_json(response)
            
        except Exception as e:
            self._output_error(f"Error listing resources: {str(e)}")
            raise

    def _handle_show(self, **options: Any) -> None:
        """
        Handle the show command.
        
        This method implements the show command functionality, displaying detailed
        information about a specific resource. It retrieves the resource by ID,
        formats the data using utility functions, and handles error cases gracefully.
        
        Args:
            **options: Command options including resource_id
            
        Raises:
            CommandError: If resource is not found or other errors occur
        """
        try:
            # Extract resource ID from options
            resource_id = options.get("resource_id")
            if not resource_id:
                raise CommandError("Resource ID is required")
            
            # Validate and retrieve the resource
            from .cli_utils import validate_resource_id, format_resource_data
            resource = validate_resource_id(resource_id)
            
            # Format the resource data for output
            resource_data = format_resource_data(resource, include_related=True)
            
            # Create response with metadata
            response = {
                "command": "show",
                "resource_id": resource_id,
                "timestamp": str(datetime.datetime.now()),
                "resource": resource_data
            }
            
            # Output the response
            self._output_json(response)
            
        except ObjectDoesNotExist:
            raise CommandError(f"Resource with ID {resource_id} not found")
        except Exception as e:
            raise CommandError(f"Error showing resource: {str(e)}")

    def _handle_create(self, **options: Any) -> None:
        """
        Handle the create command.
        
        This method implements the create command functionality, allowing users to
        create new resources either interactively or from JSON input. It handles
        validation, creates resources in draft status by default, and returns
        the created resource details.
        
        Args:
            **options: Command options including JSON data and interactive mode
            
        Raises:
            CommandError: If creation fails or validation errors occur
        """
        try:
            # Extract options
            json_input = options.get("json")
            interactive = options.get("interactive", True)
            service_areas_input = options.get("service_areas")
            interactive_areas = options.get("interactive_areas", True)
            
            if json_input:
                # Non-interactive creation from JSON
                self._create_from_json(json_input, service_areas_input)
            elif interactive:
                # Interactive creation with prompts
                self._create_interactive(interactive_areas)
            else:
                raise CommandError("Either --json input or --interactive mode must be specified")
                
        except Exception as e:
            raise CommandError(f"Error creating resource: {str(e)}")

    def _create_from_json(self, json_input: str, service_areas_input: Optional[str] = None) -> None:
        """
        Create a resource from JSON input.
        
        Args:
            json_input: JSON string containing resource data
            service_areas_input: Optional comma-separated service area names/IDs
            
        Raises:
            CommandError: If JSON is invalid or creation fails
        """
        try:
            # Parse and validate JSON input
            from .cli_utils import validate_json_input
            resource_data = validate_json_input(json_input)
            
            # Process service areas if provided
            if service_areas_input:
                # Extract state from JSON for service area disambiguation
                resource_state = resource_data.get("state")
                
                # Create a temporary resource object for state-based disambiguation
                temp_resource = None
                if resource_state:
                    # Create a minimal resource object with just the state
                    class TempResource:
                        def __init__(self, state):
                            self.state = state
                    temp_resource = TempResource(resource_state)
                
                service_areas = self._process_service_areas_input(service_areas_input, temp_resource)
                if service_areas:
                    resource_data["service_areas"] = service_areas
            
            # Create the resource
            resource = self._create_resource(resource_data)
            
            # Format and output the response
            from .cli_utils import format_resource_data
            formatted_data = format_resource_data(resource, include_related=True)
            
            response = {
                "command": "create",
                "message": "Resource created successfully",
                "resource_id": resource.id,
                "timestamp": str(datetime.datetime.now()),
                "resource": formatted_data
            }
            
            self._output_json(response)
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON input: {str(e)}")
        except ValidationError as e:
            raise CommandError(f"Validation error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error creating resource from JSON: {str(e)}")

    def _create_interactive(self, interactive_areas: bool = True) -> None:
        """
        Create a resource interactively with user prompts.
        
        This method prompts the user for required and optional resource fields,
        validates the input, and creates the resource. It provides a user-friendly
        interface for resource creation.
        
        Args:
            interactive_areas: Whether to prompt for service areas interactively
            
        Raises:
            CommandError: If creation fails or user cancels
        """
        try:
            self.stdout.write("Creating new resource interactively...\n")
            self.stdout.write("Press Enter to skip optional fields, 'quit' to cancel.\n\n")
            
            # Collect resource data interactively
            resource_data = self._collect_interactive_input()
            
            if not resource_data:
                self.stdout.write("Resource creation cancelled.\n")
                return
            
            # Collect service areas if enabled
            if interactive_areas:
                service_areas = self._collect_service_areas_interactive()
                if service_areas:
                    resource_data["service_areas"] = service_areas
            
            # Create the resource
            resource = self._create_resource(resource_data)
            
            # Format and output the response
            from .cli_utils import format_resource_data
            formatted_data = format_resource_data(resource, include_related=True)
            
            response = {
                "command": "create",
                "message": "Resource created successfully",
                "resource_id": resource.id,
                "timestamp": str(datetime.datetime.now()),
                "resource": formatted_data
            }
            
            self._output_json(response)
            
        except KeyboardInterrupt:
            self.stdout.write("\nResource creation cancelled by user.\n")
        except Exception as e:
            raise CommandError(f"Error in interactive creation: {str(e)}")

    def _collect_interactive_input(self) -> Dict[str, Any]:
        """
        Collect resource data interactively from user input.
        
        Returns:
            Dictionary containing collected resource data
            
        Raises:
            CommandError: If user cancels or input is invalid
        """
        resource_data = {}
        
        # Required fields
        required_fields = [
            ("name", "Resource name"),
            ("description", "Resource description"),
            ("city", "City"),
            ("state", "State (2-letter code)")
        ]
        
        for field, label in required_fields:
            while True:
                value = input(f"{label} (required): ").strip()
                if value.lower() == 'quit':
                    return None
                if value:
                    resource_data[field] = value
                    break
                self.stdout.write(f"{label} is required. Please enter a value.\n")
        
        # Optional fields
        optional_fields = [
            ("phone", "Phone number"),
            ("email", "Email address"),
            ("website", "Website URL"),
            ("address1", "Address line 1"),
            ("address2", "Address line 2"),
            ("county", "County"),
            ("postal_code", "Postal code"),
            ("hours_of_operation", "Hours of operation"),
            ("eligibility_requirements", "Eligibility requirements"),
            ("populations_served", "Populations served"),
            ("insurance_accepted", "Insurance accepted"),
            ("cost_information", "Cost information"),
            ("languages_available", "Languages available"),
            ("capacity", "Capacity"),
            ("source", "Source"),
            ("notes", "Additional notes")
        ]
        
        for field, label in optional_fields:
            value = input(f"{label} (optional): ").strip()
            if value.lower() == 'quit':
                return None
            if value:
                resource_data[field] = value
        
        # Boolean fields
        boolean_fields = [
            ("is_emergency_service", "Is this an emergency service?"),
            ("is_24_hour_service", "Is this a 24-hour service?")
        ]
        
        for field, label in boolean_fields:
            while True:
                value = input(f"{label} (y/n): ").strip().lower()
                if value.lower() == 'quit':
                    return None
                if value in ['y', 'yes']:
                    resource_data[field] = True
                    break
                elif value in ['n', 'no']:
                    resource_data[field] = False
                    break
                self.stdout.write("Please enter 'y' or 'n'.\n")
        
        # Category selection
        try:
            from directory.models import TaxonomyCategory
            categories = TaxonomyCategory.objects.all()
            if categories.exists():
                self.stdout.write("\nAvailable categories:\n")
                for i, cat in enumerate(categories, 1):
                    self.stdout.write(f"{i}. {cat.name} - {cat.description}\n")
                
                while True:
                    choice = input(f"Select category (1-{len(categories)}, or press Enter to skip): ").strip()
                    if choice.lower() == 'quit':
                        return None
                    if not choice:
                        break
                    try:
                        cat_index = int(choice) - 1
                        if 0 <= cat_index < len(categories):
                            resource_data["category"] = categories[cat_index]
                            break
                        else:
                            self.stdout.write(f"Please enter a number between 1 and {len(categories)}.\n")
                    except ValueError:
                        self.stdout.write("Please enter a valid number.\n")
        except Exception:
            # If categories can't be loaded, continue without category
            pass
        
        return resource_data

    def _collect_service_areas_interactive(self) -> Optional[List[str]]:
        """
        Collect service areas interactively from user input.
        
        This method prompts the user to select service areas from available options,
        providing smart suggestions and validation. Users can search, filter, and
        select multiple areas.
        
        Returns:
            List of service area names/IDs, or None if cancelled
            
        Raises:
            CommandError: If user cancels or input is invalid
        """
        try:
            self.stdout.write("\n=== Service Area Selection ===\n")
            self.stdout.write("You can select multiple service areas where this resource provides services.\n")
            self.stdout.write("Enter area names or IDs, separated by commas. Type 'list' to see available areas.\n")
            self.stdout.write("Type 'search <term>' to search for areas, or 'quit' to skip.\n\n")
            
            # Import required models
            from directory.models.geographic.coverage_area import CoverageArea
            from .cli_utils import validate_service_areas
            
            service_areas = []
            
            while True:
                # Show current selection
                if service_areas:
                    self.stdout.write(f"Current selection: {', '.join(service_areas)}\n")
                
                # Get user input
                user_input = input("Enter service area (or 'done' to finish, 'list' to browse, 'search <term>' to search): ").strip()
                
                if user_input.lower() == 'quit':
                    return None
                elif user_input.lower() == 'done':
                    break
                elif user_input.lower() == 'list':
                    self._show_available_service_areas()
                    continue
                elif user_input.lower().startswith('search '):
                    search_term = user_input[7:].strip()
                    if search_term:
                        self._search_service_areas(search_term)
                    continue
                elif not user_input:
                    continue
                
                # Parse comma-separated input
                area_inputs = [area.strip() for area in user_input.split(',') if area.strip()]
                
                # Validate the areas
                validation_result = validate_service_areas(area_inputs)
                
                if validation_result["valid_areas"]:
                    # Add valid areas
                    for area in validation_result["valid_areas"]:
                        area_name = area["name"]
                        if area_name not in service_areas:
                            service_areas.append(area_name)
                            self.stdout.write(f"✅ Added: {area_name} ({area['kind']})\n")
                        else:
                            self.stdout.write(f"⚠️  Already selected: {area_name}\n")
                    
                    # Show invalid areas with suggestions
                    if validation_result["invalid_areas"]:
                        self.stdout.write(f"\n❌ Invalid areas: {', '.join(validation_result['invalid_areas'])}\n")
                        if validation_result["suggestions"]:
                            self.stdout.write("💡 Suggestions:\n")
                            for invalid_area, suggestions in validation_result["suggestions"].items():
                                self.stdout.write(f"   '{invalid_area}' → Try: {', '.join(suggestions)}\n")
                
                elif validation_result["suggestions"]:
                    # Show suggestions for invalid input
                    self.stdout.write(f"❌ No valid areas found. Suggestions:\n")
                    for invalid_area, suggestions in validation_result["suggestions"].items():
                        self.stdout.write(f"   '{invalid_area}' → Try: {', '.join(suggestions)}\n")
                else:
                    self.stdout.write(f"❌ No valid areas found for: {', '.join(area_inputs)}\n")
                    self.stdout.write("💡 Type 'list' to see available areas or 'search <term>' to search.\n")
            
            if service_areas:
                self.stdout.write(f"\n✅ Final service area selection: {', '.join(service_areas)}\n")
            
            return service_areas if service_areas else None
            
        except KeyboardInterrupt:
            self.stdout.write("\nService area selection cancelled.\n")
            return None
        except Exception as e:
            self.stdout.write(f"Error in service area selection: {str(e)}\n")
            return None

    def _show_available_service_areas(self) -> None:
        """
        Display available service areas in a user-friendly format.
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            
            # Get areas grouped by kind
            areas = CoverageArea.objects.all().order_by('kind', 'name')
            
            if not areas.exists():
                self.stdout.write("No service areas available in the database.\n")
                return
            
            self.stdout.write("\n📋 Available Service Areas:\n")
            self.stdout.write("=" * 50 + "\n")
            
            current_kind = None
            for area in areas:
                if area.kind != current_kind:
                    current_kind = area.kind
                    self.stdout.write(f"\n📍 {current_kind.title()}:\n")
                    self.stdout.write("-" * 30 + "\n")
                
                self.stdout.write(f"  {area.id:>4} | {area.name}\n")
            
            self.stdout.write(f"\nTotal: {areas.count()} areas available\n")
            self.stdout.write("💡 You can reference areas by name or ID\n\n")
            
        except Exception as e:
            self.stdout.write(f"Error displaying service areas: {str(e)}\n")

    def _search_service_areas(self, search_term: str) -> None:
        """
        Search and display service areas matching the search term.
        
        Args:
            search_term: Term to search for in area names
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            
            # Search for areas containing the term
            areas = CoverageArea.objects.filter(name__icontains=search_term).order_by('kind', 'name')
            
            if not areas.exists():
                self.stdout.write(f"❌ No service areas found matching '{search_term}'\n")
                return
            
            self.stdout.write(f"\n🔍 Search Results for '{search_term}':\n")
            self.stdout.write("=" * 50 + "\n")
            
            current_kind = None
            for area in areas:
                if area.kind != current_kind:
                    current_kind = area.kind
                    self.stdout.write(f"\n📍 {current_kind.title()}:\n")
                    self.stdout.write("-" * 30 + "\n")
                
                self.stdout.write(f"  {area.id:>4} | {area.name}\n")
            
            self.stdout.write(f"\nFound {areas.count()} matching areas\n\n")
            
        except Exception as e:
            self.stdout.write(f"Error searching service areas: {str(e)}\n")

    def _process_service_areas_input(self, service_areas_input: str, temp_resource: Optional[Any] = None) -> Optional[List[str]]:
        """
        Process service areas input from command line arguments.
        
        This method handles both comma-separated names and JSON array formats,
        validates the input, and returns a list of valid service area references.
        
        Args:
            service_areas_input: Comma-separated string or JSON array string
            temp_resource: A temporary resource object to help with disambiguation
            
        Returns:
            List of service area names/IDs, or None if invalid
            
        Raises:
            CommandError: If input format is invalid
        """
        try:
            if not service_areas_input.strip():
                return None
            
            # Try to parse as JSON first (for array format)
            service_areas = []
            try:
                import json
                parsed_input = json.loads(service_areas_input)
                if isinstance(parsed_input, list):
                    # JSON array format
                    service_areas = [str(area).strip() for area in parsed_input if str(area).strip()]
                else:
                    raise CommandError("JSON input must be an array of service area names/IDs")
            except (json.JSONDecodeError, ValueError):
                # Not JSON - treat as comma-separated format
                # Check if it looks like a single value (no commas)
                if ',' not in service_areas_input:
                    # Single value - could be a name or ID
                    service_areas = [service_areas_input.strip()]
                else:
                    # Comma-separated format
                    service_areas = [area.strip() for area in service_areas_input.split(',') if area.strip()]
            
            if not service_areas:
                return None
            
            # Get resource state for disambiguation if available
            resource_state = None
            if temp_resource and hasattr(temp_resource, 'state') and temp_resource.state:
                resource_state = temp_resource.state
            
            # Validate the service areas with enhanced disambiguation
            from .cli_utils import validate_service_areas
            validation_result = validate_service_areas(
                service_areas, 
                resource_state=resource_state,
                auto_resolve_duplicates=False  # Always false for safety
            )
            
            # Check for ambiguous areas first - this is a critical error
            if validation_result.get("ambiguous_areas"):
                ambiguous_info = validation_result["ambiguous_areas"][0]  # First ambiguous area
                error_message = f"Ambiguous area name: '{ambiguous_info['name']}'\n\n"
                error_message += f"Multiple matches found:\n"
                
                for match in ambiguous_info["matches"]:
                    state_name = match.get("state_name", f"FIPS:{match['state_fips']}")
                    error_message += f"  - {match['name']} ({match['kind']}) in {state_name} (ID: {match['id']})\n"
                
                error_message += f"\nTo resolve this ambiguity, use one of these methods:\n"
                for instruction in ambiguous_info["resolution_instructions"]:
                    error_message += f"  • {instruction}\n"
                
                error_message += f"\nExamples:\n"
                error_message += f"  • Use state specification: '{ambiguous_info['name']},KY'\n"
                error_message += f"  • Use specific ID: {ambiguous_info['matches'][0]['id']}\n"
                error_message += f"  • Filter by area type: --kind={ambiguous_info['matches'][0]['kind']}\n"
                
                raise CommandError(error_message)
            
            if validation_result["valid_areas"]:
                # Return valid area names
                valid_names = [area["name"] for area in validation_result["valid_areas"]]
                
                # Show warnings for invalid areas
                if validation_result["invalid_areas"]:
                    self.stdout.write(f"⚠️  Warning: Invalid service areas ignored: {', '.join(validation_result['invalid_areas'])}\n")
                    if validation_result["suggestions"]:
                        self.stdout.write("💡 Suggestions:\n")
                        for invalid_area, suggestions in validation_result["suggestions"].items():
                            self.stdout.write(f"   '{invalid_area}' → Try: {', '.join(suggestions)}\n")
                
                return valid_names
            else:
                # No valid areas found
                self.stdout.write(f"❌ No valid service areas found in: {service_areas_input}\n")
                if validation_result["suggestions"]:
                    self.stdout.write("💡 Suggestions:\n")
                    for invalid_area, suggestions in validation_result["suggestions"].items():
                        self.stdout.write(f"   '{invalid_area}' → Try: {', '.join(suggestions)}\n")
                return None
                
        except Exception as e:
            raise CommandError(f"Error processing service areas input: {str(e)}")

    def _create_resource(self, resource_data: Dict[str, Any]) -> Resource:
        """
        Create a resource from the provided data.
        
        Args:
            resource_data: Dictionary containing resource field values
            
        Returns:
            Created Resource instance
            
        Raises:
            CommandError: If resource creation fails
        """
        try:
            with transaction.atomic():
                # Set default values
                resource_data.setdefault("status", "draft")
                resource_data.setdefault("is_deleted", False)
                resource_data.setdefault("is_archived", False)
                
                # Handle required user fields - for CLI, we'll use a default admin user
                # In production, this should be properly authenticated
                try:
                    from django.contrib.auth.models import User
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if not admin_user:
                        # Create a default admin user if none exists
                        admin_user = User.objects.create_superuser(
                            username="cli_admin",
                            email="cli@example.com",
                            password="temp_password_change_me"
                        )
                        self.stdout.write("Created default CLI admin user. Please change password.\n")
                    
                    resource_data["created_by"] = admin_user
                    resource_data["updated_by"] = admin_user
                except Exception as e:
                    raise CommandError(f"Failed to set user fields: {str(e)}")
                
                # Validate phone number if provided
                if resource_data.get("phone"):
                    phone = resource_data["phone"]
                    # Remove non-digits for validation
                    import re
                    digits_only = re.sub(r"\D", "", phone)
                    if len(digits_only) < 10:
                        raise CommandError("Phone number must have at least 10 digits")
                    if len(digits_only) > 11:
                        raise CommandError("Phone number cannot have more than 11 digits")
                    if len(digits_only) == 11 and digits_only[0] != "1":
                        raise CommandError("If phone number has 11 digits, it must start with 1 (country code)")
                
                # Extract service areas before creating the resource
                service_areas = resource_data.pop("service_areas", None)
                
                # Create the resource
                resource = Resource.objects.create(**resource_data)
                
                # Handle service area assignments if provided
                if service_areas:
                    self._assign_service_areas_to_resource(resource, service_areas)
                
                self.stdout.write(f"Resource '{resource.name}' created successfully with ID {resource.id}\n")
                return resource
                
        except Exception as e:
            raise CommandError(f"Failed to create resource: {str(e)}")

    def _assign_service_areas_to_resource(self, resource: Resource, service_area_names: List[str]) -> None:
        """
        Assign service areas to a resource using the ResourceCoverage through model.
        
        This method creates the necessary ResourceCoverage associations between
        the resource and coverage areas, providing a complete audit trail.
        
        Args:
            resource: The resource to assign service areas to
            service_area_names: List of service area names to assign
            
        Raises:
            CommandError: If assignment fails
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            from directory.models.geographic.resource_coverage import ResourceCoverage
            
            # Get the admin user for audit trail
            admin_user = resource.created_by
            
            # Find coverage areas by name
            coverage_areas = CoverageArea.objects.filter(name__in=service_area_names)
            
            if not coverage_areas.exists():
                self.stdout.write("⚠️  Warning: No valid coverage areas found for assignment\n")
                return
            
            # Create ResourceCoverage associations
            created_count = 0
            for coverage_area in coverage_areas:
                # Check if association already exists
                if not ResourceCoverage.objects.filter(
                    resource=resource, 
                    coverage_area=coverage_area
                ).exists():
                    ResourceCoverage.objects.create(
                        resource=resource,
                        coverage_area=coverage_area,
                        created_by=admin_user,
                        notes="Created via CLI resource creation"
                    )
                    created_count += 1
                    self.stdout.write(f"✅ Assigned service area: {coverage_area.name} ({coverage_area.kind})\n")
                else:
                    self.stdout.write(f"⚠️  Service area already assigned: {coverage_area.name}\n")
            
            if created_count > 0:
                self.stdout.write(f"✅ Successfully assigned {created_count} service areas to resource\n")
            else:
                self.stdout.write("ℹ️  No new service areas were assigned\n")
                
        except Exception as e:
            raise CommandError(f"Failed to assign service areas: {str(e)}")

    def _handle_update(self, **options: Any) -> None:
        """
        Handle the update command.
        
        This method implements the update command functionality, allowing users to
        update existing resources with field-level changes. It supports both
        individual field updates and bulk updates from JSON input, with proper
        validation and status transition handling.
        
        Args:
            **options: Command options including resource_id and update data
            
        Raises:
            CommandError: If update fails or validation errors occur
        """
        try:
            # Extract options
            resource_id = options.get("resource_id")
            json_input = options.get("json")
            add_areas = options.get("add_areas")
            remove_areas = options.get("remove_areas")
            set_areas = options.get("set_areas")
            clear_areas = options.get("clear_areas")
            
            if not resource_id:
                raise CommandError("Resource ID is required for update")
            
            # Validate and retrieve the resource
            from .cli_utils import validate_resource_id
            resource = validate_resource_id(resource_id)
            
            if json_input:
                # Bulk update from JSON
                self._update_from_json(resource, json_input)
            else:
                # Individual field updates
                self._update_individual_fields(resource, options)
            
            # Handle service area updates
            if any([add_areas, remove_areas, set_areas, clear_areas]):
                self._update_resource_service_areas(resource, add_areas, remove_areas, set_areas, clear_areas)
            
            # Handle service type updates
            add_service_types = options.get("add_service_types")
            remove_service_types = options.get("remove_service_types")
            set_service_types = options.get("set_service_types")
            clear_service_types = options.get("clear_service_types")
            
            if any([add_service_types, remove_service_types, set_service_types, clear_service_types]):
                self._update_resource_service_types(resource, add_service_types, remove_service_types, set_service_types, clear_service_types)
                
        except Exception as e:
            raise CommandError(f"Error updating resource: {str(e)}")

    def _update_resource_service_areas(self, resource: Resource, add_areas: Optional[str], 
                                     remove_areas: Optional[str], set_areas: Optional[str], 
                                     clear_areas: bool) -> None:
        """
        Update service areas for an existing resource.
        
        This method handles adding, removing, setting, and clearing service areas
        for an existing resource. It provides comprehensive service area management
        with proper validation and audit trail.
        
        Args:
            resource: Resource instance to update
            add_areas: Comma-separated service area names/IDs to add
            remove_areas: Comma-separated service area names/IDs to remove
            set_areas: Comma-separated service area names/IDs to set (replaces all)
            clear_areas: Whether to clear all service areas
            
        Raises:
            CommandError: If service area operations fail
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            from directory.models.geographic.resource_coverage import ResourceCoverage
            
            # Get the admin user for audit trail
            admin_user = resource.updated_by or resource.created_by
            
            # Handle clear areas first (highest priority)
            if clear_areas:
                self._clear_all_service_areas(resource, admin_user)
                return
            
            # Handle set areas (replaces all existing areas)
            if set_areas:
                self._set_service_areas(resource, set_areas, admin_user)
                return
            
            # Handle add areas
            if add_areas:
                self._add_service_areas(resource, add_areas, admin_user)
            
            # Handle remove areas
            if remove_areas:
                self._remove_service_areas(resource, remove_areas, admin_user)
                
        except Exception as e:
            raise CommandError(f"Failed to update service areas: {str(e)}")

    def _clear_all_service_areas(self, resource: Resource, admin_user: User) -> None:
        """
        Remove all service areas from a resource.
        
        Args:
            resource: Resource instance to clear areas from
            admin_user: User performing the operation
        """
        try:
            from directory.models.geographic.resource_coverage import ResourceCoverage
            
            # Get current service areas
            current_areas = resource.coverage_areas.all()
            if not current_areas.exists():
                self.stdout.write("ℹ️  Resource has no service areas to clear\n")
                return
            
            # Remove all associations
            removed_count = ResourceCoverage.objects.filter(resource=resource).delete()[0]
            
            self.stdout.write(f"🗑️  Cleared {removed_count} service areas from resource\n")
            
        except Exception as e:
            raise CommandError(f"Failed to clear service areas: {str(e)}")

    def _set_service_areas(self, resource: Resource, areas_input: str, admin_user: User) -> None:
        """
        Replace all service areas with the specified ones.
        
        Args:
            resource: Resource instance to update
            areas_input: Comma-separated service area names/IDs
            admin_user: User performing the operation
        """
        try:
            # Clear existing areas first
            self._clear_all_service_areas(resource, admin_user)
            
            # Add new areas
            self._add_service_areas(resource, areas_input, admin_user)
            
            self.stdout.write("🔄 Service areas replaced successfully\n")
            
        except Exception as e:
            raise CommandError(f"Failed to set service areas: {str(e)}")

    def _add_service_areas(self, resource: Resource, areas_input: str, admin_user: User) -> None:
        """
        Add service areas to a resource.
        
        Args:
            resource: Resource instance to update
            areas_input: Comma-separated service area names/IDs
            admin_user: User performing the operation
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            from directory.models.geographic.resource_coverage import ResourceCoverage
            
            # Process and validate the areas input
            service_areas = self._process_service_areas_input(areas_input, resource)
            if not service_areas:
                self.stdout.write("⚠️  No valid service areas to add\n")
                return
            
            # Get coverage areas - handle both names and IDs
            coverage_areas = []
            for area_ref in service_areas:
                if area_ref.isdigit():
                    # This is an ID - look up by ID
                    try:
                        area_id = int(area_ref)
                        area = CoverageArea.objects.filter(id=area_id).first()
                        if area:
                            coverage_areas.append(area)
                        else:
                            self.stdout.write(f"⚠️  Warning: Area ID {area_id} not found\n")
                    except (ValueError, TypeError):
                        self.stdout.write(f"⚠️  Warning: Invalid area ID format: {area_ref}\n")
                else:
                    # This is a name - look up by name
                    areas_by_name = CoverageArea.objects.filter(name__iexact=area_ref)
                    if areas_by_name.exists():
                        if areas_by_name.count() == 1:
                            # Single match - use it
                            coverage_areas.append(areas_by_name.first())
                        else:
                            # Multiple matches - show warning and use first one
                            self.stdout.write(f"⚠️  Warning: Multiple areas found with name '{area_ref}', using first match\n")
                            coverage_areas.append(areas_by_name.first())
                    else:
                        self.stdout.write(f"⚠️  Warning: Area name '{area_ref}' not found\n")
            
            if not coverage_areas:
                self.stdout.write("⚠️  No valid coverage areas found for assignment\n")
                return
            
            # Add new areas
            added_count = 0
            for coverage_area in coverage_areas:
                # Check if association already exists
                if not ResourceCoverage.objects.filter(
                    resource=resource, 
                    coverage_area=coverage_area
                ).exists():
                    ResourceCoverage.objects.create(
                        resource=resource,
                        coverage_area=coverage_area,
                        created_by=admin_user,
                        notes="Added via CLI update command"
                    )
                    added_count += 1
                    self.stdout.write(f"✅ Added service area: {coverage_area.name} ({coverage_area.kind})\n")
                else:
                    self.stdout.write(f"ℹ️  Service area already assigned: {coverage_area.name}\n")
            
            if added_count > 0:
                self.stdout.write(f"✅ Successfully added {added_count} service areas\n")
            else:
                self.stdout.write("ℹ️  No new service areas were added\n")
                
        except Exception as e:
            raise CommandError(f"Failed to add service areas: {str(e)}")

    def _remove_service_areas(self, resource: Resource, areas_input: str, admin_user: User) -> None:
        """
        Remove service areas from a resource.
        
        Args:
            resource: Resource instance to update
            areas_input: Comma-separated service area names/IDs
            admin_user: User performing the operation
        """
        try:
            from directory.models.geographic.coverage_area import CoverageArea
            from directory.models.geographic.resource_coverage import ResourceCoverage
            
            # Process and validate the areas input
            service_areas = self._process_service_areas_input(areas_input, resource)
            if not service_areas:
                self.stdout.write(f"⚠️  No valid service areas to remove\n")
                return
            
            # Get coverage areas - handle both names and IDs
            coverage_areas = []
            for area_ref in service_areas:
                if area_ref.isdigit():
                    # This is an ID - look up by ID
                    try:
                        area_id = int(area_ref)
                        area = CoverageArea.objects.filter(id=area_id).first()
                        if area:
                            coverage_areas.append(area)
                        else:
                            self.stdout.write(f"⚠️  Warning: Area ID {area_id} not found\n")
                    except (ValueError, TypeError):
                        self.stdout.write(f"⚠️  Warning: Invalid area ID format: {area_ref}\n")
                else:
                    # This is a name - look up by name
                    areas_by_name = CoverageArea.objects.filter(name__iexact=area_ref)
                    if areas_by_name.exists():
                        if areas_by_name.count() == 1:
                            # Single match - use it
                            coverage_areas.append(areas_by_name.first())
                        else:
                            # Multiple matches - show warning and use first one
                            self.stdout.write(f"⚠️  Warning: Multiple areas found with name '{area_ref}', using first match\n")
                            coverage_areas.append(areas_by_name.first())
                    else:
                        self.stdout.write(f"⚠️  Warning: Area name '{area_ref}' not found\n")
            
            if not coverage_areas:
                self.stdout.write("⚠️  No valid coverage areas found for removal\n")
                return
            
            # Remove specified areas
            removed_count = 0
            for coverage_area in coverage_areas:
                # Check if association exists
                if ResourceCoverage.objects.filter(
                    resource=resource, 
                    coverage_area=coverage_area
                ).exists():
                    ResourceCoverage.objects.filter(
                        resource=resource, 
                        coverage_area=coverage_area
                    ).delete()
                    removed_count += 1
                    self.stdout.write(f"🗑️  Removed service area: {coverage_area.name} ({coverage_area.kind})\n")
                else:
                    self.stdout.write(f"ℹ️  Service area not assigned: {coverage_area.name}\n")
            
            if removed_count > 0:
                self.stdout.write(f"✅ Successfully removed {removed_count} service areas\n")
            else:
                self.stdout.write("ℹ️  No service areas were removed\n")
                
        except Exception as e:
            raise CommandError(f"Failed to remove service areas: {str(e)}")

    def _update_resource_service_types(self, resource: Resource, add_service_types: Optional[str], 
                                     remove_service_types: Optional[str], set_service_types: Optional[str], 
                                     clear_service_types: bool) -> None:
        """
        Update service types for an existing resource.
        
        This method handles adding, removing, setting, and clearing service types
        for an existing resource. It provides comprehensive service type management
        with proper validation.
        
        Args:
            resource: Resource instance to update
            add_service_types: Comma-separated service type names/IDs to add
            remove_service_types: Comma-separated service type names/IDs to remove
            set_service_types: Comma-separated service type names/IDs to set (replaces all)
            clear_service_types: Whether to clear all service types
            
        Raises:
            CommandError: If service type operations fail
        """
        try:
            # Handle clear service types first (highest priority)
            if clear_service_types:
                self._clear_all_service_types(resource)
                return
            
            # Handle set service types (replaces all existing types)
            if set_service_types:
                self._set_service_types(resource, set_service_types)
                return
            
            # Handle add service types
            if add_service_types:
                self._add_service_types(resource, add_service_types)
            
            # Handle remove service types
            if remove_service_types:
                self._remove_service_types(resource, remove_service_types)
                
        except Exception as e:
            raise CommandError(f"Failed to update service types: {str(e)}")

    def _clear_all_service_types(self, resource: Resource) -> None:
        """
        Remove all service types from a resource.
        
        Args:
            resource: Resource instance to clear service types from
        """
        try:
            # Get current service types
            current_types = resource.service_types.all()
            if not current_types.exists():
                self.stdout.write("ℹ️  Resource has no service types to clear\n")
                return
            
            # Remove all associations
            resource.service_types.clear()
            
            self.stdout.write(f"🗑️  Cleared {current_types.count()} service types from resource\n")
            
        except Exception as e:
            raise CommandError(f"Failed to clear service types: {str(e)}")

    def _set_service_types(self, resource: Resource, types_input: str) -> None:
        """
        Replace all service types with the specified ones.
        
        Args:
            resource: Resource instance to update
            types_input: Comma-separated service type names/IDs
        """
        try:
            # Clear existing service types first
            self._clear_all_service_types(resource)
            
            # Add new service types
            self._add_service_types(resource, types_input)
            
            self.stdout.write("🔄 Service types replaced successfully\n")
            
        except Exception as e:
            raise CommandError(f"Failed to set service types: {str(e)}")

    def _add_service_types(self, resource: Resource, types_input: str) -> None:
        """
        Add service types to a resource.
        
        Args:
            resource: Resource instance to update
            types_input: Comma-separated service type names/IDs
        """
        try:
            # Process and validate the types input
            service_types = self._process_service_types_input(types_input)
            if not service_types:
                self.stdout.write(f"⚠️  No valid service types to add\n")
                return
            
            # Add specified service types
            added_count = 0
            for service_type in service_types:
                if not resource.service_types.filter(id=service_type.id).exists():
                    resource.service_types.add(service_type)
                    added_count += 1
                    self.stdout.write(f"➕ Added service type: {service_type.name}\n")
                else:
                    self.stdout.write(f"ℹ️  Service type already assigned: {service_type.name}\n")
            
            if added_count > 0:
                self.stdout.write(f"✅ Successfully added {added_count} service types\n")
            else:
                self.stdout.write("ℹ️  No new service types were added\n")
                
        except Exception as e:
            raise CommandError(f"Failed to add service types: {str(e)}")

    def _remove_service_types(self, resource: Resource, types_input: str) -> None:
        """
        Remove service types from a resource.
        
        Args:
            resource: Resource instance to update
            types_input: Comma-separated service type names/IDs
        """
        try:
            # Process and validate the types input
            service_types = self._process_service_types_input(types_input)
            if not service_types:
                self.stdout.write(f"⚠️  No valid service types to remove\n")
                return
            
            # Remove specified service types
            removed_count = 0
            for service_type in service_types:
                if resource.service_types.filter(id=service_type.id).exists():
                    resource.service_types.remove(service_type)
                    removed_count += 1
                    self.stdout.write(f"🗑️  Removed service type: {service_type.name}\n")
                else:
                    self.stdout.write(f"ℹ️  Service type not assigned: {service_type.name}\n")
            
            if removed_count > 0:
                self.stdout.write(f"✅ Successfully removed {removed_count} service types\n")
            else:
                self.stdout.write("ℹ️  No service types were removed\n")
                
        except Exception as e:
            raise CommandError(f"Failed to remove service types: {str(e)}")

    def _process_service_types_input(self, types_input: str) -> List[ServiceType]:
        """
        Process service types input string and return list of ServiceType objects.
        
        Args:
            types_input: Comma-separated service type names/IDs
            
        Returns:
            List of ServiceType objects
        """
        try:
            # Split input and clean up
            type_refs = [ref.strip() for ref in types_input.split(",") if ref.strip()]
            if not type_refs:
                return []
            
            # Get service types - handle both names and IDs
            service_types = []
            for type_ref in type_refs:
                if type_ref.isdigit():
                    # This is an ID - look up by ID
                    try:
                        type_id = int(type_ref)
                        service_type = ServiceType.objects.filter(id=type_id).first()
                        if service_type:
                            service_types.append(service_type)
                        else:
                            self.stdout.write(f"⚠️  Warning: Service type ID {type_id} not found\n")
                    except (ValueError, TypeError):
                        self.stdout.write(f"⚠️  Warning: Invalid service type ID format: {type_ref}\n")
                else:
                    # This is a name - look up by name
                    types_by_name = ServiceType.objects.filter(name__iexact=type_ref)
                    if types_by_name.exists():
                        if types_by_name.count() == 1:
                            # Single match - use it
                            service_types.append(types_by_name.first())
                        else:
                            # Multiple matches - show warning and use first one
                            self.stdout.write(f"⚠️  Warning: Multiple service types found with name '{type_ref}', using first match\n")
                            service_types.append(types_by_name.first())
                    else:
                        self.stdout.write(f"⚠️  Warning: Service type name '{type_ref}' not found\n")
            
            return service_types
            
        except Exception as e:
            raise CommandError(f"Failed to process service types input: {str(e)}")

    def _update_from_json(self, resource: Resource, json_input: str) -> None:
        """
        Update a resource from JSON input.
        
        Args:
            resource: Resource instance to update
            json_input: JSON string containing update data
            
        Raises:
            CommandError: If JSON is invalid or update fails
        """
        try:
            # Parse and validate JSON input
            from .cli_utils import validate_json_input
            update_data = validate_json_input(json_input)
            
            # Update the resource
            updated_resource = self._update_resource(resource, update_data)
            
            # Format and output the response
            from .cli_utils import format_resource_data
            resource_data = format_resource_data(updated_resource, include_related=True)
            
            response = {
                "command": "update",
                "message": "Resource updated successfully",
                "resource_id": updated_resource.id,
                "timestamp": str(datetime.datetime.now()),
                "resource": resource_data
            }
            
            self._output_json(response)
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON input: {str(e)}")
        except ValidationError as e:
            raise CommandError(f"Validation error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error updating resource from JSON: {str(e)}")

    def _update_individual_fields(self, resource: Resource, options: Dict[str, Any]) -> None:
        """
        Update individual fields of a resource.
        
        Args:
            resource: Resource instance to update
            options: Command options containing field updates
            
        Raises:
            CommandError: If update fails
        """
        try:
            # Extract updateable fields from options
            update_data = {}
            
            # Status update with validation (only if explicitly provided)
            if "status" in options and options["status"] is not None:
                new_status = options["status"]
                from .cli_utils import validate_status_transition
                if validate_status_transition(resource.status, new_status):
                    update_data["status"] = new_status
                else:
                    raise CommandError(f"Invalid status transition from '{resource.status}' to '{new_status}'")
            
            # Category update with validation
            if "category" in options and options["category"] is not None:
                category_value = options["category"]
                try:
                    # Try to find category by ID first
                    if category_value.isdigit():
                        category = TaxonomyCategory.objects.filter(id=int(category_value)).first()
                        if not category:
                            raise CommandError(f"Category with ID {category_value} not found")
                    else:
                        # Try to find by name
                        category = TaxonomyCategory.objects.filter(name__iexact=category_value).first()
                        if not category:
                            raise CommandError(f"Category '{category_value}' not found")
                    
                    update_data["category"] = category
                except Exception as e:
                    raise CommandError(f"Error updating category: {str(e)}")
            
            # Text field updates
            text_fields = ["name", "description", "phone", "email", "website", 
                          "address1", "address2", "city", "state", "county", 
                          "postal_code", "hours_of_operation", "eligibility_requirements",
                          "populations_served", "insurance_accepted", "cost_information",
                          "languages_available", "capacity", "source", "notes"]
            
            for field in text_fields:
                if field in options and options[field] is not None:
                    update_data[field] = options[field]
            
            # Boolean field updates
            boolean_fields = ["is_emergency_service", "is_24_hour_service"]
            for field in boolean_fields:
                if field in options and options[field] is not None:
                    # Convert string values to boolean
                    if isinstance(options[field], str):
                        value = options[field].lower()
                        if value in ['true', '1', 'yes', 'y']:
                            update_data[field] = True
                        elif value in ['false', '0', 'no', 'n']:
                            update_data[field] = False
                        else:
                            raise CommandError(f"Invalid boolean value for {field}: {options[field]}")
                    else:
                        update_data[field] = options[field]
            
            # Update the resource if there are field updates
            if update_data:
                updated_resource = self._update_resource(resource, update_data)
                
                # Format and output the response
                from .cli_utils import format_resource_data
                resource_data = format_resource_data(updated_resource, include_related=True)
                
                response = {
                    "command": "update",
                    "message": "Resource updated successfully",
                    "resource_id": updated_resource.id,
                    "timestamp": str(datetime.datetime.now()),
                    "resource": resource_data,
                    "fields_updated": list(update_data.keys())
                }
                
                self._output_json(response)
            else:
                # No field updates, but service areas might be updated later
                # Just output a basic success message
                response = {
                    "command": "update",
                    "message": "Resource service areas updated successfully",
                    "resource_id": resource.id,
                    "timestamp": str(datetime.datetime.now()),
                    "resource": None
                }
                
                self._output_json(response)
            
        except Exception as e:
            raise CommandError(f"Error updating individual fields: {str(e)}")

    def _update_resource(self, resource: Resource, update_data: Dict[str, Any]) -> Resource:
        """
        Update a resource with the provided data.
        
        Args:
            resource: Resource instance to update
            update_data: Dictionary containing field updates
            
        Returns:
            Updated Resource instance
            
        Raises:
            CommandError: If update fails
        """
        try:
            with transaction.atomic():
                # Validate phone number if being updated
                if "phone" in update_data and update_data["phone"]:
                    phone = update_data["phone"]
                    # Remove non-digits for validation
                    import re
                    digits_only = re.sub(r"\D", "", phone)
                    if len(digits_only) < 10:
                        raise CommandError("Phone number must have at least 10 digits")
                    if len(digits_only) > 11:
                        raise CommandError("Phone number cannot have more than 11 digits")
                    if len(digits_only) == 11 and digits_only[0] != "1":
                        raise CommandError("If phone number has 11 digits, it must start with 1 (country code)")
                
                # Set updated_by field
                try:
                    from django.contrib.auth.models import User
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        update_data["updated_by"] = admin_user
                except Exception:
                    # Continue without setting updated_by if user lookup fails
                    pass
                
                # Update the resource
                for field, value in update_data.items():
                    if hasattr(resource, field):
                        setattr(resource, field, value)
                
                # Save the resource
                resource.save()
                
                self.stdout.write(f"Resource '{resource.name}' updated successfully\n")
                return resource
                
        except Exception as e:
            raise CommandError(f"Failed to update resource: {str(e)}")

    def _handle_search(self, **options: Any) -> None:
        """
        Handle the search command.
        
        This method implements comprehensive search functionality using FTS5
        full-text search combined with exact field matching. It supports
        filtering by location, category, and status, and provides pagination
        for large result sets.
        
        Args:
            **options: Command options including query and filters
        """
        try:
            query = options.get("query", "").strip()
            if not query:
                self._output_error("Search query is required")
                return

            # Get filter options
            city_filter = options.get("city", "").strip() if options.get("city") else ""
            state_filter = options.get("state", "").strip() if options.get("state") else ""
            category_filter = options.get("category", "").strip() if options.get("category") else ""
            status_filter = options.get("status", "").strip() if options.get("status") else ""
            limit = options.get("limit", 50)

            # Start with combined search (FTS5 + exact matches)
            queryset = Resource.objects.search_combined(query)

            # Apply additional filters
            if city_filter:
                queryset = queryset.filter(city__icontains=city_filter)

            if state_filter:
                queryset = queryset.filter(state__icontains=state_filter)

            if category_filter:
                # Try to find category by name
                try:
                    category = TaxonomyCategory.objects.filter(
                        name__icontains=category_filter
                    ).first()
                    if category:
                        queryset = queryset.filter(category=category)
                except Exception:
                    # Continue without category filter if lookup fails
                    pass

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Apply limit
            if limit and limit > 0:
                queryset = queryset[:limit]

            # Get results with related data
            resources = list(queryset.select_related("category").prefetch_related(
                "service_types", "coverage_areas"
            ))

            # Format results
            from .cli_utils import format_resource_data
            formatted_results = []
            for resource in resources:
                formatted_results.append(format_resource_data(resource, include_related=True))

            # Prepare response data
            response_data = {
                "command": "search",
                "query": query,
                "filters_applied": {
                    "city": city_filter if city_filter else None,
                    "state": state_filter if state_filter else None,
                    "category": category_filter if category_filter else None,
                    "status": status_filter if status_filter else None,
                    "limit": limit
                },
                "results_count": len(formatted_results),
                "results": formatted_results,
                "search_metadata": {
                    "search_method": "combined_fts5",
                    "fts5_available": True,
                    "fallback_used": False
                }
            }

            # Output success response
            self._output_success(
                f"Search completed successfully. Found {len(formatted_results)} results.",
                response_data
            )

        except Exception as e:
            self._output_error(f"Search failed: {str(e)}")

    def _handle_list_areas(self, **options: Any) -> None:
        """
        Handle the list-areas command.
        
        This method implements the list-areas command functionality, providing filtering,
        pagination, and sorting capabilities for coverage areas. It uses the CoverageArea
        model to efficiently query the database.
        
        Args:
            **options: Command options including filters and pagination
        """
        try:
            # Import CoverageArea model
            from directory.models.geographic.coverage_area import CoverageArea
            
            # Extract options
            kind = options.get("kind")
            search = options.get("search")
            limit = options.get("limit", 50)
            offset = options.get("offset", 0)
            sort_field = options.get("sort", "name")
            sort_order = options.get("order", "asc")
            
            # Build queryset with filters
            queryset = CoverageArea.objects.all()
            
            # Apply filters
            filters_applied = {}
            if kind:
                queryset = queryset.filter(kind=kind)
                filters_applied["kind"] = kind
            
            if search:
                queryset = queryset.filter(name__icontains=search)
                filters_applied["search"] = search
            
            # Apply sorting
            if sort_order == "desc":
                sort_field = f"-{sort_field}"
            
            queryset = queryset.order_by(sort_field)
            
            # Get total count before pagination
            total_count = queryset.count()
            
            # Apply pagination
            page = (offset // limit) + 1
            queryset = queryset[offset:offset + limit]
            
            # Convert to list to avoid lazy evaluation issues
            areas = list(queryset)
            
            # Format areas for output
            formatted_areas = []
            for area in areas:
                area_data = {
                    "id": area.id,
                    "name": area.name,
                    "kind": area.kind,
                    "created_at": area.created_at,
                    "updated_at": area.updated_at,
                    "ext_ids": area.ext_ids,
                    "has_geometry": bool(area.geom or area.center),
                    "radius_m": area.radius_m
                }
                formatted_areas.append(area_data)
            
            # Prepare response data
            response_data = {
                "command": "list-areas",
                "areas": formatted_areas,
                "pagination": {
                    "page": page,
                    "page_size": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": offset + limit < total_count,
                    "has_previous": offset > 0
                },
                "filters_applied": filters_applied,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"List areas completed successfully. Found {total_count} areas.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"List areas failed: {str(e)}")

    def _handle_show_area(self, **options: Any) -> None:
        """
        Handle the show-area command.
        
        This method implements the show-area command functionality, displaying detailed
        information about a specific coverage area including associated resources.
        
        Args:
            **options: Command options including area_id
        """
        try:
            # Import CoverageArea model
            from directory.models.geographic.coverage_area import CoverageArea
            
            # Extract options
            area_id = options.get("area_id")
            
            # Get the coverage area
            try:
                area = CoverageArea.objects.get(id=area_id)
            except CoverageArea.DoesNotExist:
                self._output_error(f"Coverage area with ID {area_id} not found")
                return
            
            # Get associated resources
            resources = area.resources.all()
            
            # Format area data
            area_data = {
                "id": area.id,
                "name": area.name,
                "kind": area.kind,
                "created_at": area.created_at,
                "updated_at": area.updated_at,
                "created_by": {
                    "id": area.created_by.id,
                    "username": area.created_by.username
                } if area.created_by else None,
                "updated_by": {
                    "id": area.updated_by.id,
                    "username": area.updated_by.username
                } if area.updated_by else None,
                "ext_ids": area.ext_ids,
                "geometry": {
                    "has_geom": bool(area.geom),
                    "has_center": bool(area.center),
                    "radius_m": area.radius_m
                },
                "associated_resources": {
                    "count": resources.count(),
                    "resources": []
                }
            }
            
            # Add resource details if any exist
            if resources.exists():
                from .cli_utils import format_resource_data
                for resource in resources:
                    area_data["associated_resources"]["resources"].append(
                        format_resource_data(resource, include_related=False)
                    )
            
            # Prepare response data
            response_data = {
                "command": "show-area",
                "area": area_data,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"Show area completed successfully for area ID {area_id}.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"Show area failed: {str(e)}")

    def _output_json(self, data: Dict[str, Any]) -> None:
        """
        Output data in JSON format.
        
        Args:
            data: Data to output as JSON
        """
        json_output = json.dumps(data, indent=2, default=str)
        self.stdout.write(json_output)

    def _output_error(self, message: str) -> None:
        """
        Output an error message in JSON format.
        
        Args:
            message: Error message to output
        """
        error_data = {
            "error": True,
            "message": message,
            "timestamp": str(datetime.datetime.now())
        }
        self._output_json(error_data)

    def _output_success(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Output a success message in JSON format.
        
        Args:
            message: Success message to output
            data: Optional additional data to include
        """
        success_data = {
            "success": True,
            "message": message,
            "timestamp": str(datetime.datetime.now())
        }
        if data:
            success_data.update(data)
        self._output_json(success_data)

    def _handle_list_categories(self, **options: Any) -> None:
        """
        Handle the list-categories command.
        
        This method implements the list-categories command functionality, providing filtering,
        pagination, and sorting capabilities for taxonomy categories. It uses the TaxonomyCategory
        model to efficiently query the database.
        
        Args:
            **options: Command options including filters and pagination
        """
        try:
            # Import TaxonomyCategory model
            from directory.models import TaxonomyCategory
            
            # Extract options
            search = options.get("search")
            limit = options.get("limit", 50)
            offset = options.get("offset", 0)
            sort_field = options.get("sort", "name")
            sort_order = options.get("order", "asc")
            
            # Build queryset with filters
            queryset = TaxonomyCategory.objects.all()
            
            # Apply filters
            filters_applied = {}
            if search:
                queryset = queryset.filter(name__icontains=search)
                filters_applied["search"] = search
            
            # Apply sorting
            if sort_order == "desc":
                sort_field = f"-{sort_field}"
            
            queryset = queryset.order_by(sort_field)
            
            # Get total count before pagination
            total_count = queryset.count()
            
            # Apply pagination
            page = (offset // limit) + 1
            queryset = queryset[offset:offset + limit]
            
            # Convert to list to avoid lazy evaluation issues
            categories = list(queryset)
            
            # Format categories for output
            formatted_categories = []
            for category in categories:
                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "created_at": category.created_at,
                    "updated_at": category.updated_at,
                    "resource_count": category.resources.count()
                }
                formatted_categories.append(category_data)
            
            # Prepare response data
            response_data = {
                "command": "list-categories",
                "categories": formatted_categories,
                "pagination": {
                    "page": page,
                    "page_size": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": offset + limit < total_count,
                    "has_previous": offset > 0
                },
                "filters_applied": filters_applied,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"List categories completed successfully. Found {total_count} categories.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"List categories failed: {str(e)}")

    def _handle_show_category(self, **options: Any) -> None:
        """
        Handle the show-category command.
        
        This method implements the show-category command functionality, displaying detailed
        information about a specific taxonomy category including associated resources.
        
        Args:
            **options: Command options including category_id
        """
        try:
            category_id = options.get("category_id")
            if not category_id:
                self._output_error("Category ID is required")
                return
            
            # Import TaxonomyCategory model
            from directory.models import TaxonomyCategory
            
            # Get the category
            try:
                category = TaxonomyCategory.objects.get(id=category_id)
            except TaxonomyCategory.DoesNotExist:
                self._output_error(f"Category with ID {category_id} not found")
                return
            
            # Get associated resources
            resources = category.resources.all()
            
            # Format category data
            category_data = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "associated_resources": {
                    "count": resources.count(),
                    "resources": []
                }
            }
            
            # Add resource details if any exist
            if resources.exists():
                from .cli_utils import format_resource_data
                for resource in resources:
                    category_data["associated_resources"]["resources"].append(
                        format_resource_data(resource, include_related=False)
                    )
            
            # Prepare response data
            response_data = {
                "command": "show-category",
                "category": category_data,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"Show category completed successfully for category ID {category_id}.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"Show category failed: {str(e)}")

    def _handle_list_services(self, **options: Any) -> None:
        """
        Handle the list-services command.
        
        This method implements the list-services command functionality, providing filtering,
        pagination, and sorting capabilities for service types. It uses the existing
        ServiceType model to efficiently query the database.
        
        Args:
            **options: Command options including filters and pagination
        """
        try:
            # Extract options
            limit = options.get("limit", 50)
            offset = options.get("offset", 0)
            search = options.get("search")
            sort_field = options.get("sort", "name")
            sort_order = options.get("order", "asc")
            
            # Build queryset with filters
            queryset = ServiceType.objects.all()
            
            # Apply filters
            filters_applied = {}
            if search:
                queryset = queryset.filter(name__icontains=search)
                filters_applied["search"] = search
            
            # Apply sorting
            if sort_order == "desc":
                sort_field = f"-{sort_field}"
            queryset = queryset.order_by(sort_field)
            
            # Apply pagination
            total_count = queryset.count()
            page = (offset // limit) + 1
            services = queryset[offset:offset + limit]
            
            # Format service type data
            formatted_services = []
            for service in services:
                service_data = {
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "created_at": service.created_at,
                    "resource_count": service.resources.count()
                }
                formatted_services.append(service_data)
            
            # Prepare response data
            response_data = {
                "command": "list-services",
                "services": formatted_services,
                "pagination": {
                    "page": page,
                    "page_size": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": offset + limit < total_count,
                    "has_previous": offset > 0
                },
                "filters_applied": filters_applied,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"List services completed successfully. Found {total_count} service types.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"List services failed: {str(e)}")

    def _handle_show_service(self, **options: Any) -> None:
        """
        Handle the show-service command.
        
        This method implements the show-service command functionality, displaying detailed
        information about a specific service type including associated resources.
        
        Args:
            **options: Command options including service_id
        """
        try:
            service_id = options.get("service_id")
            if not service_id:
                self._output_error("Service ID is required")
                return
            
            # Get the service type
            try:
                service = ServiceType.objects.get(id=service_id)
            except ServiceType.DoesNotExist:
                self._output_error(f"Service type with ID {service_id} not found")
                return
            
            # Get associated resources
            resources = service.resources.all()
            
            # Format service type data
            service_data = {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "created_at": service.created_at,
                "associated_resources": {
                    "count": resources.count(),
                    "resources": []
                }
            }
            
            # Add resource details if any exist
            if resources.exists():
                from .cli_utils import format_resource_data
                for resource in resources:
                    service_data["associated_resources"]["resources"].append(
                        format_resource_data(resource, include_related=False)
                    )
            
            # Prepare response data
            response_data = {
                "command": "show-service",
                "service": service_data,
                "metadata": {
                    "processing_timestamp": str(datetime.datetime.now())
                }
            }
            
            # Output success response
            self._output_success(
                f"Show service completed successfully for service ID {service_id}.",
                response_data
            )
            
        except Exception as e:
            self._output_error(f"Show service failed: {str(e)}")

    def _handle_create_service(self, **options: Any) -> None:
        """
        Handle the create-service command.
        
        This method implements the create-service command functionality, allowing users to
        create new service types either interactively or from JSON input. It handles
        validation and returns the created service type details.
        
        Args:
            **options: Command options including JSON data and interactive mode
            
        Raises:
            CommandError: If creation fails or validation errors occur
        """
        try:
            # Extract options
            json_input = options.get("json")
            interactive = options.get("interactive", True)
            
            if json_input:
                # Non-interactive creation from JSON
                self._create_service_from_json(json_input)
            elif interactive:
                # Interactive creation with prompts
                self._create_service_interactive()
            else:
                raise CommandError("Either --json input or --interactive mode must be specified")
                
        except Exception as e:
            raise CommandError(f"Error creating service type: {str(e)}")

    def _create_service_from_json(self, json_input: str) -> None:
        """
        Create a service type from JSON input.
        
        Args:
            json_input: JSON string containing service type data
            
        Raises:
            CommandError: If JSON is invalid or creation fails
        """
        try:
            # Parse and validate JSON input
            from .cli_utils import validate_json_input
            service_data = validate_json_input(json_input)
            
            # Validate required fields
            if "name" not in service_data:
                raise CommandError("Service type name is required")
            
            # Create the service type
            service = ServiceType.objects.create(
                name=service_data["name"],
                description=service_data.get("description", "")
            )
            
            # Format and output the response
            from .cli_utils import format_service_type_data
            formatted_data = format_service_type_data(service)
            
            response = {
                "command": "create-service",
                "message": "Service type created successfully",
                "service_id": service.id,
                "timestamp": str(datetime.datetime.now()),
                "service": formatted_data
            }
            
            self._output_json(response)
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON input: {str(e)}")
        except ValidationError as e:
            raise CommandError(f"Validation error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error creating service type from JSON: {str(e)}")

    def _create_service_interactive(self) -> None:
        """
        Create a service type interactively with user prompts.
        
        This method prompts the user for required and optional service type fields,
        validates the input, and creates the service type. It provides a user-friendly
        interface for service type creation.
        
        Raises:
            CommandError: If creation fails or user cancels
        """
        try:
            self.stdout.write("Creating new service type interactively...\n")
            self.stdout.write("Press Enter to skip optional fields, 'quit' to cancel.\n\n")
            
            # Collect service type data interactively
            service_data = self._collect_service_interactive_input()
            
            if not service_data:
                self.stdout.write("Service type creation cancelled.\n")
                return
            
            # Create the service type
            service = ServiceType.objects.create(
                name=service_data["name"],
                description=service_data.get("description", "")
            )
            
            # Format and output the response
            from .cli_utils import format_service_type_data
            formatted_data = format_service_type_data(service)
            
            response = {
                "command": "create-service",
                "message": "Service type created successfully",
                "service_id": service.id,
                "timestamp": str(datetime.datetime.now()),
                "service": formatted_data
            }
            
            self._output_json(response)
            
        except Exception as e:
            raise CommandError(f"Error creating service type interactively: {str(e)}")

    def _collect_service_interactive_input(self) -> Optional[Dict[str, Any]]:
        """
        Collect service type data interactively from user input.
        
        Returns:
            Dict containing the collected service type data, or None if cancelled
        """
        try:
            service_data = {}
            
            # Get required name
            while True:
                name = input("Service type name (required): ").strip()
                if name.lower() == "quit":
                    return None
                if name:
                    service_data["name"] = name
                    break
                print("❌ Service type name is required!")
            
            # Get optional description
            description = input("Description (optional): ").strip()
            if description.lower() == "quit":
                return None
            if description:
                service_data["description"] = description
            
            return service_data
            
        except (EOFError, KeyboardInterrupt):
            return None

    def _handle_update_service(self, **options: Any) -> None:
        """
        Handle the update-service command.
        
        This method implements the update-service command functionality, allowing users to
        update existing service types with field-level changes. It supports both
        individual field updates and bulk updates from JSON input.
        
        Args:
            **options: Command options including service_id and update data
            
        Raises:
            CommandError: If update fails or validation errors occur
        """
        try:
            # Extract options
            service_id = options.get("service_id")
            json_input = options.get("json")
            name = options.get("name")
            description = options.get("description")
            
            if not service_id:
                raise CommandError("Service ID is required for update")
            
            # Get the service type
            try:
                service = ServiceType.objects.get(id=service_id)
            except ServiceType.DoesNotExist:
                raise CommandError(f"Service type with ID {service_id} not found")
            
            if json_input:
                # Bulk update from JSON
                self._update_service_from_json(service, json_input)
            else:
                # Individual field updates
                self._update_service_individual_fields(service, name, description)
                
        except Exception as e:
            raise CommandError(f"Error updating service type: {str(e)}")

    def _update_service_from_json(self, service: ServiceType, json_input: str) -> None:
        """
        Update a service type from JSON input.
        
        Args:
            service: ServiceType instance to update
            json_input: JSON string containing update data
            
        Raises:
            CommandError: If JSON is invalid or update fails
        """
        try:
            # Parse and validate JSON input
            from .cli_utils import format_service_type_data
            service_data = validate_json_input(json_input)
            
            # Update fields
            if "name" in service_data:
                service.name = service_data["name"]
            if "description" in service_data:
                service.description = service_data["description"]
            
            # Save changes
            service.save()
            
            # Format and output the response
            formatted_data = format_service_type_data(service)
            
            response = {
                "command": "update-service",
                "message": "Service type updated successfully",
                "service_id": service.id,
                "timestamp": str(datetime.datetime.now()),
                "service": formatted_data
            }
            
            self._output_json(response)
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON input: {str(e)}")
        except ValidationError as e:
            raise CommandError(f"Validation error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error updating service type from JSON: {str(e)}")

    def _update_service_individual_fields(self, service: ServiceType, name: Optional[str], description: Optional[str]) -> None:
        """
        Update individual fields of a service type.
        
        Args:
            service: ServiceType instance to update
            name: New name for the service type
            description: New description for the service type
        """
        try:
            # Track changes
            changes_made = []
            
            # Update name if provided
            if name is not None:
                service.name = name
                changes_made.append("name")
            
            # Update description if provided
            if description is not None:
                service.description = description
                changes_made.append("description")
            
            # Save changes if any were made
            if changes_made:
                service.save()
                
                # Format and output the response
                from .cli_utils import format_service_type_data
                formatted_data = format_service_type_data(service)
                
                response = {
                    "command": "update-service",
                    "message": f"Service type updated successfully. Changed fields: {', '.join(changes_made)}",
                    "service_id": service.id,
                    "timestamp": str(datetime.datetime.now()),
                    "service": formatted_data
                }
                
                self._output_json(response)
            else:
                self.stdout.write("ℹ️  No changes specified for service type\n")
                
        except Exception as e:
            raise CommandError(f"Error updating service type fields: {str(e)}")
