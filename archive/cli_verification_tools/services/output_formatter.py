"""
Output Formatter Service for consistent output formatting.

This service handles formatting and displaying results from the verification
process, including Rich formatting and JSON output.
"""

import json
from typing import Any, Dict, Optional

from django.utils import timezone

from directory.models.verification_models import WebsiteDiscoveryResult
from directory.config.verification_config import DisplayConfig, default_display_config

# Import Rich components
try:
    from rich import print as rprint
    from rich.json import JSON
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class OutputFormatter:
    """
    Service for formatting and displaying verification results.

    This service provides consistent formatting for all output from the
    verification process, including Rich formatting and JSON output.
    """

    def __init__(self, config: Optional[DisplayConfig] = None):
        """
        Initialize the output formatter.

        Args:
            config: Display configuration
        """
        self.config = config or default_display_config
        self.console = Console() if RICH_AVAILABLE else None

    def format_success_response(self, message: str, data: Dict[str, Any]) -> str:
        """
        Format a successful response.

        Args:
            message: Success message
            data: Response data

        Returns:
            Formatted JSON string
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": timezone.now().isoformat(),
            "data": data
        }
        return json.dumps(response, indent=2, default=str)

    def format_error_response(self, message: str, error_details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format an error response.

        Args:
            message: Error message
            error_details: Additional error details

        Returns:
            Formatted JSON string
        """
        response = {
            "success": False,
            "error": message,
            "timestamp": timezone.now().isoformat()
        }

        if error_details:
            response["details"] = error_details

        return json.dumps(response, indent=2, default=str)

    def display_website_discovery_summary(self, result: WebsiteDiscoveryResult) -> None:
        """
        Display a summary of website discovery results.

        Args:
            result: Website discovery result to display
        """
        if not RICH_AVAILABLE or not self.console:
            self._display_plain_summary(result)
            return

        # Create a summary table
        summary_table = Table(title="Website Discovery Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Status", f"✅ {result.status.title()}" if result.status == "success" else f"❌ {result.status.title()}")
        summary_table.add_row("URLs Found", str(result.urls_found))
        summary_table.add_row("Tool Calls", str(result.tool_calls_count))
        summary_table.add_row("Duration", f"{result.duration_ms}ms" if result.duration_ms > 0 else "N/A")

        if result.search_strategy:
            summary_table.add_row("Strategy", result.search_strategy[:50] + "..." if len(result.search_strategy) > 50 else result.search_strategy)

        self.console.print(summary_table)

        # Display discovered URLs
        if result.discovered_urls:
            self._display_discovered_urls(result.discovered_urls)

    def _display_plain_summary(self, result: WebsiteDiscoveryResult) -> None:
        """
        Display summary in plain text format.

        Args:
            result: Website discovery result
        """
        print("Website Discovery Summary")
        print("=" * 50)
        print(f"Status: {result.status}")
        print(f"URLs Found: {result.urls_found}")
        print(f"Tool Calls: {result.tool_calls_count}")
        print(f"Duration: {result.duration_ms}ms")
        print(f"Message: {result.message}")

        if result.discovered_urls:
            print("\nDiscovered URLs:")
            for i, url_info in enumerate(result.discovered_urls, 1):
                print(f"{i}. {url_info.get('url', 'N/A')}")

    def _display_discovered_urls(self, urls: list) -> None:
        """
        Display discovered URLs in a formatted table.

        Args:
            urls: List of discovered URL information
        """
        if not urls:
            return

        url_table = Table(title="Discovered URLs", show_header=True, header_style="bold blue")
        url_table.add_column("URL", style="cyan", max_width=60)
        url_table.add_column("Type", style="green")
        url_table.add_column("Confidence", style="yellow")
        url_table.add_column("Description", style="white", max_width=40)

        for url_info in urls[:10]:  # Limit to first 10 for display
            url_table.add_row(
                url_info.get('url', 'N/A'),
                url_info.get('type', 'N/A'),
                url_info.get('confidence', 'N/A'),
                url_info.get('description', 'N/A')[:37] + "..." if len(url_info.get('description', '')) > 40 else url_info.get('description', 'N/A')
            )

        self.console.print(url_table)

        if len(urls) > 10:
            self.console.print(f"\n... and {len(urls) - 10} more URLs")

    def format_json_data(self, data: Any, title: Optional[str] = None) -> None:
        """
        Format and display JSON data.

        Args:
            data: Data to format as JSON
            title: Optional title for the display
        """
        if RICH_AVAILABLE and self.console:
            panel = Panel(
                JSON.from_data(data),
                title=title or "JSON Data",
                border_style="blue"
            )
            self.console.print(panel)
        else:
            formatted_json = json.dumps(data, indent=2, default=str)
            if title:
                print(f"{title}:")
                print("-" * len(title))
            print(formatted_json)

    def display_progress(self, message: str, step: int, total_steps: int) -> None:
        """
        Display progress information.

        Args:
            message: Progress message
            step: Current step number
            total_steps: Total number of steps
        """
        if RICH_AVAILABLE and self.console:
            progress_panel = Panel(
                f"Step {step}/{total_steps}: {message}",
                title="Progress",
                border_style="yellow"
            )
            self.console.print(progress_panel)
        else:
            print(f"[{step}/{total_steps}] {message}")

    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Display an error message.

        Args:
            message: Error message
            details: Optional error details
        """
        if RICH_AVAILABLE and self.console:
            error_panel = Panel(
                f"{message}" + (f"\n\n{details}" if details else ""),
                title="❌ Error",
                border_style="red"
            )
            self.console.print(error_panel)
        else:
            print(f"ERROR: {message}")
            if details:
                print(f"Details: {details}")

    def display_success(self, message: str, details: Optional[str] = None) -> None:
        """
        Display a success message.

        Args:
            message: Success message
            details: Optional success details
        """
        if RICH_AVAILABLE and self.console:
            success_panel = Panel(
                f"{message}" + (f"\n\n{details}" if details else ""),
                title="✅ Success",
                border_style="green"
            )
            self.console.print(success_panel)
        else:
            print(f"SUCCESS: {message}")
            if details:
                print(f"Details: {details}")

