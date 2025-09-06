"""
Configuration settings for the resource verification system.

This module contains configuration dataclasses and default values
used throughout the verification process.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VerificationConfig:
    """
    Configuration for the resource verification system.

    Attributes:
        default_timeout_seconds: Default timeout for AI operations
        max_resources_per_batch: Maximum resources to process in one batch
        verification_frequency_days: Default verification frequency
        max_urls_per_discovery: Maximum URLs to discover per resource
        output_format: Default output format ('json', 'rich', 'text')
        verbose_logging: Whether to enable verbose logging
        enable_progress_bars: Whether to show progress bars
        cache_enabled: Whether to enable caching
        cache_ttl_seconds: Cache time-to-live in seconds
    """
    default_timeout_seconds: int = 300
    max_resources_per_batch: int = 10
    verification_frequency_days: int = 180
    max_urls_per_discovery: int = 15
    output_format: str = "json"
    verbose_logging: bool = False
    enable_progress_bars: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "default_timeout_seconds": self.default_timeout_seconds,
            "max_resources_per_batch": self.max_resources_per_batch,
            "verification_frequency_days": self.verification_frequency_days,
            "max_urls_per_discovery": self.max_urls_per_discovery,
            "output_format": self.output_format,
            "verbose_logging": self.verbose_logging,
            "enable_progress_bars": self.enable_progress_bars,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }


@dataclass
class DisplayConfig:
    """
    Configuration for display and output formatting.

    Attributes:
        show_tool_calls: Whether to show tool calls in output
        show_system_messages: Whether to show system messages
        max_description_length: Maximum length for descriptions
        table_style: Rich table style
        panel_border_style: Rich panel border style
        success_color: Color for success messages
        error_color: Color for error messages
    """
    show_tool_calls: bool = True
    show_system_messages: bool = False
    max_description_length: int = 100
    table_style: str = "blue"
    panel_border_style: str = "blue"
    success_color: str = "green"
    error_color: str = "red"


@dataclass
class ProcessConfig:
    """
    Configuration for processing and execution.

    Attributes:
        subprocess_timeout: Timeout for subprocess operations
        max_retries: Maximum number of retries for failed operations
        retry_delay_seconds: Delay between retries
        cleanup_temp_files: Whether to cleanup temporary files
        log_level: Logging level
        enable_profiling: Whether to enable performance profiling
    """
    subprocess_timeout: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5
    cleanup_temp_files: bool = True
    log_level: str = "INFO"
    enable_profiling: bool = False


# Default configurations
default_verification_config = VerificationConfig()
default_display_config = DisplayConfig()
default_process_config = ProcessConfig()

# Configuration presets
fast_config = VerificationConfig(
    default_timeout_seconds=60,
    max_resources_per_batch=5,
    enable_progress_bars=False
)

thorough_config = VerificationConfig(
    default_timeout_seconds=300,
    max_urls_per_discovery=25,
    verbose_logging=True,
    cache_enabled=False
)
