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
from typing import Any, Dict, List, Optional, Union
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from directory.models import Resource, CoverageArea


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

    help = """Find resources that need verification through the command line interface

This CLI tool provides resource verification capabilities for the Community Resource Directory.
It implements the verification process outlined in VERIFICATION_PROCESS.md with priority-based
resource selection.

AVAILABLE COMMANDS:
  verify           Find the next resource to verify based on priority criteria

EXAMPLES:
  # Find next resource to verify
  python manage.py verify_cli verify

  # Find next resource to verify with verbose output
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
  - website discovery results (always included)
  - Chunk 1 verification results (Identity & Contact Information)

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
            help="Find the next resource to verify based on priority criteria",
            description="""Find the next resource that needs verification based on priority criteria.
            
This command identifies resources that need verification in the following priority order:
1. Resources with no verification date AND no service areas defined (highest priority)
2. Resources with no verification date (high priority)
3. Resources with expired verification dates (medium priority)

The command returns the resource with the lowest ID that meets the criteria, along with
complete resource information, available service areas for assignment, website discovery results, and comprehensive verification data.

You can also specify a specific resource ID to verify that resource regardless of priority.

EXAMPLES:
  # Find next resource to verify
  python manage.py verify_cli verify

  # Find next resource to verify with verbose output
  python manage.py verify_cli verify --verbose

  # Verify a specific resource by ID
  python manage.py verify_cli verify --resource-id 355

OUTPUT: JSON with the next resource to verify, complete details, available service areas, and website discovery results."""
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
            help="Verify a specific resource by ID (overrides priority-based selection)"
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
        based on priority criteria defined in VERIFICATION_PROCESS.md and always running website discovery.
        
        Args:
            **options: Command options including verbose output, limit, and resource-id
        """
        try:
            verbose = options.get("verbose", False)
            limit = options.get("limit", 1)
            resource_id = options.get("resource_id")
            timeout = 180  # Hardcoded timeout for AI responses (increased for real web searches)
            
            # If a specific resource ID is provided, verify that resource
            if resource_id:
                try:
                    resource = Resource.objects.get(id=resource_id)
                    resources_to_verify = [resource]
                    response_message = f"Verifying specific resource ID {resource_id}."
                except Resource.DoesNotExist:
                    self._output_error(f"Resource with ID {resource_id} not found.")
                    return
            else:
                # Find resources that need verification based on priority criteria
                resources_to_verify = self._find_resources_needing_verification(limit)
                response_message = f"Found {len(resources_to_verify)} resource(s) needing verification."
            
            if not resources_to_verify:
                self._output_success(
                    "No resources need verification.",
                    {
                        "command": "verify",
                        "resources_found": 0,
                        "message": "All resources are up to date with verification",
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
                resource_data = self._format_resource_for_verification(resource, verbose)
                
                # Step 1: Website Discovery (always runs first)
                self.stdout.write(f"\n🔍 STEP 1: Starting website discovery for resource: {resource.name}\n")
                website_result = self._discover_websites(resource_data, timeout)
                resource_data["website_discovery"] = website_result
                
                # Step 2: Chunk 1 Verification (Identity & Contact Information)
                self.stdout.write(f"\n🔍 STEP 2: Starting Chunk 1 verification (Identity & Contact) for resource: {resource.name}\n")
                chunk_1_result = self._verify_chunk_1_identity_contact(resource_data, timeout)
                resource_data["chunk_1_verification"] = chunk_1_result
                
                response_data["resources"].append(resource_data)
            
            # Output success response
            self._output_success(response_message, response_data)
            
        except Exception as e:
            self._output_error(f"Error finding resources to verify: {str(e)}")



    def _discover_websites(self, resource_data: Dict[str, Any], timeout_seconds: int = 180) -> Dict[str, Any]:
        """
        Use Cursor Agent to discover websites with information about this resource.
        
        Args:
            resource_data: Formatted resource data
            timeout_seconds: Timeout in seconds for AI response
            
        Returns:
            Dictionary with website discovery results
        """
        try:
            # Create a comprehensive prompt for website discovery with chain of thought and JSON template
            website_prompt = f"""
Find as many URLs as possible with information about this resource using chain of thought reasoning.

Resource: {resource_data['name']}
Category: {resource_data['category']}
Description: {resource_data['description']}
Location: {resource_data['city']}, {resource_data['state']}

Think through this step by step:

1. First, consider what type of organization this is and what search terms would be most effective
2. Think about where such organizations typically have online presence
3. Consider both official and unofficial sources that might mention this resource
4. Plan your search strategy to cover multiple angles

Search for:
- Official organization website
- Social media profiles (Facebook, Twitter, LinkedIn, Instagram)
- Directory listings (Google Business, Yelp, Yellow Pages)
- News articles or press coverage
- Government or nonprofit database listings
- Service provider directories
- Any other websites mentioning this resource

IMPORTANT: Follow this three-step process:
1. Use the web_search tool to search for URLs and information about this organization
2. Use pull_markdown to extract content from discovered websites
3. Use render_html only if you need to see the visual layout of complex pages

CRITICAL: Before launching any MCP tool, explain what you are about to do and why. For example:
- "I will now use web_search to search for '{resource_data['name']} {resource_data['city']}' because this will find official and directory listings"
- "I will now use pull_markdown to extract content from [URL] because this will give me clean text to analyze"
- "I will now use render_html to view [URL] because this page may have complex formatting that needs visual inspection"

AVAILABLE MCP TOOLS:
- web_search: Search the web using DuckDuckGo (privacy-focused, no rate limits)
- pull_markdown: Convert any webpage to clean Markdown format
- render_html: Render HTML content in browser for visual inspection

Use these tools strategically - start with web search, then pull content from promising URLs.

MCP TOOLS USAGE GUIDE:
- web_search: Use for finding URLs and general information. Query format: organization name + location + "contact" or "phone" or "address"
- pull_markdown: Use for extracting readable text from websites. Best for contact pages, about pages, and service descriptions
- render_html: Use only when you need to see interactive elements, forms, or complex page layouts that markdown can't capture properly

EXAMPLE WORKFLOW:
1. "I will use web_search with query '{resource_data['name']} {resource_data['city']} contact information' to find official contact details"
2. "Based on search results, I will use pull_markdown on the official website to extract contact information"
3. "If the website has complex forms, I will use render_html to see the full contact page layout"

Use chain of thought to explain your search process, then provide your findings in this exact JSON format:

{{
  "search_strategy": "Brief description of your search approach",
  "urls_found": [
    {{
      "url": "https://example.com",
      "type": "official_website|social_media|directory|news|other",
      "description": "Brief description of what this URL contains",
      "reason": "Why this URL is relevant and useful for verification"
    }}
  ],
  "total_urls": 0,
  "search_notes": "Any additional notes about your search process"
}}

IMPORTANT: Complete the JSON structure above and then print <|END|> to signal completion.
"""
            
            # Show the prompt being sent
            self.stdout.write("\nPROMPT BEING SENT TO CURSOR AGENT:\n")
            self.stdout.write(website_prompt)
            self.stdout.write("\n")
            
            # Use cursor-agent with MCP tools for website discovery
            result = self._smart_cursor_call(website_prompt, timeout_seconds=60)
            
            if result and not result.startswith("Error:"):
                # Parse the result to extract structured data
                parsed_result = self._parse_website_discovery_result(result)
                
                return {
                    "status": "success",
                    "response": {"text": result},
                    "raw_output": result,
                    "parsed_data": parsed_result,
                    "timestamp": timezone.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": result,
                    "timestamp": timezone.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to discover websites: {str(e)}",
                "timestamp": timezone.now().isoformat()
            }

    def _mock_website_discovery_response(self):
        """Return a mock response for website discovery until MCP tools are working"""
        mock_json = '''{
  "search_strategy": "Mock search strategy for testing - would use web_search tool in production",
  "urls_found": [
    {
      "url": "https://bwjp.org/",
      "type": "official_website",
      "description": "Official website of Battered Women's Justice Project",
      "reason": "Primary source for organization information and contact details"
    },
    {
      "url": "https://bwjp.org/about/contact/",
      "type": "official_website",
      "description": "Contact page with phone, email, and address information",
      "reason": "Contains detailed contact information for verification"
    },
    {
      "url": "https://www.facebook.com/bwjp.org",
      "type": "social_media",
      "description": "Facebook page for Battered Women's Justice Project",
      "reason": "Social media presence for additional verification"
    }
  ],
  "total_urls": 3,
  "search_notes": "Mock response - MCP tools not currently available. In production, this would use web_search to find actual URLs."
}'''
        return mock_json

    def _mock_verification_response(self):
        """Return a mock response for verification until MCP tools are working"""
        mock_json = '''{
  "verification_results": {
    "name": {
      "verified_value": "Battered Women's Justice Project (BWJP)",
      "source_url": "https://bwjp.org/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "Battered Women's Justice Project (BWJP) - Home",
      "discrepancy_found": false,
      "verification_notes": "Name matches exactly on official website"
    },
    "category": {
      "verified_value": "Hotlines",
      "source_url": "https://bwjp.org/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "8",
      "evidence_quote": "Technical assistance for domestic violence cases",
      "discrepancy_found": false,
      "verification_notes": "Organization provides technical assistance for DV cases"
    },
    "description": {
      "verified_value": "BWJP is a collective of national policy and practice centers that provides technical assistance to professionals working with domestic violence cases. They offer resources, training, consultations, and research at the intersection of gender-based violence and legal systems. BWJP recently merged with Global Rights for Women to expand their global impact.",
      "source_url": "https://bwjp.org/about/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "9",
      "evidence_quote": "BWJP provides technical assistance to professionals working with domestic violence cases...",
      "discrepancy_found": false,
      "verification_notes": "Description matches official website content"
    },
    "phone": {
      "verified_value": "(800) 903-0111",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "Phone: (800) 903-0111",
      "discrepancy_found": false,
      "verification_notes": "Phone number found on official contact page"
    },
    "email": {
      "verified_value": "technicalassistance@bwjp.org",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "Email: technicalassistance@bwjp.org",
      "discrepancy_found": false,
      "verification_notes": "Email found on official contact page"
    },
    "website": {
      "verified_value": "https://bwjp.org/",
      "source_url": "https://bwjp.org/",
      "verification_method": "web_search",
      "confidence_level": "10",
      "evidence_quote": "Official website URL",
      "discrepancy_found": false,
      "verification_notes": "Website is functional and matches search results"
    },
    "address": {
      "verified_value": "540 Fairview Avenue N, Suite 208",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "540 Fairview Avenue N, Suite 208, St. Paul, MN 55104",
      "discrepancy_found": false,
      "verification_notes": "Address found on official contact page"
    },
    "city": {
      "verified_value": "St. Paul",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "St. Paul, MN 55104",
      "discrepancy_found": false,
      "verification_notes": "City matches address on contact page"
    },
    "state": {
      "verified_value": "MN",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "St. Paul, MN 55104",
      "discrepancy_found": false,
      "verification_notes": "State matches address on contact page"
    },
    "county": {
      "verified_value": "Ramsey",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "9",
      "evidence_quote": "Located in Ramsey County, Minnesota",
      "discrepancy_found": false,
      "verification_notes": "County verified through address location"
    },
    "postal_code": {
      "verified_value": "55104",
      "source_url": "https://bwjp.org/about/contact/",
      "verification_method": "web_search + pull_markdown",
      "confidence_level": "10",
      "evidence_quote": "St. Paul, MN 55104",
      "discrepancy_found": false,
      "verification_notes": "Postal code found on contact page"
    }
  },
  "overall_confidence": "9.5",
  "verification_summary": "Mock verification - all fields verified successfully using web_search and pull_markdown tools",
  "sources_consulted": [
    {
      "url": "https://bwjp.org/",
      "type": "primary",
      "reliability_score": "10",
      "fields_verified": ["name", "category", "description", "website"]
    },
    {
      "url": "https://bwjp.org/about/contact/",
      "type": "primary",
      "reliability_score": "10",
      "fields_verified": ["phone", "email", "address", "city", "state", "postal_code"]
    }
  ]
}'''
        return mock_json

    def _parse_website_discovery_result(self, raw_result: str) -> Dict[str, Any]:
        """
        Parse the website discovery result from Cursor Agent to extract structured data.
        
        Args:
            raw_result: Raw text response from Cursor Agent
            
        Returns:
            Dictionary with parsed website discovery data
        """
        try:
            # Try to extract JSON from the response
            json_start = raw_result.find('{')
            json_end = raw_result.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return {
                    "parse_status": "error",
                    "error": "No JSON structure found in website discovery response",
                    "extracted_data": None
                }
            
            # Extract the JSON portion
            json_text = raw_result[json_start:json_end]
            
            try:
                # Parse the JSON
                parsed_json = json.loads(json_text)
                
                # Validate and structure the parsed data
                structured_data = {
                    "parse_status": "success",
                    "search_strategy": parsed_json.get("search_strategy", ""),
                    "urls_found": parsed_json.get("urls_found", []),
                    "total_urls": parsed_json.get("total_urls", 0),
                    "search_notes": parsed_json.get("search_notes", "")
                }
                
                # Add URL statistics by type
                urls_by_type = {}
                for url_data in structured_data["urls_found"]:
                    url_type = url_data.get("type", "other")
                    if url_type not in urls_by_type:
                        urls_by_type[url_type] = []
                    urls_by_type[url_type].append(url_data)
                
                structured_data["urls_by_type"] = urls_by_type
                structured_data["url_type_counts"] = {url_type: len(urls) for url_type, urls in urls_by_type.items()}
                
                return structured_data
                
            except json.JSONDecodeError as json_error:
                return {
                    "parse_status": "error",
                    "error": f"Failed to parse JSON: {str(json_error)}",
                    "raw_text": json_text,
                    "extracted_data": None
                }
                
        except Exception as e:
            return {
                "parse_status": "error",
                "error": f"Failed to parse website discovery result: {str(e)}",
                "raw_text": raw_result,
                "extracted_data": None
            }

    def _verify_chunk_1_identity_contact(self, resource_data: Dict[str, Any], timeout_seconds: int = 180) -> Dict[str, Any]:
        """
        Verify Chunk 1: Identity & Contact Information using Cursor Agent.
        
        This chunk verifies:
        - Name, category, description
        - Phone, email, website
        - Address (street, city, state, county, postal code)
        
        Args:
            resource_data: Formatted resource data
            timeout_seconds: Timeout in seconds for AI response
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Create structured verification prompt for Chunk 1
            verification_prompt = f"""
VERIFY IDENTITY & CONTACT INFORMATION

Resource: {resource_data['name']} (ID: {resource_data['id']})

CURRENT DATA TO VERIFY:
- Name: {resource_data['name']}
- Category: {resource_data['category']}
- Description: {resource_data['description']}
- Phone: {resource_data.get('contact_information', {}).get('phone', 'Not provided')}
- Email: {resource_data.get('contact_information', {}).get('email', 'Not provided')}
- Website: {resource_data.get('contact_information', {}).get('website', 'Not provided')}
- Address: {resource_data.get('contact_information', {}).get('address1', 'Not provided')}
- City: {resource_data['city']}
- State: {resource_data['state']}
- County: {resource_data['county']}
- Postal Code: {resource_data.get('contact_information', {}).get('postal_code', 'Not provided')}

DISCOVERED WEBSITES FROM STEP 1:
{self._format_discovered_urls_for_prompt(resource_data.get('website_discovery', {}))}

VERIFICATION REQUIREMENTS:
1. Use web_search to search for current information about this organization
2. Use pull_markdown to extract content from discovered websites
3. Use render_html only for complex pages that need visual inspection

CRITICAL: Before launching any MCP tool, explain what you are about to do and why. For example:
- "I will now use web_search to search for '{resource_data['name']} contact information' because I need to find current phone and email details"
- "I will now use pull_markdown to extract content from [URL] because this appears to be their official website"
- "I will now use render_html to view [URL] because this page may have complex contact forms or dynamic content"
3. For each field, provide:

VALID CATEGORIES TO VERIFY AGAINST:
- Hotline
- Counseling
- Housing
- Food Assistance
- Legal Services
- Healthcare
- Employment
- Transportation
- Education
- Child Care
- Veterans Services
- Domestic Violence
- Substance Abuse
- Emergency Services
- Financial Assistance
- Food Pantry
- Emergency Shelter
- Transitional Housing
- Mental Health Counseling
- Substance Abuse Treatment
- Medical Care
- Legal Aid
- Job Training
- Utility Assistance
- Pet Care
- Health Education
- Mental Health Support
- Health
- Emergency Preparedness
- 24/7 emergency shelter
- meals
- showers
- personal hygiene items
- laundry facilities
- clothing
- case management services

5. For each field, provide:
   - VERIFIED_VALUE: What you actually found in sources
   - SOURCE_URL: Exact URL where found (must be accessible)
   - VERIFICATION_METHOD: How verified (direct observation, web search, etc.)
   - CONFIDENCE_LEVEL: Use this scale from VERIFICATION_PROCESS.md:
     * 10: Direct official source, exact match
     * 9: Official source, minor variation
     * 8: Reliable third-party source, exact match
     * 7: Reliable third-party source, minor variation
     * 6: Multiple sources agree
     * 5: Single reliable source
     * 4: Partial verification possible
     * 3: Limited verification
     * 2: Minimal verification
     * 1: Cannot verify
   - EVIDENCE_QUOTE: Direct quote from source (if applicable)
   - DISCREPANCY_FOUND: YES/NO - If YES, describe the difference
   - VERIFICATION_NOTES: Any additional verification details

6. CRITICAL ANTI-HALLUCINATION RULES:
   - Use web_search for web searches (privacy-focused, no rate limiting)
   - Use pull_markdown to extract clean content from websites
   - Use render_html only when visual inspection is necessary
   - ALWAYS explain what you are doing before using any MCP tool with specific reasoning
   - Use ONLY information found in actual sources - NO assumptions or inferences
   - If information cannot be verified, mark as UNVERIFIABLE with explanation
   - Require actual accessible URLs for all sources
   - Demand specific evidence quotes when possible
   - Acknowledge any verification limitations

7. VERIFICATION SCALE (from VERIFICATION_PROCESS.md):
   - 10: Direct verification from primary sources (official website, direct contact)
   - 9: Official source, minor variation
   - 8: Reliable third-party source, exact match
   - 7: Reliable third-party source, minor variation
   - 6: Multiple sources agree
   - 5: Single reliable source
   - 4: Partial verification possible
   - 3: Limited verification
   - 2: Minimal verification
   - 1: Cannot verify

MCP TOOLS WORKFLOW FOR VERIFICATION:
1. Use web_search first to find the most current information
2. Use pull_markdown to extract content from official sources
3. Use render_html only for complex pages with dynamic content

TOOL SELECTION CRITERIA:
- Use web_search when: You need to find current information or verify against multiple sources
- Use pull_markdown when: You have a specific URL and need clean, readable content
- Use render_html when: You need to see interactive forms, maps, or complex layouts

OUTPUT FORMAT (JSON):
{{
  "verification_results": {{
    "name": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "category": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "description": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "phone": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "email": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "website": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "address": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "city": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "state": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "county": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }},
    "postal_code": {{
      "verified_value": "string",
      "source_url": "string",
      "verification_method": "string",
      "confidence_level": "string",
      "evidence_quote": "string",
      "discrepancy_found": "boolean",
      "verification_notes": "string"
    }}
  }},
  "overall_confidence": "string",
  "verification_summary": "string",
  "sources_consulted": [
    {{
      "url": "string",
      "type": "primary|secondary|tertiary",
      "reliability_score": "1-10",
      "fields_verified": ["list", "of", "fields"]
    }}
  ]
}}

IMPORTANT: Complete the JSON structure above and then print <|END|> to signal completion.
"""
            
            # Show the prompt being sent
            self.stdout.write("\n🔍 CHUNK 1 VERIFICATION PROMPT BEING SENT TO CURSOR AGENT:\n")
            self.stdout.write("=" * 60 + "\n")
            self.stdout.write(verification_prompt)
            self.stdout.write("\n" + "=" * 60 + "\n")
            
            # Use cursor-agent with MCP tools for verification
            result = self._smart_cursor_call(verification_prompt, timeout_seconds=120)
            
            if result and not result.startswith("Error:"):
                # Parse the verification result
                parsed_result = self._parse_verification_result(result)
                
                return {
                    "status": "success",
                    "chunk": "identity_contact",
                    "response": {"text": result},
                    "raw_output": result,
                    "parsed_data": parsed_result,
                    "timestamp": timezone.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "chunk": "identity_contact",
                    "error": result,
                    "timestamp": timezone.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "chunk": "identity_contact",
                "error": f"Failed to verify Chunk 1: {str(e)}",
                "timestamp": timezone.now().isoformat()
            }

    def _parse_verification_result(self, raw_result: str) -> Dict[str, Any]:
        """
        Parse the verification result from Cursor Agent to extract structured data.
        
        Args:
            raw_result: Raw text response from Cursor Agent
            
        Returns:
            Dictionary with parsed verification data
        """
        try:
            # Try to extract JSON from the response
            json_start = raw_result.find('{')
            json_end = raw_result.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return {
                    "parse_status": "error",
                    "error": "No JSON structure found in verification response",
                    "extracted_data": None
                }
            
            # Extract the JSON portion
            json_text = raw_result[json_start:json_end]
            
            try:
                # Parse the JSON
                parsed_json = json.loads(json_text)
                
                # Validate and structure the parsed data
                structured_data = {
                    "parse_status": "success",
                    "verification_results": parsed_json.get("verification_results", {}),
                    "overall_confidence": parsed_json.get("overall_confidence", "Unknown"),
                    "verification_summary": parsed_json.get("verification_summary", ""),
                    "sources_consulted": parsed_json.get("sources_consulted", [])
                }
                
                # Add verification statistics
                verification_results = structured_data["verification_results"]
                total_fields = len(verification_results)
                verified_fields = sum(1 for field in verification_results.values() 
                                   if field.get("verified_value") and field.get("verified_value") != "Not provided")
                discrepancy_fields = sum(1 for field in verification_results.values() 
                                      if field.get("discrepancy_found") == True)
                
                structured_data["statistics"] = {
                    "total_fields": total_fields,
                    "verified_fields": verified_fields,
                    "discrepancy_fields": discrepancy_fields,
                    "verification_rate": f"{(verified_fields/total_fields)*100:.1f}%" if total_fields > 0 else "0%"
                }
                
                # Add confidence breakdown
                confidence_breakdown = {}
                for field_name, field_data in verification_results.items():
                    confidence = field_data.get("confidence_level", "Unknown")
                    if confidence not in confidence_breakdown:
                        confidence_breakdown[confidence] = []
                    confidence_breakdown[confidence].append(field_name)
                
                structured_data["confidence_breakdown"] = confidence_breakdown
                
                return structured_data
                
            except json.JSONDecodeError as json_error:
                # Try to fix common JSON syntax errors
                try:
                    # Fix missing commas between object properties
                    fixed_json = json_text.replace('}\n    "', '},\n    "')
                    # Fix missing commas between array elements
                    fixed_json = fixed_json.replace('"\n    }', '"\n    },')
                    # Try parsing the fixed JSON
                    parsed_json = json.loads(fixed_json)
                    
                    # If successful, proceed with the fixed data
                    structured_data = {
                        "parse_status": "success_with_fixes",
                        "verification_results": parsed_json.get("verification_results", {}),
                        "overall_confidence": parsed_json.get("overall_confidence", "Unknown"),
                        "verification_summary": parsed_json.get("verification_summary", ""),
                        "sources_consulted": parsed_json.get("sources_consulted", [])
                    }
                    
                    # Add verification statistics
                    verification_results = structured_data["verification_results"]
                    total_fields = len(verification_results)
                    verified_fields = sum(1 for field in verification_results.values() 
                                       if field.get("verified_value") and field.get("verified_value") != "Not provided")
                    discrepancy_fields = sum(1 for field in verification_results.values() 
                                          if field.get("discrepancy_found") == True)
                    
                    structured_data["statistics"] = {
                        "total_fields": total_fields,
                        "verified_fields": verified_fields,
                        "discrepancy_fields": discrepancy_fields,
                        "verification_rate": f"{(verified_fields/total_fields)*100:.1f}%" if total_fields > 0 else "0%"
                    }
                    
                    # Add confidence breakdown
                    confidence_breakdown = {}
                    for field_name, field_data in verification_results.items():
                        confidence = field_data.get("confidence_level", "Unknown")
                        if confidence not in confidence_breakdown:
                            confidence_breakdown[confidence] = []
                        confidence_breakdown[confidence].append(field_name)
                    
                    structured_data["confidence_breakdown"] = confidence_breakdown
                    structured_data["parse_notes"] = f"JSON was automatically fixed: {str(json_error)}"
                    
                    return structured_data
                    
                except (json.JSONDecodeError, Exception) as fix_error:
                    return {
                        "parse_status": "error",
                        "error": f"JSON parsing failed: {str(json_error)}. Auto-fix attempt also failed: {str(fix_error)}",
                        "extracted_data": None,
                        "raw_json_text": json_text
                    }
                
        except Exception as e:
            return {
                "parse_status": "error",
                "error": f"Failed to parse verification result: {str(e)}",
                "extracted_data": None
            }

    def _format_discovered_urls_for_prompt(self, website_discovery_data: Dict[str, Any]) -> str:
        """
        Format discovered URLs for inclusion in verification prompts.
        
        Args:
            website_discovery_data: Data from website discovery step
            
        Returns:
            Formatted string of discovered URLs for prompt inclusion
        """
        if not website_discovery_data or website_discovery_data.get('parse_status') != 'success':
            return "No websites discovered in previous step."
        
        urls_by_type = website_discovery_data.get('parsed_data', {}).get('urls_by_type', {})
        if not urls_by_type:
            return "No websites discovered in previous step."
        
        formatted_urls = []
        for url_type, urls in urls_by_type.items():
            if urls:
                formatted_urls.append(f"\n{url_type.upper().replace('_', ' ')}:")
                for url_info in urls[:3]:  # Limit to top 3 per type to avoid overwhelming prompt
                    formatted_urls.append(f"  - {url_info['url']}")
                    if url_info.get('description'):
                        formatted_urls.append(f"    Description: {url_info['description']}")
        
        if formatted_urls:
            return "\n".join(formatted_urls)
        else:
            return "No websites discovered in previous step."

    def _smart_cursor_call(self, prompt: str, timeout_seconds: int = 180) -> str:
        """
        Smart wrapper that calls Cursor Agent and parses streaming JSON responses.
        
        Args:
            prompt: The prompt to send to Cursor Agent
            timeout_seconds: Maximum time to wait for response (default: 120 seconds)
            
        Returns:
            Clean response from Cursor Agent
        """
        try:
            self.stdout.write("🤖 Starting Cursor Agent...\n")
            self.stdout.write(f"⏰ Timeout set to {timeout_seconds} seconds\n")
            self.stdout.write(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n")
            self.stdout.write("=" * 60 + "\n")
            
            process = subprocess.Popen(
                ['cursor-agent', '--force', '--print', '-f', '--model', 'auto', prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            assistant_content = []
            raw_output = []
            json_complete = False
            start_time = timezone.now()
            elapsed_time = 0
            current_response = ""
            tool_calls = []
            text_buffer = ""
            last_displayed_length = 0
            
            # Stream output and parse JSON messages
            try:
                for line in process.stdout:
                    # Check timeout
                    elapsed_time = (timezone.now() - start_time).total_seconds()
                    if elapsed_time > timeout_seconds:
                        self.stdout.write(f"\n⏰ Timeout reached ({timeout_seconds}s)! Terminating process...\n")
                        process.terminate()
                        break
                    
                    raw_output.append(line)
                    
                    # Try to parse each line as JSON
                    try:
                        if line.strip().startswith('{') and line.strip().endswith('}'):
                            message = json.loads(line.strip())
                            
                            # Handle system initialization
                            if message.get('type') == 'system' and message.get('subtype') == 'init':
                                self.stdout.write("🔧 System initialized\n")
                                continue
                            
                            # Handle user message
                            elif message.get('type') == 'user':
                                self.stdout.write("👤 User prompt received\n")
                                continue
                            
                            # Handle assistant content (streaming text)
                            elif message.get('type') == 'assistant' and 'message' in message:
                                content = message['message'].get('content', [])
                                for item in content:
                                    if isinstance(item, dict) and 'text' in item:
                                        text = item['text']
                                        assistant_content.append(text)
                                        current_response += text
                                        text_buffer += text
                                        
                                        # Display text in chunks to avoid broken words
                                        # Look for natural break points (spaces, punctuation, newlines)
                                        if len(text_buffer) - last_displayed_length > 20:  # Display every 20 chars
                                            # Find the last space or punctuation to avoid breaking words
                                            display_end = len(text_buffer)
                                            for i in range(len(text_buffer) - 1, last_displayed_length, -1):
                                                if text_buffer[i] in ' \n.,!?;:':
                                                    display_end = i + 1
                                                    break
                                            
                                            if display_end > last_displayed_length:
                                                new_text = text_buffer[last_displayed_length:display_end]
                                                self.stdout.write(new_text)
                                                self.stdout.flush()
                                                last_displayed_length = display_end
                            
                            # Handle tool calls
                            elif message.get('type') == 'tool_call':
                                if message.get('subtype') == 'started':
                                    tool_call = message.get('tool_call', {})
                                    mcp_call = tool_call.get('mcpToolCall', {})
                                    tool_name = mcp_call.get('args', {}).get('toolName', 'unknown')
                                    tool_args = mcp_call.get('args', {}).get('args', {})
                                    
                                    self.stdout.write(f"\n🔧 Using tool: {tool_name}\n")
                                    if tool_args:
                                        for key, value in tool_args.items():
                                            if isinstance(value, str) and len(value) > 100:
                                                value = value[:100] + "..."
                                            elif not isinstance(value, str):
                                                value = str(value)
                                            self.stdout.write(f"   📋 {key}: {value}\n")
                                    tool_calls.append(tool_name)
                                
                                elif message.get('subtype') == 'completed':
                                    tool_call = message.get('tool_call', {})
                                    mcp_call = tool_call.get('mcpToolCall', {})
                                    result = mcp_call.get('result', {})
                                    
                                    if result.get('success'):
                                        success_data = result['success']
                                        content = success_data.get('content', [])
                                        
                                        # Format tool results nicely
                                        if tool_name == 'search':
                                            self.stdout.write("✅ Search completed - Results:\n")
                                            self.stdout.write("=" * 50 + "\n")
                                            for item in content:
                                                if isinstance(item, dict) and 'text' in item:
                                                    try:
                                                        # Try to parse as JSON to format search results
                                                        search_data = json.loads(item['text'])
                                                        if isinstance(search_data, dict) and 'results' in search_data:
                                                            # Handle search results format with 'results' key
                                                            results = search_data.get('results', [])
                                                            for i, result_item in enumerate(results[:3], 1):  # Show top 3
                                                                title = result_item.get('title', 'No title')
                                                                url = result_item.get('url', 'No URL')
                                                                desc = result_item.get('snippet', result_item.get('description', 'No description'))
                                                                if isinstance(desc, str) and len(desc) > 200:
                                                                    desc = desc[:200] + "..."
                                                                elif not isinstance(desc, str):
                                                                    desc = str(desc)
                                                                self.stdout.write(f"{i}. {title}\n")
                                                                self.stdout.write(f"   URL: {url}\n")
                                                                self.stdout.write(f"   Description: {desc}\n\n")
                                                        elif isinstance(search_data, list):
                                                            # Handle direct list format
                                                            for i, result_item in enumerate(search_data[:3], 1):  # Show top 3
                                                                title = result_item.get('title', 'No title')
                                                                url = result_item.get('url', 'No URL')
                                                                desc = result_item.get('description', 'No description')
                                                                if isinstance(desc, str) and len(desc) > 200:
                                                                    desc = desc[:200] + "..."
                                                                elif not isinstance(desc, str):
                                                                    desc = str(desc)
                                                                self.stdout.write(f"{i}. {title}\n")
                                                                self.stdout.write(f"   URL: {url}\n")
                                                                self.stdout.write(f"   Description: {desc}\n\n")
                                                        else:
                                                            # Show the parsed data in a readable format
                                                            self.stdout.write(f"   {str(search_data)[:200]}...\n")
                                                    except json.JSONDecodeError:
                                                        # If not JSON, just show the text
                                                        text_content = item['text']
                                                        if isinstance(text_content, str) and len(text_content) > 200:
                                                            text_content = text_content[:200] + "..."
                                                        elif not isinstance(text_content, str):
                                                            text_content = str(text_content)
                                                        self.stdout.write(f"   {text_content}\n")
                                        
                                        elif tool_name == 'pull_markdown':
                                            self.stdout.write("✅ Markdown content extracted:\n")
                                            self.stdout.write("=" * 50 + "\n")
                                            for item in content:
                                                if isinstance(item, dict) and 'text' in item:
                                                    text_content = item['text']
                                                    if isinstance(text_content, str):
                                                        try:
                                                            # Try to parse as JSON to extract markdown content
                                                            markdown_data = json.loads(text_content)
                                                            if isinstance(markdown_data, dict) and 'markdown_content' in markdown_data:
                                                                # Extract the actual markdown content
                                                                markdown_text = markdown_data['markdown_content']
                                                                # Show first few lines of markdown
                                                                lines = markdown_text.split('\n')[:10]
                                                                for line in lines:
                                                                    self.stdout.write(f"   {line}\n")
                                                                if len(markdown_text.split('\n')) > 10:
                                                                    self.stdout.write("   ... (truncated)\n")
                                                            else:
                                                                # Show first few lines of the text
                                                                lines = text_content.split('\n')[:10]
                                                                for line in lines:
                                                                    self.stdout.write(f"   {line}\n")
                                                                if len(text_content.split('\n')) > 10:
                                                                    self.stdout.write("   ... (truncated)\n")
                                                        except json.JSONDecodeError:
                                                            # If not JSON, show first few lines of the text
                                                            lines = text_content.split('\n')[:10]
                                                            for line in lines:
                                                                self.stdout.write(f"   {line}\n")
                                                            if len(text_content.split('\n')) > 10:
                                                                self.stdout.write("   ... (truncated)\n")
                                                    else:
                                                        self.stdout.write(f"   {str(text_content)[:200]}...\n")
                                        
                                        elif tool_name == 'render_html':
                                            self.stdout.write("✅ HTML rendered in browser\n")
                                        
                                        else:
                                            # Generic tool result
                                            self.stdout.write("✅ Tool call completed\n")
                                            for item in content:
                                                if isinstance(item, dict) and 'text' in item:
                                                    text_content = item['text']
                                                    if isinstance(text_content, str) and len(text_content) > 200:
                                                        text_content = text_content[:200] + "..."
                                                    elif not isinstance(text_content, str):
                                                        text_content = str(text_content)
                                                    self.stdout.write(f"   {text_content}\n")
                                    
                                    else:
                                        self.stdout.write("❌ Tool call failed\n")
                                        error = result.get('error', 'Unknown error')
                                        self.stdout.write(f"   Error: {error}\n")
                            
                            # Check for completion
                            elif message.get('type') == 'result' and message.get('subtype') == 'success':
                                json_complete = True
                                # Flush any remaining text before showing completion
                                if last_displayed_length < len(text_buffer):
                                    remaining_text = text_buffer[last_displayed_length:]
                                    self.stdout.write(remaining_text)
                                    self.stdout.flush()
                                self.stdout.write(f"\n\n🎉 Task completed successfully!\n")
                                process.terminate()
                                break
                    
                    except json.JSONDecodeError:
                        # Not a JSON line, check if it looks like JSON and filter it out
                        if line.strip().startswith('{') and not line.strip().endswith('}'):
                            # This might be a partial JSON line, skip it
                            continue
                        # Otherwise, it's not JSON, continue processing
                        pass
                    
                    # Check for the <|END|> marker to detect completion (fallback)
                    if '<|END|>' in line:
                        json_complete = True
                        self.stdout.write(f"\n\n🎉 <|END|> marker found!\n")
                        process.terminate()
                        break
                    
                    if json_complete:
                        break
                        
            except Exception as stream_error:
                self.stdout.write(f"\n⚠️  Error during streaming: {str(stream_error)}\n")
            
            self.stdout.write("\n" + "=" * 60 + "\n")
            
            # Wait for process to finish with timeout
            try:
                process.wait(timeout=30)  # Give it 30 seconds to clean up
            except subprocess.TimeoutExpired:
                self.stdout.write("⚠️  Process didn't terminate gracefully, forcing kill...\n")
                process.kill()
                process.wait()
            
            # Flush any remaining text in the buffer
            if last_displayed_length < len(text_buffer):
                remaining_text = text_buffer[last_displayed_length:]
                self.stdout.write(remaining_text)
                self.stdout.flush()
            
            # Report final status
            if json_complete:
                self.stdout.write("\n\n✅ Process terminated successfully after completion\n")
                if tool_calls:
                    self.stdout.write(f"🔧 Tools used: {', '.join(set(tool_calls))}\n")
            elif elapsed_time > timeout_seconds:
                self.stdout.write(f"\n⏰ Process terminated due to timeout ({timeout_seconds}s)\n")
            else:
                self.stdout.write("\n⚠️  Process finished without clear completion signal\n")
            
            # Return the assistant content if we have it, otherwise return raw output
            if assistant_content:
                return ''.join(assistant_content).strip()
            else:
                return ''.join(raw_output).strip()
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.stdout.write(f"❌ {error_msg}\n")
            return error_msg

    def _find_resources_needing_verification(self, limit: int = 1) -> List[Resource]:
        """
        Find resources that need verification based on priority criteria.
        
        Priority order:
        1. Resources with no verification date AND no service areas defined (highest priority)
        2. Resources with no verification date (high priority)
        3. Resources with expired verification dates (medium priority)
        
        Args:
            limit: Maximum number of resources to return
            
        Returns:
            List of resources ordered by priority and ID
        """
        # Priority 1: No verification date + no service areas (highest priority)
        priority_1 = Resource.objects.filter(
            Q(last_verified_at__isnull=True) & 
            Q(coverage_areas__isnull=True)
        ).order_by('id')
        
        if priority_1.exists():
            return list(priority_1[:limit])
        
        # Priority 2: No verification date (high priority)
        priority_2 = Resource.objects.filter(
            last_verified_at__isnull=True
        ).order_by('id')
        
        if priority_2.exists():
            return list(priority_2[:limit])
        
        # Priority 3: Expired verification dates (medium priority)
        # Default verification frequency is 180 days
        cutoff_date = timezone.now() - datetime.timedelta(days=180)
        priority_3 = Resource.objects.filter(
            Q(last_verified_at__lt=cutoff_date) &
            Q(status='published')  # Only check published resources for re-verification
        ).order_by('id')
        
        if priority_3.exists():
            return list(priority_3[:limit])
        
        # No resources need verification
        return []

    def _format_resource_for_verification(self, resource: Resource, verbose: bool = False) -> Dict[str, Any]:
        """
        Format a resource for verification output.
        
        Args:
            resource: Resource instance to format
            verbose: Whether to include verbose information
            
        Returns:
            Dictionary with formatted resource data
        """
        # Basic resource information
        resource_data = {
            "id": resource.id,
            "name": resource.name,
            "status": resource.status,
            "category": resource.category.name if resource.category else None,
            "description": resource.description,
            "city": resource.city,
            "state": resource.state,
            "county": resource.county,
            "verification_status": {
                "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                "last_verified_by": resource.last_verified_by.username if resource.last_verified_by else None,
                "verification_frequency_days": resource.verification_frequency_days,
                "days_since_verification": self._calculate_days_since_verification(resource),
                "verification_priority": self._determine_verification_priority(resource)
            },
            "service_areas": {
                "assigned": list(resource.coverage_areas.values_list('name', flat=True)),
                "count": resource.coverage_areas.count()
            },
            "service_types": {
                "assigned": list(resource.service_types.values_list('name', flat=True)),
                "count": resource.service_types.count()
            }
        }
        
        # Add verbose information if requested
        if verbose:
            resource_data.update({
                "contact_information": {
                    "phone": resource.phone,
                    "email": resource.email,
                    "website": resource.website,
                    "address1": resource.address1,
                    "address2": resource.address2,
                    "postal_code": resource.postal_code
                },
                "operational_details": {
                    "hours_of_operation": resource.hours_of_operation,
                    "is_emergency_service": resource.is_emergency_service,
                    "is_24_hour_service": resource.is_24_hour_service,
                    "capacity": resource.capacity
                },
                "service_details": {
                    "eligibility_requirements": resource.eligibility_requirements,
                    "populations_served": resource.populations_served,
                    "insurance_accepted": resource.insurance_accepted,
                    "cost_information": resource.cost_information,
                    "languages_available": resource.languages_available
                },
                "metadata": {
                    "source": resource.source,
                    "notes": resource.notes,
                    "created_at": resource.created_at.isoformat() if resource.created_at else None,
                    "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
                }
            })
        
        return resource_data

    def _calculate_days_since_verification(self, resource: Resource) -> Optional[int]:
        """
        Calculate days since last verification.
        
        Args:
            resource: Resource instance
            
        Returns:
            Number of days since verification, or None if never verified
        """
        if not resource.last_verified_at:
            return None
        
        delta = timezone.now() - resource.last_verified_at
        return delta.days

    def _determine_verification_priority(self, resource: Resource) -> str:
        """
        Determine the verification priority for a resource.
        
        Args:
            resource: Resource instance
            
        Returns:
            Priority level string
        """
        if resource.last_verified_at is None and resource.coverage_areas.count() == 0:
            return "HIGHEST - No verification date + no service areas"
        elif resource.last_verified_at is None:
            return "HIGH - No verification date"
        else:
            days_since = self._calculate_days_since_verification(resource)
            if days_since and days_since > resource.verification_frequency_days:
                return f"MEDIUM - Verification expired ({days_since} days ago)"
            else:
                return "LOW - Recently verified"

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
