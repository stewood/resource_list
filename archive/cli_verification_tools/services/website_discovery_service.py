"""
Website Discovery Service for resource verification.

This service handles the discovery of websites for resources using AI-powered
search and verification techniques.
"""

import json
from typing import Any, Dict, Optional

from django.utils import timezone

from directory.models.verification_models import WebsiteDiscoveryResult, ResourceData
from directory.utils.verification_utils import format_discovered_urls_for_prompt
from directory.utils.json_utils import parse_website_discovery_result
from directory.config.verification_config import VerificationConfig, default_verification_config

# Import the cursor parser - this might need to be adjusted based on your project structure
try:
    import sys
    import os
    # Add the project root to the path for importing test modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from test_cursor_parser import parse_cursor_agent_output
    from rich import print as rprint
    from rich.json import JSON
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class WebsiteDiscoveryService:
    """
    Service for discovering websites for resources.

    This service encapsulates the website discovery logic, including AI-powered
    search, result parsing, and output formatting.
    """

    def __init__(self, config: Optional[VerificationConfig] = None):
        """
        Initialize the website discovery service.

        Args:
            config: Configuration for the service
        """
        self.config = config or default_verification_config
        self.console = Console() if RICH_AVAILABLE else None

    def discover_websites(self, resource_data: ResourceData, timeout_seconds: Optional[int] = None) -> WebsiteDiscoveryResult:
        """
        Discover websites for a resource using AI-powered search.

        Args:
            resource_data: Formatted resource data
            timeout_seconds: Timeout for the discovery process

        Returns:
            WebsiteDiscoveryResult with discovery results
        """
        timeout = timeout_seconds or self.config.default_timeout_seconds

        try:
            # Create website discovery prompt
            website_prompt = self._create_website_prompt(resource_data)

            if RICH_AVAILABLE and self.console:
                return self._discover_with_rich_formatting(resource_data, website_prompt, timeout)
            else:
                return self._discover_with_fallback(resource_data, website_prompt, timeout)

        except Exception as e:
            return WebsiteDiscoveryResult(
                status="error",
                message=f"Failed to discover websites: {str(e)}",
                timestamp=timezone.now().isoformat()
            )

    def _create_website_prompt(self, resource_data: ResourceData) -> str:
        """
        Create a prompt for website discovery.

        Args:
            resource_data: Resource data to use in the prompt

        Returns:
            Formatted prompt for AI agent
        """
        return f"""
You are a web research agent with tools: web_search, pull_markdown, render_html.

Goal: Find and verify URLs about the specific organization below, then output ONLY JSON (no code fences, no extra text) followed by <|END|>.

Organization: {resource_data.name}
Location: {resource_data.city}, {resource_data.state}
Category: {resource_data.category}

## What to collect (prioritized)
1) Official website
2) Social media profiles (org-owned)
3) Directory listings (legit business/NGO directories)
4) News articles (credible outlets)
5) Other highly relevant URLs

## Iterative search & branching
- Start with queries combining name, city/state, and category.
- After each search, ADAPT: refine or expand keywords from what you found (aliases, former names, DBA, acronyms, street address, phone, unique phrases).
- Continue iterating until you either:
  (a) find a clear official site and 2–5 corroborating sources, or
  (b) hit 12 total unique, high-confidence URLs, or
  (c) exhaust obviously useful variations.

## Disambiguation & verification
- NEVER assume a page is about the target just because names match.
- Verify with at least TWO of the following on-page signals (via pull_markdown or render_html):
  - Matching name + city/state or service area
  - Matching phone, email domain, or street address across ≥2 sources
  - About/Contact pages explicitly naming the org
  - Consistent branding/handles across official site and socials
- If ambiguity remains, mark the item "uncertain" and explain briefly in "reason".

## Link following (controlled crawl)
- From any already-verified page, you MAY follow up to 2 internal/external links if link text or URL strongly suggests:
  - Contact/About/Locations/Press/Programs/Partners pages
  - Official social icons/links
  - Authoritative directory or news references
- Depth limit: 2 clicks from your current page. Avoid infinite loops, ads, login walls, and generic portals.
- Only include URLs you actually visited via tools. Do NOT invent or guess.

## Rate limiting & fallbacks (use ONLY if HTTP 429 or tool error)
1) Vary search terms (name-only; name + city; name + category; address/phone; acronym/DBA)
2) Use pull_markdown on pages you already have to mine new keywords, aliases, or contacts
3) Use render_html for JS-heavy sites
4) Proceed with what you could verify so far, clearly noting the limitation

## Data quality rules
- Dedupe by canonical URL (strip fragments, utm params; prefer https; prefer root for homepages).
- Prefer primary sources over scraped mirrors.
- Cap description and reason to ≤20 words each.
- Types must be one of: official_website | social_media | directory | news | other
- Only include organization-owned socials (mark third-party fan pages as "other" if clearly useful).

## Output format (return ONLY this JSON then print <|END|>)
{{
  "search_strategy": "1–3 sentences on your query progression, keyword pivots, and whether fallbacks were needed",
  "entity_resolution": {{
    "normalized_name": "final canonical name used",
    "aliases": ["any discovered aliases or DBA"],
    "key_signals": ["brief list of strongest verification signals (e.g., address match, phone match, cross-links)"]
  }},
  "urls_found": [
    {{
      "url": "https://example.com",
      "type": "official_website|social_media|directory|news|other",
      "description": "What the URL contains (≤20 words).",
      "reason": "Why it's relevant/verified (≤20 words).",
      "confidence": "high|medium|uncertain",
      "signals": ["address match","cross-linked from official","phone matches directory"],
      "discovered_via": "web_search|followed_link|on_page_link"
    }}
  ],
  "total_urls": 0,
  "search_notes": "Any errors or 429s, pages skipped, JS rendering needed, or unresolved ambiguities"
}}

STRICT OUTPUT RULES:
- Output ONLY the JSON object above, then print <|END|> on a new line.
- Do NOT include code fences, explanations, or any text outside the JSON.
- Include ONLY URLs you actually opened or saw via tools. No fabricated URLs.
"""

    def _discover_with_rich_formatting(self, resource_data: ResourceData, prompt: str, timeout: int) -> WebsiteDiscoveryResult:
        """
        Discover websites with Rich formatting support.

        Args:
            resource_data: Resource data
            prompt: Discovery prompt
            timeout: Timeout in seconds

        Returns:
            WebsiteDiscoveryResult
        """
        # Header with Rich styling
        header_panel = Panel(
            f"🔍 Website Discovery for: {resource_data.name}\n"
            f"📍 Location: {resource_data.city}, {resource_data.state}\n"
            f"⏰ Timeout: {timeout}s",
            title="🌐 Starting website discovery...",
            border_style="blue"
        )
        self.console.print(header_panel)

        # Use the cursor parser
        result = parse_cursor_agent_output(
            prompt=prompt,
            timeout_seconds=timeout,
            verbose=True,
            show_tool_calls=True,
            show_system_messages=False
        )

        # Display results summary
        if result['success']:
            # Create a summary table
            summary_table = Table(title="Website Discovery Summary", show_header=True, header_style="bold magenta")
            summary_table.add_column("Metric", style="cyan", no_wrap=True)
            summary_table.add_column("Value", style="green")

            summary_table.add_row("Success", "✅ Yes")
            summary_table.add_row("Duration", f"{result['duration_ms']}ms")
            summary_table.add_row("Tool calls", str(len(result['tool_calls'])))

            self.console.print(summary_table)

            # Try to extract and display the final JSON response
            try:
                # Look for JSON in the full text
                json_start = result['full_text'].find('{')
                json_end = result['full_text'].rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_text = result['full_text'][json_start:json_end]
                    json_data = json.loads(json_text)

                    final_panel = Panel(
                        JSON.from_data(json_data),
                        title="🎯 Website Discovery Results",
                        border_style="bold green"
                    )
                    self.console.print(final_panel)

                    # Parse the result to extract structured data
                    parsed_result = parse_website_discovery_result(result['full_text'])

                    return WebsiteDiscoveryResult(
                        status="success",
                        message="Website discovery completed successfully",
                        urls_found=len(parsed_result.get('urls', [])) if parsed_result else 0,
                        discovered_urls=parsed_result.get('urls', []) if parsed_result else [],
                        tool_calls_count=len(result.get('tool_calls', [])),
                        duration_ms=result['duration_ms'],
                        timestamp=timezone.now().isoformat(),
                        search_strategy=parsed_result.get('search_strategy', '') if parsed_result else '',
                        total_urls=parsed_result.get('total_urls', 0) if parsed_result else 0,
                        search_notes=parsed_result.get('search_notes', '') if parsed_result else ''
                    )
                else:
                    return WebsiteDiscoveryResult(
                        status="success",
                        message="Website discovery completed (no JSON found in response)",
                        urls_found=0,
                        tool_calls_count=len(result.get('tool_calls', [])),
                        duration_ms=result['duration_ms'],
                        timestamp=timezone.now().isoformat()
                    )

            except json.JSONDecodeError:
                return WebsiteDiscoveryResult(
                    status="error",
                    message="Website discovery failed - JSON parse error",
                    urls_found=0,
                    tool_calls_count=len(result.get('tool_calls', [])),
                    duration_ms=result['duration_ms'],
                    timestamp=timezone.now().isoformat()
                )
        else:
            # Error occurred
            error_panel = Panel(
                f"Error: {result.get('error', 'Unknown error')}",
                title="❌ Website Discovery Failed",
                border_style="red"
            )
            self.console.print(error_panel)

            return WebsiteDiscoveryResult(
                status="error",
                message=result.get('error', 'Unknown error'),
                timestamp=timezone.now().isoformat()
            )

    def _discover_with_fallback(self, resource_data: ResourceData, prompt: str, timeout: int) -> WebsiteDiscoveryResult:
        """
        Discover websites using fallback method without Rich formatting.

        Args:
            resource_data: Resource data
            prompt: Discovery prompt
            timeout: Timeout in seconds

        Returns:
            WebsiteDiscoveryResult
        """
        # This would need to be implemented based on your existing _smart_cursor_call method
        # For now, return a placeholder
        return WebsiteDiscoveryResult(
            status="error",
            message="Fallback method not yet implemented in service",
            timestamp=timezone.now().isoformat()
        )

