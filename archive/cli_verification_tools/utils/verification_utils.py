"""
Utility functions for resource verification.

This module contains utility functions used throughout the verification process,
including date calculations, priority determination, and data formatting.
"""

from typing import Any, Dict, Optional
from django.utils import timezone

from directory.models import Resource


def calculate_days_since_verification(resource: Resource) -> Optional[int]:
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


def determine_verification_priority(resource: Resource) -> str:
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
        days_since = calculate_days_since_verification(resource)
        if days_since and days_since > resource.verification_frequency_days:
            return f"MEDIUM - Verification expired ({days_since} days ago)"
        else:
            return "LOW - Recently verified"


def format_discovered_urls_for_prompt(website_discovery_data: Dict[str, Any]) -> str:
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

