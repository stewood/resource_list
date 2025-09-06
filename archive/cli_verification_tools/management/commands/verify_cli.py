#!/usr/bin/env python3
"""
Resource Verification CLI Tool

This module provides a command-line interface for finding resources that need verification
in the Community Resource Directory. It implements the verification process outlined in
VERIFICATION_PROCESS.md with priority-based resource selection.

Commands:
    - verify: Find the next resource to verify based on priority criteria

Usage:
    python manage.py verify_cli verify [options]

Examples:
    python manage.py verify_cli verify
    python manage.py verify_cli verify --verbose
    python manage.py verify_cli verify --resource-id 355

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import argparse
import datetime
import json
import subprocess
import sys
import os
from typing import Any, Dict, List, Optional, Union
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from directory.models import Resource, CoverageArea
from directory.models.verification_models import (
    WebsiteDiscoveryResult,
    ResourceData,
    VerificationResult,
    FieldVerificationResult,
    CursorAgentResult
)
from directory.utils.verification_utils import (
    calculate_days_since_verification,
    determine_verification_priority,
    format_discovered_urls_for_prompt
)
from directory.utils.json_utils import (
    extract_json_from_text,
    parse_website_discovery_result,
    format_json_for_display
)
from directory.config.verification_config import (
    VerificationConfig,
    DisplayConfig,
    ProcessConfig,
    default_verification_config,
    default_display_config,
    default_process_config
)
from directory.services.website_discovery_service import WebsiteDiscoveryService
from directory.services.resource_verification_service import ResourceVerificationService
from directory.services.field_verification_service import FieldVerificationService
from directory.services.cursor_agent_service import CursorAgentService
from directory.services.output_formatter import OutputFormatter

# Add the project root to the path for importing test modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import the new cursor parser functionality
try:
    from test_cursor_parser import parse_cursor_agent_output
    from rich import print as rprint
    from rich.json import JSON
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Command(BaseCommand):
    """
    Main command class for resource verification CLI operations.

    This command provides an interface for finding resources that need verification
    based on priority criteria defined in VERIFICATION_PROCESS.md with priority-based
    resource selection.

    Attributes:
        help: Command help text
        requires_migrations_checks: Whether to check migrations before running

    Subcommands:
        verify: Find the next resource to verify based on priority criteria
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the command with service dependencies.
        """
        super().__init__(*args, **kwargs)

        # Initialize configuration
        self.config = default_verification_config

        # Initialize services
        self.website_discovery_service = WebsiteDiscoveryService(self.config)
        self.resource_verification_service = ResourceVerificationService(self.config)
        self.field_verification_service = FieldVerificationService(self.config)
        self.cursor_agent_service = CursorAgentService()
        self.output_formatter = OutputFormatter()

    help = """Find resources that need verification and discover their websites through the command line interface

This CLI tool provides resource verification capabilities for the Community Resource Directory.
It implements the verification process outlined in VERIFICATION_PROCESS.md with priority-based
resource selection, AI-powered website discovery, and field-by-field verification.

AVAILABLE COMMANDS:
  verify           Find the next resource to verify, discover websites, and verify fields

EXAMPLES:
  # Find next resource to verify with full verification process
  python manage.py verify_cli verify

  # Find next resource with verbose output
  python manage.py verify_cli verify --verbose

  # Verify a specific resource by ID
  python manage.py verify_cli verify --resource-id 355

  # Verify a specific resource with verbose output
  python manage.py verify_cli verify --resource-id 355 --verbose

OUTPUT FORMAT:
  All commands output JSON with consistent structure including:
  - success/error status
  - timestamp
  - command executed
  - next resource to verify with complete details
  - available service areas for assignment
  - metadata and priority information
  - website discovery results
  - field verification results

For detailed help on any command, use: python manage.py verify_cli <command> --help"""

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

        # Verify command
        verify_parser = subparsers.add_parser(
            "verify",
            help="Find the next resource to verify, discover websites, and verify fields",
            description="""Find the next resource that needs verification and perform comprehensive verification using AI-powered search and field verification.
            
This command identifies resources that need verification in the following priority order:
1. Resources with no verification date AND no service areas defined (highest priority)
2. Resources with no verification date (high priority)
3. Resources with expired verification dates (medium priority)

The command performs a two-step verification process:
1. Website Discovery: AI-powered search to discover official websites and contact information
2. Field Verification: AI-powered verification of basic resource information using London, KY focused research

The command returns the resource with the lowest ID that meets the criteria, along with
complete resource information, available service areas for assignment, website discovery results, and field verification results.

You can also specify a specific resource ID to verify that resource regardless of priority.

EXAMPLES:
  # Find next resource to verify with full verification process
  python manage.py verify_cli verify

  # Find next resource with verbose output
  python manage.py verify_cli verify --verbose

  # Verify a specific resource by ID
  python manage.py verify_cli verify --resource-id 355

OUTPUT: JSON with the next resource to verify, complete details, available service areas, website discovery results, and field verification results."""
        )
        self._add_verify_arguments(verify_parser)

    def _add_verify_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the verify command.
        
        Args:
            parser: Parser to add arguments to
        """
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output with detailed resource information"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1,
            help="Maximum number of resources to return (default: 1)"
        )
        parser.add_argument(
            "--resource-id",
            type=int,
            help="Discover websites for a specific resource by ID (overrides priority-based selection)"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle the command execution.
        
        This method routes to the appropriate subcommand handler based on the
        command argument.
        
        Args:
            *args: Positional arguments
            **options: Command options
            
        Raises:
            CommandError: If command execution fails
        """
        command = options.get("command")
        
        if not command:
            self.print_help("manage.py", "verify_cli")
            return

        # Route to appropriate command handler
        try:
            if command == "verify":
                self._handle_verify(**options)
            else:
                raise CommandError(f"Unknown command: {command}")
        except Exception as e:
            self._output_error(str(e))
            sys.exit(1)

    def _handle_verify(self, **options: Any) -> None:
        """
        Handle the verify command.
        
        This method implements the verify command functionality, finding the next resource to verify
        based on priority criteria defined in VERIFICATION_PROCESS.md and performing website discovery.
        
        Args:
            **options: Command options including verbose output, limit, and resource-id
        """
        try:
            verbose = options.get("verbose", False)
            limit = options.get("limit", 1)
            resource_id = options.get("resource_id")
            timeout = self.config.default_timeout_seconds
            
            # If a specific resource ID is provided, discover websites for that resource
            if resource_id:
                try:
                    resource = Resource.objects.get(id=resource_id)
                    resources_to_verify = [resource]
                    response_message = f"Discovering websites for specific resource ID {resource_id}."
                except Resource.DoesNotExist:
                    self._output_error(f"Resource with ID {resource_id} not found.")
                    return
            else:
                # Find resources that need verification based on priority criteria
                resources_to_verify = self.resource_verification_service.find_resources_needing_verification(limit)
                response_message = f"Found {len(resources_to_verify)} resource(s) needing website discovery."
            
            if not resources_to_verify:
                self._output_success(
                    "No resources need website discovery.",
                    {
                        "command": "verify",
                        "resources_found": 0,
                        "message": "All resources are up to date with website discovery",
                        "metadata": {
                            "processing_timestamp": timezone.now().isoformat(),
                            "verification_criteria_applied": "Priority-based selection" if not resource_id else f"Specific resource ID {resource_id}"
                        }
                    }
                )
                return
            
            # Format response data
            response_data = {
                "command": "verify",
                "resources_found": len(resources_to_verify),
                "resources": [],
                "metadata": {
                    "processing_timestamp": timezone.now().isoformat(),
                    "verification_criteria_applied": "Priority-based selection" if not resource_id else f"Specific resource ID {resource_id}",
                    "priority_order": [
                        "No verification date + no service areas (highest)",
                        "No verification date (high)",
                        "Expired verification date (medium)"
                    ] if not resource_id else ["Specific resource ID specified"]
                }
            }
            
            # Process each resource
            for resource in resources_to_verify:
                resource_data = self.resource_verification_service.format_resource_for_verification(resource, verbose)
                
                # Step 1: Website Discovery (always runs first)
                self.stdout.write("\n" + "="*100 + "\n")
                self.stdout.write(f"🔍 STEP 1: WEBSITE DISCOVERY\n")
                self.stdout.write(f"Resource: {resource.name}\n")
                self.stdout.write(f"Category: {resource.category}\n")
                self.stdout.write(f"Location: {resource.city}, {resource.state}\n")
                self.stdout.write("="*100 + "\n")
                website_result = self.website_discovery_service.discover_websites(resource_data, timeout)
                # Convert WebsiteDiscoveryResult to dict for backward compatibility
                resource_data_dict = {
                    "id": resource_data.id,
                    "name": resource_data.name,
                    "status": resource_data.status,
                    "category": resource_data.category,
                    "description": resource_data.description,
                    "city": resource_data.city,
                    "state": resource_data.state,
                    "county": resource_data.county,
                    "verification_status": resource_data.verification_status,
                    "service_areas": resource_data.service_areas,
                    "service_types": resource_data.service_types,
                    "website_discovery": {
                        "status": website_result.status,
                        "message": website_result.message,
                        "urls_found": website_result.urls_found,
                        "discovered_urls": website_result.discovered_urls,
                        "tool_calls_count": website_result.tool_calls_count,
                        "duration_ms": website_result.duration_ms,
                        "timestamp": website_result.timestamp,
                        "search_strategy": website_result.search_strategy,
                        "total_urls": website_result.total_urls,
                        "search_notes": website_result.search_notes
                    }
                }
                
                # Continue to next step regardless of website discovery status
                
                # Step 2: Field Verification
                self.stdout.write("\n" + "="*100 + "\n")
                self.stdout.write(f"🔍 STEP 2: FIELD VERIFICATION\n")
                self.stdout.write(f"Resource: {resource.name}\n")
                self.stdout.write(f"Verifying basic resource information using AI research prompt...\n")
                self.stdout.write("="*100 + "\n")
                
                field_verification_result = self.field_verification_service.verify_fields(
                    resource_data, 
                    resource_data_dict["website_discovery"], 
                    timeout
                )
                
                # Add field verification results to the resource data
                resource_data_dict["field_verification"] = {
                    "status": field_verification_result.status,
                    "message": field_verification_result.message,
                    "fields_verified": field_verification_result.fields_verified,
                    "field_results": field_verification_result.field_results,
                    "tool_calls_count": field_verification_result.tool_calls_count,
                    "duration_ms": field_verification_result.duration_ms,
                    "timestamp": field_verification_result.timestamp,
                    "verification_strategy": field_verification_result.verification_strategy,
                    "total_fields": field_verification_result.total_fields,
                    "verification_notes": field_verification_result.verification_notes,
                    "resource_name": field_verification_result.resource_name,
                    "category": field_verification_result.category,
                    "description": field_verification_result.description,
                    "location": field_verification_result.location,
                    "contact_info": field_verification_result.contact_info,
                    "sources": field_verification_result.sources
                }
                
                # Continue to final response regardless of field verification status
                
                # Add resource data to response (field verification complete)
                response_data["resources"].append(resource_data_dict)
            
            # Output success response
            self._output_success(response_message, response_data)
            
        except Exception as e:
            self._output_error(f"Error finding resources to verify: {str(e)}")

    def _output_success(self, message: str, data: Dict[str, Any]) -> None:
        """
        Output a successful response.

        Args:
            message: Success message
            data: Response data
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": timezone.now().isoformat(),
            "data": data
        }
        
        # Output as JSON
        self.stdout.write(json.dumps(response, indent=2, default=str))
        self.stdout.write("\n")

    def _output_error(self, message: str) -> None:
        """
        Output an error response.
        
        Args:
            message: Error message
        """
        response = {
            "success": False,
            "error": message,
            "timestamp": timezone.now().isoformat()
        }
        
        # Output as JSON
        self.stdout.write(json.dumps(response, indent=2, default=str))
        self.stdout.write("\n")
