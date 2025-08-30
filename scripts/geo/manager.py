"""
Geographic Data Manager - Main Manager

This module provides the main GeographicDataManager class that integrates
all the extracted operations and utilities.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')

import django
django.setup()

from django.core.management import call_command
from directory.models import CoverageArea
from directory.utils.tiger_cache import TigerFileCache

# Rich imports for beautiful UI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm
from rich.align import Align
from rich import box

# Import our extracted modules
from .operations.populate import PopulateOperations
from .operations.clear import ClearOperations
from .operations.update import UpdateOperations
from .operations.status import StatusOperations
from .utils.cache import CacheUtilities
from .utils.validation import ValidationUtilities


class GeographicDataManager:
    """Beautiful CLI manager for geographic data operations."""
    
    def __init__(self):
        """Initialize the manager with Rich console."""
        self.console = Console()
        self.logger = self._setup_logging()
        self.cache = TigerFileCache()
        
        # State FIPS codes mapping for user-friendly input
        self.state_mapping = {
            'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
            'CO': '08', 'CT': '09', 'DE': '10', 'DC': '11', 'FL': '12',
            'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
            'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23',
            'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
            'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33',
            'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38',
            'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44',
            'SC': '45', 'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49',
            'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
            'WY': '56'
        }
        
        # All state FIPS codes for bulk operations
        self.all_state_fips = list(self.state_mapping.values())
        
        # Initialize operation modules
        self.populate_ops = PopulateOperations(
            self.console, self.logger, self.state_mapping, self.all_state_fips
        )
        self.clear_ops = ClearOperations(self.console, self.logger)
        self.update_ops = UpdateOperations(
            self.console, self.logger, self.state_mapping, self.all_state_fips
        )
        self.status_ops = StatusOperations(
            self.console, self.logger, self.state_mapping, self.cache
        )
        self.cache_utils = CacheUtilities(self.console, self.logger, self.cache)
        self.validation_utils = ValidationUtilities(
            self.console, self.logger, self.state_mapping
        )
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the manager."""
        logger = logging.getLogger('geographic_data_manager')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        file_handler = logging.FileHandler('geographic_data_manager.log')
        file_handler.setLevel(logging.INFO)
        
        # Create formatters and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        
        return logger
    
    def show_help(self):
        """Display help information."""
        help_text = Text()
        help_text.append("Geographic Data Manager\n\n", style="bold blue")
        help_text.append("A simple CLI for managing geographic data from US Census Bureau TIGER/Line files.\n\n", style="white")
        
        help_text.append("Commands:\n\n", style="bold")
        help_text.append("status                    Show current geographic data status\n", style="white")
        help_text.append("populate          Import all states + counties/cities for specified states\n", style="white")
        help_text.append("clear                     Clear all geographic data\n", style="white")
        help_text.append("kentucky-region           Import all states + KY region counties/cities\n", style="white")
        help_text.append("cache-status              Show cache status and information\n", style="white")
        help_text.append("cache-clear               Clear all cached files\n", style="white")
        help_text.append("cache-cleanup             Remove expired cache files\n", style="white")
        help_text.append("help                      Show this help message\n\n", style="white")
        
        help_text.append("State Formats:\n", style="bold")
        help_text.append("• Use state abbreviations: KY, IN, CA, NY\n", style="white")
        help_text.append("• Use FIPS codes: 21, 18, 06, 36\n", style="white")
        help_text.append("• Use 'all' for all states\n", style="white")
        help_text.append("• Leave empty for states only\n\n", style="white")
        
        help_text.append("Examples:\n", style="bold")
        help_text.append("• python scripts/geo_manager.py status\n", style="white")
        help_text.append("• python scripts/geo_manager.py populate KY,IN,IL,MO,TN,VA,WV,OH\n", style="white")
        help_text.append("• python scripts/geo_manager.py populate all\n", style="white")
        help_text.append("• python scripts/geo_manager.py populate\n", style="white")
        help_text.append("• python scripts/geo_manager.py clear\n", style="white")
        help_text.append("• python scripts/geo_manager.py kentucky-region\n", style="white")
        help_text.append("• python scripts/geo_manager.py cache-status\n", style="white")
        help_text.append("• python scripts/geo_manager.py cache-clear\n\n", style="white")
        
        help_text.append("Notes:\n", style="bold")
        help_text.append("• States are ALWAYS imported (all 57 states/territories)\n", style="white")
        help_text.append("• Counties and cities are imported for specified states only\n", style="white")
        help_text.append("• Year is auto-detected (latest available)\n", style="white")
        help_text.append("• Files are cached to avoid re-downloading (30-day expiration)\n", style="white")
        help_text.append("• Use 'populate' for new installations\n", style="white")
        help_text.append("• Commands are non-interactive by default\n", style="white")
        help_text.append("• Use --clear-existing to clear data before import\n", style="white")
        
        self.console.print(Panel(help_text, title="Help", box=box.ROUNDED))
    
    def show_status(self):
        """Display current status."""
        self.status_ops.show_status()
    
    def clear_data(self, confirm: bool = False):
        """Clear all geographic data."""
        self.clear_ops.clear_data(confirm)
    
    def populate_data_simple(self, states_input: str, clear_existing: bool = False):
        """Simplified populate: Always import all states, optionally import counties/cities for specific states."""
        self.populate_ops.populate_data_simple(states_input, clear_existing)
    
    def populate_states_only(self, clear_existing: bool = False):
        """Import only all states (no counties or cities)."""
        self.populate_ops.populate_states_only(clear_existing)
    
    def populate_kentucky_region_simple(self, clear_existing: bool = False):
        """Simplified Kentucky region populate: Always import all states, counties/cities for Kentucky region."""
        self.populate_ops.populate_kentucky_region_simple(clear_existing)
    
    def show_cache_status(self):
        """Display cache status with detailed information."""
        self.status_ops.show_cache_status()
    
    def clear_cache(self, confirm: bool = False):
        """Clear all cached files."""
        self.cache_utils.clear_cache(confirm)
    
    def cleanup_expired_cache(self):
        """Remove expired cache files."""
        self.cache_utils.cleanup_expired_cache()
    
    def show_validation_report(self):
        """Display validation report."""
        self.validation_utils.show_validation_report()
    
    def show_data_quality_report(self):
        """Display data quality report."""
        self.validation_utils.show_data_quality_report()
    
    def show_cache_stats(self):
        """Display cache statistics."""
        self.cache_utils.show_cache_stats()
    
    def show_cache_integrity_report(self):
        """Display cache integrity report."""
        self.cache_utils.show_cache_integrity_report()
    
    def show_cache_recommendations(self):
        """Display cache management recommendations."""
        self.cache_utils.show_cache_recommendations()
    
    def validate_state_coverage(self, state_fips: str):
        """Validate coverage for a specific state."""
        self.validation_utils.show_state_validation_report(state_fips)
    
    def get_available_tiger_years(self) -> List[int]:
        """Get list of available TIGER/Line years."""
        return self.validation_utils.get_available_tiger_years()
    
    def validate_tiger_year(self, year: int) -> bool:
        """Validate if a TIGER/Line year is available."""
        return self.validation_utils.validate_tiger_year(year)
    
    def get_latest_tiger_year(self) -> int:
        """Get the latest available TIGER/Line year."""
        return self.validation_utils.get_latest_tiger_year()
    
    def parse_states(self, states_input: str) -> List[str]:
        """Parse state input into FIPS codes."""
        return self.validation_utils.parse_states(states_input)
    
    def validate_state_codes(self, state_codes: List[str]) -> tuple:
        """Validate state codes and return valid and invalid ones."""
        return self.validation_utils.validate_state_codes(state_codes)
    
    def get_state_name(self, state_fips: str) -> str:
        """Get state name from FIPS code."""
        return self.validation_utils.get_state_name(state_fips)
    
    def update_states(self, states_input: str = None, year: int = None):
        """Update state data for specified states or all states."""
        self.update_ops.update_states(states_input, year)
    
    def update_counties(self, states_input: str, year: int = None):
        """Update county data for specified states."""
        self.update_ops.update_counties(states_input, year)
    
    def update_cities(self, states_input: str, year: int = None):
        """Update city data for specified states."""
        self.update_ops.update_cities(states_input, year)
    
    def update_all_data(self, states_input: str = None, year: int = None):
        """Update all geographic data for specified states."""
        self.update_ops.update_all_data(states_input, year)
    
    def update_kentucky_region(self, year: int = None):
        """Update Kentucky region data."""
        self.update_ops.update_kentucky_region(year)
    
    def clear_states_only(self, confirm: bool = False):
        """Clear only state data."""
        self.clear_ops.clear_states_only(confirm)
    
    def clear_counties_only(self, confirm: bool = False):
        """Clear only county data."""
        self.clear_ops.clear_counties_only(confirm)
    
    def clear_cities_only(self, confirm: bool = False):
        """Clear only city data."""
        self.clear_ops.clear_cities_only(confirm)
    
    def clear_by_state(self, state_fips: str, confirm: bool = False):
        """Clear data for a specific state."""
        self.clear_ops.clear_by_state(state_fips, confirm)
    
    def show_detailed_status(self):
        """Display detailed status information."""
        self.status_ops.show_detailed_status()
    
    def show_state_status(self, state_fips: str):
        """Display status for a specific state."""
        self.status_ops.show_state_status(state_fips)
