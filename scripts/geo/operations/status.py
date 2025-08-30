"""
Status Operations for Geographic Data Management

This module contains all status-related operations extracted from geo_manager.py.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')

import django
django.setup()

from directory.models import CoverageArea

# Rich imports for beautiful UI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm
from rich.align import Align
from rich import box


class StatusOperations:
    """Operations for displaying geographic data status."""
    
    def __init__(self, console: Console, logger: logging.Logger, state_mapping: Dict[str, str], cache):
        """Initialize status operations.
        
        Args:
            console: Rich console for output
            logger: Logger instance
            state_mapping: State abbreviation to FIPS code mapping
            cache: Cache instance for file information
        """
        self.console = console
        self.logger = logger
        self.state_mapping = state_mapping
        self.cache = cache
    
    def _get_status_data(self) -> Dict[str, Any]:
        """Get current status of geographic data.
        
        Returns:
            Dictionary with status information
        """
        try:
            states = CoverageArea.objects.filter(kind='STATE').count()
            counties = CoverageArea.objects.filter(kind='COUNTY').count()
            cities = CoverageArea.objects.filter(kind='CITY').count()
            
            # Get sample data
            sample_states = list(CoverageArea.objects.filter(kind='STATE').values_list('name', flat=True)[:5])
            sample_counties = list(CoverageArea.objects.filter(kind='COUNTY').values_list('name', flat=True)[:5])
            sample_cities = list(CoverageArea.objects.filter(kind='CITY').values_list('name', flat=True)[:5])
            
            return {
                'states': {'count': states, 'sample': sample_states},
                'counties': {'count': counties, 'sample': sample_counties},
                'cities': {'count': cities, 'sample': sample_cities}
            }
        except Exception as e:
            self.console.print(f"[red]Error getting status: {str(e)}[/red]")
            return {}
    
    def show_status(self):
        """Display current status with beautiful Rich formatting."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Geographic Data Status Report[/bold blue]",
            box=box.ROUNDED
        ))
        
        status = self._get_status_data()
        if not status:
            self.console.print("[red]Could not retrieve status information[/red]")
            return
        
        # Create status table
        table = Table(title="Current Coverage Areas", box=box.ROUNDED)
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("Sample Data", style="yellow")
        
        table.add_row("States", f"{status['states']['count']:,}", ", ".join(status['states']['sample']))
        table.add_row("Counties", f"{status['counties']['count']:,}", ", ".join(status['counties']['sample']))
        table.add_row("Cities", f"{status['cities']['count']:,}", ", ".join(status['cities']['sample']))
        
        total = status['states']['count'] + status['counties']['count'] + status['cities']['count']
        table.add_row("Total", f"[bold]{total:,}[/bold]", "")
        
        self.console.print(table)
        
        # Show cache status
        cache_info = self.cache.get_cache_info()
        if cache_info['cached_files']:
            self.console.print("\n[blue]📁 Cache Status:[/blue]")
            cache_table = Table(title="Cached Files", box=box.ROUNDED)
            cache_table.add_column("Type", style="cyan")
            cache_table.add_column("Year", style="green")
            cache_table.add_column("State", style="magenta")
            cache_table.add_column("Size", style="yellow")
            cache_table.add_column("Age", style="blue")
            
            for file_info in cache_info['cached_files']:
                age_text = f"{file_info['age_days']} days"
                if file_info['is_expired']:
                    age_text = f"[red]{age_text} (expired)[/red]"
                
                # Get state name for display
                state_display = file_info.get('state_fips', 'N/A')
                if file_info.get('state_fips'):
                    # Convert FIPS to state name if possible
                    state_names = {v: k for k, v in self.state_mapping.items()}
                    state_display = state_names.get(file_info['state_fips'], file_info['state_fips'])
                
                cache_table.add_row(
                    file_info['file_type'],
                    str(file_info['year']),
                    state_display,
                    f"{file_info['file_size']:,} bytes",
                    age_text
                )
            
            self.console.print(cache_table)
        
        # Add helpful message
        if total == 0:
            self.console.print("\n[yellow]No geographic data found. Use 'populate' to add data.[/yellow]")
        else:
            self.console.print(f"\n[green]✓ Found {total:,} geographic records[/green]")
    
    def show_detailed_status(self):
        """Display detailed status information including database statistics."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Detailed Geographic Data Status Report[/bold blue]",
            box=box.ROUNDED
        ))
        
        status = self._get_status_data()
        if not status:
            self.console.print("[red]Could not retrieve status information[/red]")
            return
        
        # Create detailed status table
        table = Table(title="Detailed Coverage Areas", box=box.ROUNDED)
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("Percentage", style="blue", justify="right")
        table.add_column("Sample Data", style="yellow")
        
        total = status['states']['count'] + status['counties']['count'] + status['cities']['count']
        
        if total > 0:
            states_pct = (status['states']['count'] / total) * 100
            counties_pct = (status['counties']['count'] / total) * 100
            cities_pct = (status['cities']['count'] / total) * 100
            
            table.add_row("States", f"{status['states']['count']:,}", f"{states_pct:.1f}%", ", ".join(status['states']['sample']))
            table.add_row("Counties", f"{status['counties']['count']:,}", f"{counties_pct:.1f}%", ", ".join(status['counties']['sample']))
            table.add_row("Cities", f"{status['cities']['count']:,}", f"{cities_pct:.1f}%", ", ".join(status['cities']['sample']))
            table.add_row("Total", f"[bold]{total:,}[/bold]", "100.0%", "")
        else:
            table.add_row("States", "0", "0.0%", "No data")
            table.add_row("Counties", "0", "0.0%", "No data")
            table.add_row("Cities", "0", "0.0%", "No data")
            table.add_row("Total", "[bold]0[/bold]", "0.0%", "")
        
        self.console.print(table)
        
        # Show additional statistics
        if total > 0:
            self.console.print("\n[blue]📊 Additional Statistics:[/blue]")
            stats_table = Table(box=box.ROUNDED)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green", justify="right")
            
            # Calculate average counties per state
            if status['states']['count'] > 0:
                avg_counties = status['counties']['count'] / status['states']['count']
                stats_table.add_row("Average Counties per State", f"{avg_counties:.1f}")
            
            # Calculate average cities per state
            if status['states']['count'] > 0:
                avg_cities = status['cities']['count'] / status['states']['count']
                stats_table.add_row("Average Cities per State", f"{avg_cities:.1f}")
            
            # Calculate average cities per county
            if status['counties']['count'] > 0:
                avg_cities_per_county = status['cities']['count'] / status['counties']['count']
                stats_table.add_row("Average Cities per County", f"{avg_cities_per_county:.1f}")
            
            self.console.print(stats_table)
    
    def show_state_status(self, state_fips: str):
        """Display status for a specific state.
        
        Args:
            state_fips: FIPS code of the state to check
        """
        # Convert FIPS to state name if possible
        state_names = {v: k for k, v in self.state_mapping.items()}
        state_name = state_names.get(state_fips, state_fips)
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold blue]Status Report for {state_name} ({state_fips})[/bold blue]",
            box=box.ROUNDED
        ))
        
        try:
            # Get state data
            state_count = CoverageArea.objects.filter(kind='STATE', ext_ids__state_fips=state_fips).count()
            county_count = CoverageArea.objects.filter(kind='COUNTY', ext_ids__state_fips=state_fips).count()
            city_count = CoverageArea.objects.filter(kind='CITY', ext_ids__state_fips=state_fips).count()
            
            # Get sample data
            sample_counties = list(CoverageArea.objects.filter(kind='COUNTY', ext_ids__state_fips=state_fips).values_list('name', flat=True)[:5])
            sample_cities = list(CoverageArea.objects.filter(kind='CITY', ext_ids__state_fips=state_fips).values_list('name', flat=True)[:5])
            
            # Create status table
            table = Table(title=f"Coverage Areas for {state_name}", box=box.ROUNDED)
            table.add_column("Type", style="cyan", no_wrap=True)
            table.add_column("Count", style="green", justify="right")
            table.add_column("Sample Data", style="yellow")
            
            table.add_row("State", f"{state_count:,}", state_name if state_count > 0 else "Not found")
            table.add_row("Counties", f"{county_count:,}", ", ".join(sample_counties))
            table.add_row("Cities", f"{city_count:,}", ", ".join(sample_cities))
            
            total = state_count + county_count + city_count
            table.add_row("Total", f"[bold]{total:,}[/bold]", "")
            
            self.console.print(table)
            
            if total == 0:
                self.console.print(f"\n[yellow]No data found for {state_name}. Use 'populate' to add data.[/yellow]")
            else:
                self.console.print(f"\n[green]✓ Found {total:,} records for {state_name}[/green]")
                
        except Exception as e:
            self.console.print(f"[red]Error getting status for {state_name}: {str(e)}[/red]")
    
    def show_cache_status(self):
        """Display cache status with detailed information."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]TIGER/Line Cache Status[/bold blue]",
            box=box.ROUNDED
        ))
        
        cache_info = self.cache.get_cache_info()
        
        # Show cache directory
        self.console.print(f"[blue]Cache Directory:[/blue] {cache_info['cache_dir']}")
        self.console.print(f"[blue]Max Age:[/blue] {cache_info['max_age_days']} days")
        
        if not cache_info['cached_files']:
            self.console.print("\n[yellow]No cached files found.[/yellow]")
            self.console.print("[blue]Files will be cached automatically on first download.[/blue]")
            return
        
        # Show cached files
        self.console.print(f"\n[blue]Cached Files ({len(cache_info['cached_files'])}):[/blue]")
        
        cache_table = Table(title="Cached TIGER/Line Files", box=box.ROUNDED)
        cache_table.add_column("Type", style="cyan", no_wrap=True)
        cache_table.add_column("Year", style="green", justify="right")
        cache_table.add_column("Size", style="yellow", justify="right")
        cache_table.add_column("Cached", style="blue")
        cache_table.add_column("Age", style="magenta", justify="right")
        cache_table.add_column("Status", style="red")
        
        total_size = 0
        expired_count = 0
        
        for file_info in cache_info['cached_files']:
            total_size += file_info['file_size']
            if file_info['is_expired']:
                expired_count += 1
            
            # Format cached date
            cached_date = datetime.fromisoformat(file_info['cached_at']).strftime('%Y-%m-%d %H:%M')
            
            # Format age
            age_text = f"{file_info['age_days']} days"
            
            # Status
            status = "✅ Valid" if not file_info['is_expired'] else "⚠️ Expired"
            
            cache_table.add_row(
                file_info['file_type'],
                str(file_info['year']),
                f"{file_info['file_size']:,} bytes",
                cached_date,
                age_text,
                status
            )
        
        self.console.print(cache_table)
        
        # Summary
        self.console.print(f"\n[blue]Summary:[/blue]")
        self.console.print(f"  • Total files: {len(cache_info['cached_files'])}")
        self.console.print(f"  • Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
        self.console.print(f"  • Valid files: {len(cache_info['cached_files']) - expired_count}")
        self.console.print(f"  • Expired files: {expired_count}")
        
        if expired_count > 0:
            self.console.print(f"\n[yellow]💡 Run 'cache-cleanup' to remove expired files.[/yellow]")
