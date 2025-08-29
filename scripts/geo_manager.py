#!/usr/bin/env python3
"""
Geographic Data Manager CLI

A beautiful, user-friendly command-line interface for managing geographic data
with standardized output, progress tracking, and easy-to-use commands.

Features:
- Beautiful Rich-based UI with progress bars and status updates
- Standardized, friendly text messages
- Easy commands for populate, clear, update, and status
- Clear understanding of each step's progress
- Simple CLI structure for common operations

Usage:
    python scripts/geo_manager.py status
    python scripts/geo_manager.py populate --states KY,IN
    python scripts/geo_manager.py clear
    python scripts/geo_manager.py update --states KY

Author: Resource Directory Team
Created: 2025-01-15
Version: 3.0.0
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional, Tuple
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
from django.contrib.auth.models import User
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
    
    def _parse_states(self, states_input: str) -> List[str]:
        """Parse state input (e.g., 'KY,IN' or '21,18') into FIPS codes."""
        if not states_input:
            return []
        
        states = [s.strip().upper() for s in states_input.split(',')]
        fips_codes = []
        
        for state in states:
            if state in self.state_mapping:
                fips_codes.append(self.state_mapping[state])
            elif state in self.state_mapping.values():
                fips_codes.append(state)
            else:
                self.console.print(f"[red]Warning: Unknown state '{state}'[/red]")
        
        return fips_codes
    
    def _get_status_data(self) -> Dict[str, Any]:
        """Get current status of geographic data."""
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
    
    def clear_data(self, confirm: bool = False):
        """Clear all geographic data."""
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL geographic data![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        else:
            # No confirmation needed, proceed directly
            pass
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Clearing geographic data...", total=None)
            
            try:
                # Get counts before deletion
                states_count = CoverageArea.objects.filter(kind='STATE').count()
                counties_count = CoverageArea.objects.filter(kind='COUNTY').count()
                cities_count = CoverageArea.objects.filter(kind='CITY').count()
                
                # Delete all geographic data
                CoverageArea.objects.filter(kind__in=['STATE', 'COUNTY', 'CITY']).delete()
                
                progress.update(task, description="✅ Data cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared:[/green]")
                self.console.print(f"  • {states_count:,} states")
                self.console.print(f"  • {counties_count:,} counties") 
                self.console.print(f"  • {cities_count:,} cities")
                self.console.print(f"  • Total: {states_count + counties_count + cities_count:,} records")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing data: {str(e)}[/red]")
                self.logger.error(f"Error clearing data: {str(e)}")
    
    def populate_data(self, states_input: str, year: int = 2023, clear_existing: bool = False):
        """Populate geographic data for specified states."""
        states = self._parse_states(states_input)
        
        if not states:
            self.console.print("[red]No valid states specified. Use format: KY,IN or 21,18[/red]")
            return
        
        # Show what we're about to do
        state_names = [k for k, v in self.state_mapping.items() if v in states]
        self.console.print(f"\n[blue]Preparing to populate data for:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print("[yellow]Will clear existing data before import[/yellow]")
        
        # Show warning for clearing existing data
        if clear_existing:
            self.console.print("[yellow]⚠️  Will clear existing data before import[/yellow]")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Import states
            task1 = progress.add_task("Importing states...", total=len(states))
            try:
                # Use optimized import for all states, regular import for specific states
                if len(states) == len(self.all_state_fips):
                    # Importing all states - use optimized approach
                    call_command('import_states_enhanced', all_states=True, year=year, clear_existing=clear_existing)
                else:
                    # Importing specific states - use regular approach
                    call_command('import_states_enhanced', states=','.join(states), year=year, clear_existing=clear_existing)
                progress.update(task1, completed=len(states))
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties
            task2 = progress.add_task("Importing counties...", total=len(states))
            try:
                call_command('import_counties_enhanced', states=','.join(states), year=year, clear_existing=clear_existing)
                progress.update(task2, completed=len(states))
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities
            task3 = progress.add_task("Importing cities...", total=len(states))
            try:
                call_command('import_cities_enhanced', states=','.join(states), year=year, clear_existing=clear_existing)
                progress.update(task3, completed=len(states))
            except Exception as e:
                self.console.print(f"\n[red]Error importing cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Population Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully populated geographic data for {len(states)} states![/green]")
    
    def populate_data_simple(self, states_input: str, clear_existing: bool = False):
        """Simplified populate: Always import all states, optionally import counties/cities for specific states."""
        states = self._parse_states(states_input)
        
        if not states:
            self.console.print("[red]No valid states specified for counties/cities. Use format: KY,IN or 21,18[/red]")
            return
        
        # Auto-detect latest year
        year = self._get_latest_tiger_year()
        
        # Show what we're about to do
        state_names = [k for k, v in self.state_mapping.items() if v in states]
        self.console.print(f"\n[blue]🌍 Geographic Data Import[/blue]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories (always imported)")
        self.console.print(f"[blue]Counties & Cities:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            self.clear_data(confirm=True)
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Import all states first (optimized - single download)
            task1 = progress.add_task("Importing all states...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 1: Downloading state boundary data...[/blue]")
                self.console.print(f"[blue]   This will download maps for all 50 states plus territories[/blue]")
                self.console.print(f"[blue]   This may take a minute or two depending on your internet speed.[/blue]")
                call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
                self.console.print(f"[green]✅ States imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties for specified states
            task2 = progress.add_task("Importing counties...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 2: Downloading county boundary data...[/blue]")
                self.console.print(f"[blue]   This will download county maps for: {', '.join(state_names)}[/blue]")
                self.console.print(f"[blue]   This may take a few minutes depending on your internet speed.[/blue]")
                
                # Show progress per state for counties
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=self.console
                ) as county_progress:
                    county_task = county_progress.add_task("Processing counties...", total=len(states))
                    
                    # Process each state individually to show progress
                    for i, state_fips in enumerate(states):
                        try:
                            county_progress.update(county_task, description=f"Processing counties for state {state_fips}...")
                            call_command('import_counties_enhanced', states=state_fips, year=year, clear_existing=clear_existing)
                            county_progress.update(county_task, advance=1)
                        except Exception as e:
                            self.console.print(f"\n[red]Error importing counties for state {state_fips}: {str(e)}[/red]")
                            return
                
                progress.update(task2, completed=1)
                self.console.print(f"[green]✅ Counties imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities for specified states
            task3 = progress.add_task("Importing cities...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 3: Downloading city boundary data...[/blue]")
                self.console.print(f"[blue]   This will download city maps for: {', '.join(state_names)}[/blue]")
                self.console.print(f"[blue]   This may take several minutes as there are many cities.[/blue]")
                
                # Show progress per state for cities
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=self.console
                ) as city_progress:
                    city_task = city_progress.add_task("Processing cities...", total=len(states))
                    
                    # Process each state individually to show progress
                    for i, state_fips in enumerate(states):
                        try:
                            city_progress.update(city_task, description=f"Processing cities for state {state_fips}...")
                            call_command('import_cities_enhanced', states=state_fips, year=year, clear_existing=clear_existing)
                            city_progress.update(city_task, advance=1)
                        except Exception as e:
                            self.console.print(f"\n[red]Error importing cities for state {state_fips}: {str(e)}[/red]")
                            return
                
                progress.update(task3, completed=1)
                self.console.print(f"[green]✅ Cities imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Import Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported geographic data![/green]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Counties & Cities:[/blue] {', '.join(state_names)}")
    
    def populate_states_only(self, clear_existing: bool = False):
        """Import only all states (no counties or cities)."""
        # Auto-detect latest year
        year = self._get_latest_tiger_year()
        
        self.console.print(f"\n[blue]🌍 States-Only Import[/blue]")
        self.console.print(f"[blue]Importing:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            self.clear_data(confirm=True)
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Import all states (optimized - single download)
            task1 = progress.add_task("Importing all states...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Downloading state boundary data...[/blue]")
                self.console.print(f"[blue]   This will download maps for all 50 states plus territories[/blue]")
                self.console.print(f"[blue]   This may take a minute or two depending on your internet speed.[/blue]")
                call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
                self.console.print(f"[green]✅ States imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ States Import Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="States Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported all states![/green]")
        self.console.print(f"[blue]Counties and cities can be imported later with:[/blue] python scripts/geo_manager.py populate KY,IN,IL")
    
    def populate_kentucky_region(self, year: int = 2023, clear_existing: bool = False):
        """Populate geographic data for Kentucky and its bordering states."""
        # Kentucky and its bordering states
        kentucky_region_states = {
            'KY': '21',  # Kentucky
            'IN': '18',  # Indiana
            'IL': '17',  # Illinois
            'MO': '29',  # Missouri
            'TN': '47',  # Tennessee
            'VA': '51',  # Virginia
            'WV': '54',  # West Virginia
            'OH': '39',  # Ohio
        }
        
        state_names = list(kentucky_region_states.keys())
        state_fips = list(kentucky_region_states.values())
        
        self.console.print(f"\n[blue]🌍 Kentucky Region Import[/blue]")
        self.console.print(f"[blue]Importing data for Kentucky and bordering states:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            self.clear_data(confirm=True)
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Import all states first (optimized - single download)
            task1 = progress.add_task("Importing all states...", total=1)
            try:
                # Use optimized import that downloads file once and processes all states
                call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties for Kentucky region (optimized - single download)
            task2 = progress.add_task("Importing counties for Kentucky region...", total=len(state_fips))
            try:
                # Download county file once and process all states
                self._import_counties_optimized(state_fips, year, clear_existing, progress, task2)
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities for Kentucky region
            task3 = progress.add_task("Importing cities for Kentucky region...", total=len(state_fips))
            try:
                # Process cities individually to show real progress
                for i, state_fips in enumerate(state_fips):
                    call_command('import_cities_enhanced', states=state_fips, year=year, clear_existing=clear_existing)
                    progress.update(task3, completed=i+1)
            except Exception as e:
                self.console.print(f"\n[red]Error importing cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Kentucky Region Import Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Kentucky Region Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("All States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported (KY Region)", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported (KY Region)", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported Kentucky region data![/green]")
        self.console.print(f"[blue]States:[/blue] All 50 states + territories")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
    
    def populate_kentucky_region_simple(self, clear_existing: bool = False):
        """Simplified Kentucky region import: All states + KY region counties/cities."""
        # Auto-detect latest year
        year = self._get_latest_tiger_year()
        
        # Kentucky and its bordering states
        kentucky_region_states = {
            'KY': '21',  # Kentucky
            'IN': '18',  # Indiana
            'IL': '17',  # Illinois
            'MO': '29',  # Missouri
            'TN': '47',  # Tennessee
            'VA': '51',  # Virginia
            'WV': '54',  # West Virginia
            'OH': '39',  # Ohio
        }
        
        state_names = list(kentucky_region_states.keys())
        state_fips = list(kentucky_region_states.values())
        
        self.console.print(f"\n[blue]🌍 Kentucky Region Import[/blue]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories (always imported)")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            self.clear_data(confirm=True)
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Import all states first (optimized - single download)
            task1 = progress.add_task("Importing all states...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 1: Downloading state boundary data...[/blue]")
                self.console.print(f"[blue]   This will download maps for all 50 states plus territories[/blue]")
                self.console.print(f"[blue]   This may take a minute or two depending on your internet speed.[/blue]")
                call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
                self.console.print(f"[green]✅ States imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties for Kentucky region
            task2 = progress.add_task("Importing counties for Kentucky region...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 2: Downloading county boundary data...[/blue]")
                self.console.print(f"[blue]   This will download county maps for Kentucky and bordering states[/blue]")
                self.console.print(f"[blue]   This may take a few minutes depending on your internet speed.[/blue]")
                
                # Show progress per state for counties
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=self.console
                ) as county_progress:
                    county_task = county_progress.add_task("Processing counties...", total=len(state_fips))
                    
                    # Process each state individually to show progress
                    for i, state_fips_code in enumerate(state_fips):
                        try:
                            county_progress.update(county_task, description=f"Processing counties for state {state_fips_code}...")
                            call_command('import_counties_enhanced', states=state_fips_code, year=year, clear_existing=clear_existing)
                            county_progress.update(county_task, advance=1)
                        except Exception as e:
                            self.console.print(f"\n[red]Error importing counties for state {state_fips_code}: {str(e)}[/red]")
                            return
                
                progress.update(task2, completed=1)
                self.console.print(f"[green]✅ Counties imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities for Kentucky region
            task3 = progress.add_task("Importing cities for Kentucky region...", total=1)
            try:
                self.console.print(f"\n[blue]📥 Step 3: Downloading city boundary data...[/blue]")
                self.console.print(f"[blue]   This will download city maps for Kentucky and bordering states[/blue]")
                self.console.print(f"[blue]   This may take several minutes as there are many cities.[/blue]")
                
                # Show progress per state for cities
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=self.console
                ) as city_progress:
                    city_task = city_progress.add_task("Processing cities...", total=len(state_fips))
                    
                    # Process each state individually to show progress
                    for i, state_fips_code in enumerate(state_fips):
                        try:
                            city_progress.update(city_task, description=f"Processing cities for state {state_fips_code}...")
                            call_command('import_cities_enhanced', states=state_fips_code, year=year, clear_existing=clear_existing)
                            city_progress.update(city_task, advance=1)
                        except Exception as e:
                            self.console.print(f"\n[red]Error importing cities for state {state_fips_code}: {str(e)}[/red]")
                            return
                
                progress.update(task3, completed=1)
                self.console.print(f"[green]✅ Cities imported successfully![/green]")
            except Exception as e:
                self.console.print(f"\n[red]Error importing cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Kentucky Region Import Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Kentucky Region Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported (KY Region)", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported (KY Region)", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported Kentucky region data![/green]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
    
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
    
    def clear_cache(self, confirm: bool = False):
        """Clear all cached files."""
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL cached TIGER/Line files![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        else:
            # No confirmation needed, proceed directly
            pass
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Clearing cache...", total=None)
            
            try:
                # Get cache info before clearing
                cache_info = self.cache.get_cache_info()
                file_count = len(cache_info['cached_files'])
                total_size = sum(f['file_size'] for f in cache_info['cached_files'])
                
                # Clear cache
                self.cache.clear_cache()
                
                progress.update(task, description="✅ Cache cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared cache:[/green]")
                self.console.print(f"  • Files removed: {file_count}")
                self.console.print(f"  • Space freed: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing cache: {str(e)}[/red]")
                self.logger.error(f"Error clearing cache: {str(e)}")
    
    def cleanup_expired_cache(self):
        """Remove expired cache files."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Checking for expired files...", total=None)
            
            try:
                # Get cache info
                cache_info = self.cache.get_cache_info()
                expired_files = [f for f in cache_info['cached_files'] if f['is_expired']]
                
                if not expired_files:
                    progress.update(task, description="✅ No expired files found")
                    self.console.print(f"\n[green]No expired files to clean up.[/green]")
                    return
                
                progress.update(task, description=f"Removing {len(expired_files)} expired files...")
                
                # Clean up expired files
                self.cache.cleanup_expired()
                
                progress.update(task, description="✅ Cleanup completed")
                
                total_size = sum(f['file_size'] for f in expired_files)
                self.console.print(f"\n[green]Successfully cleaned up expired cache:[/green]")
                self.console.print(f"  • Files removed: {len(expired_files)}")
                self.console.print(f"  • Space freed: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
                
            except Exception as e:
                self.console.print(f"\n[red]Error cleaning up cache: {str(e)}[/red]")
                self.logger.error(f"Error cleaning up cache: {str(e)}")
    
    def _get_latest_tiger_year(self) -> int:
        """Auto-detect the latest available TIGER/Line year."""
        import urllib.request
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # Try the last few years to find the latest available
        for year in range(current_year, current_year - 3, -1):
            try:
                # Test if the states file exists
                url = f"https://www2.census.gov/geo/tiger/TIGER{year}/STATE/tl_{year}_us_state.zip"
                response = urllib.request.urlopen(url, timeout=5)
                if response.getcode() == 200:
                    return year
            except:
                continue
        
        # Fallback to 2023 if we can't detect
        return 2023
    
    def _import_counties_optimized(self, state_fips_list: List[str], year: int, clear_existing: bool, progress=None, task_id=None):
        """Optimized county import - download once, process all states."""
        import tempfile
        import zipfile
        import json
        import urllib.request
        from directory.models import CoverageArea
        from django.contrib.auth.models import User
        from django.contrib.gis.geos import GEOSGeometry
        from directory.management.commands.import_counties_enhanced import ColoredUI
        
        ui = ColoredUI()
        ui.header("Optimized County Import")
        
        # Clear existing data if requested
        if clear_existing:
            ui.step("Clearing existing county data...")
            deleted_count = CoverageArea.objects.filter(kind='COUNTY').delete()[0]
            ui.success(f"Deleted {deleted_count} existing county records")
        
        # Download county file once
        ui.step("Downloading county shapefile (once for all states)...")
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip"
        filename = f"tl_{year}_us_county.zip"
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        zip_path = temp_file.name
        temp_file.close()
        
        # Download with progress bar
        try:
            with urllib.request.urlopen(url) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            ui.progress(f"Downloading {filename}", downloaded_size, total_size)
                
                ui.success(f"Download completed! ({downloaded_size:,} bytes)")
                
        except Exception as e:
            ui.error(f"Download failed: {str(e)}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise
        
        try:
            # Extract and convert to GeoJSON once
            ui.step("Extracting and converting county data...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Find the shapefile
                    shapefile_path = None
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith('.shp'):
                                shapefile_path = os.path.join(root, file)
                                break
                        if shapefile_path:
                            break
                    
                    if not shapefile_path:
                        ui.error(f"No shapefile found in {zip_path}")
                        return
                    
                    ui.info(f"Found shapefile: {os.path.basename(shapefile_path)} ({os.path.getsize(shapefile_path):,} bytes)")
                    
                    # Convert to GeoJSON
                    ui.info("Converting shapefile to GeoJSON...")
                    import uuid
                    geojson_path = os.path.join(tempfile.gettempdir(), f"county_import_{uuid.uuid4().hex}.geojson")
                    
                    cmd = f'ogr2ogr -f GeoJSON -t_srs EPSG:4326 "{geojson_path}" "{shapefile_path}"'
                    ui.info(f"Running: {cmd}")
                    
                    result = os.system(cmd)
                    if result != 0:
                        ui.error("Shapefile conversion failed")
                        raise Exception("ogr2ogr conversion failed")
                    
                    ui.success("Shapefile converted successfully")
                    
                    # Process all states from the same GeoJSON file
                    ui.step("Processing counties for all states...")
                    total_imported = 0
                    total_errors = 0
                    
                    # Get default user
                    try:
                        default_user = User.objects.first()
                    except:
                        default_user = User.objects.create_user(
                            username='import_user',
                            email='import@example.com',
                            password='temp_password_123'
                        )
                    
                    # Load GeoJSON data once
                    with open(geojson_path, 'r') as f:
                        geojson_data = json.load(f)
                    
                    features = geojson_data.get('features', [])
                    ui.info(f"Processing {len(features)} county features...")
                    
                    # Filter features for our target states
                    target_features = [
                        f for f in features 
                        if f.get('properties', {}).get('STATEFP') in state_fips_list
                    ]
                    
                    ui.info(f"Found {len(target_features)} counties for target states")
                    
                    # Process each state
                    for i, state_fips in enumerate(state_fips_list):
                        state_features = [f for f in target_features if f.get('properties', {}).get('STATEFP') == state_fips]
                        ui.info(f"Processing {len(state_features)} counties for state {state_fips}...")
                        
                        # Update progress if available
                        if progress and task_id is not None:
                            progress.update(task_id, completed=i+1)
                        
                        imported_count = 0
                        error_count = 0
                        
                        for feature in state_features:
                            try:
                                properties = feature.get('properties', {})
                                geometry = feature.get('geometry')
                                
                                if not geometry or not properties:
                                    continue
                                
                                county_name = properties.get('NAME', 'Unknown County')
                                county_fips = properties.get('COUNTYFP', '')
                                
                                if not county_fips:
                                    continue
                                
                                # Create full county name
                                full_county_name = f"{county_name} County"
                                
                                # Check if county already exists
                                existing_county = CoverageArea.objects.filter(
                                    kind='COUNTY',
                                    ext_ids__county_fips=county_fips,
                                    ext_ids__state_fips=state_fips
                                ).first()
                                
                                # Create or update county
                                geom_obj = GEOSGeometry(json.dumps(geometry))
                                
                                # Convert single polygon to multipolygon if needed
                                if geom_obj.geom_type == 'Polygon':
                                    from django.contrib.gis.geos import MultiPolygon
                                    geom_obj = MultiPolygon([geom_obj])
                                
                                if existing_county:
                                    existing_county.name = full_county_name
                                    existing_county.geom = geom_obj
                                    existing_county.updated_by = default_user
                                    existing_county.save()
                                else:
                                    CoverageArea.objects.create(
                                        kind='COUNTY',
                                        name=full_county_name,
                                        geom=geom_obj,
                                        ext_ids={
                                            'state_fips': state_fips,
                                            'county_fips': county_fips
                                        },
                                        created_by=default_user,
                                        updated_by=default_user
                                    )
                                
                                imported_count += 1
                                
                            except Exception as e:
                                ui.error(f"Error importing county feature: {str(e)}")
                                error_count += 1
                                continue
                        
                        total_imported += imported_count
                        total_errors += error_count
                        ui.success(f"Imported {imported_count} counties for state {state_fips}")
                    
                    # Cleanup GeoJSON file
                    if os.path.exists(geojson_path):
                        os.remove(geojson_path)
            
            # Display summary
            success_rate = (total_imported / (total_imported + total_errors)) * 100 if (total_imported + total_errors) > 0 else 0
            ui.summary("Optimized County Import Summary", {
                "Counties Imported": total_imported,
                "Errors Encountered": total_errors,
                "Success Rate": f"{success_rate:.1f}%"
            })
            
            if total_errors > 0:
                ui.warning(f"⚠️ {total_errors} errors occurred during import")
            else:
                ui.success("🎉 All county imports completed successfully!")
                
        finally:
            # Cleanup zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def show_help(self):
        """Show comprehensive help information."""
        help_text = """
[bold blue]Geographic Data Manager[/bold blue]

A simple CLI for managing geographic data from US Census Bureau TIGER/Line files.

[bold cyan]Commands:[/bold cyan]

[green]status[/green]                    Show current geographic data status
[green]populate [states][/green]         Import all states + counties/cities for specified states
[green]clear[/green]                     Clear all geographic data
[green]kentucky-region[/green]           Import all states + KY region counties/cities
[green]cache-status[/green]              Show cache status and information
[green]cache-clear[/green]               Clear all cached files
[green]cache-cleanup[/green]             Remove expired cache files
[green]help[/green]                      Show this help message

[bold cyan]State Formats:[/bold cyan]
• Use state abbreviations: KY, IN, CA, NY
• Use FIPS codes: 21, 18, 06, 36
• Use 'all' for all states
• Leave empty for states only

[bold cyan]Examples:[/bold cyan]
• python scripts/geo_manager.py status
• python scripts/geo_manager.py populate KY,IN,IL,MO,TN,VA,WV,OH
• python scripts/geo_manager.py populate all
• python scripts/geo_manager.py populate
• python scripts/geo_manager.py clear
• python scripts/geo_manager.py kentucky-region
• python scripts/geo_manager.py cache-status
• python scripts/geo_manager.py cache-clear

[bold cyan]Notes:[/bold cyan]
• States are ALWAYS imported (all 57 states/territories)
• Counties and cities are imported for specified states only
• Year is auto-detected (latest available)
• Files are cached to avoid re-downloading (30-day expiration)
• Use 'populate' for new installations
• Commands are non-interactive by default
• Use --clear-existing to clear data before import
        """
        
        self.console.print(Panel(help_text, title="Help", box=box.ROUNDED))

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Geographic Data Manager - Simple CLI for managing geographic data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/geo_manager.py status
  python scripts/geo_manager.py populate KY,IN,IL,MO,TN,VA,WV,OH
  python scripts/geo_manager.py populate all
  python scripts/geo_manager.py clear
  python scripts/geo_manager.py kentucky-region
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'populate', 'clear', 'kentucky-region', 'cache-status', 'cache-clear', 'cache-cleanup', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'states',
        nargs='?',
        type=str,
        help='States for counties/cities (e.g., KY,IN,IL or "all"). States are always imported.'
    )
    
    parser.add_argument(
        '--clear-existing',
        action='store_true',
        help='Clear existing data before populate (use with caution)'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = GeographicDataManager()
    
    try:
        if args.command == 'help':
            manager.show_help()
        
        elif args.command == 'status':
            manager.show_status()
        
        elif args.command == 'clear':
            manager.clear_data(confirm=args.no_confirm)
        
        elif args.command == 'populate':
            # Always import all states, optionally import counties/cities for specific states
            if args.states:
                states_input = args.states
                if states_input.lower() == 'all':
                    states_input = ','.join(manager.all_state_fips)
                
                manager.populate_data_simple(
                    states_input=states_input,
                    clear_existing=args.clear_existing
                )
            else:
                # Just import all states
                manager.populate_states_only(clear_existing=args.clear_existing)
        
        elif args.command == 'kentucky-region':
            manager.populate_kentucky_region_simple(clear_existing=args.clear_existing)
        
        elif args.command == 'cache-status':
            manager.show_cache_status()
        
        elif args.command == 'cache-clear':
            manager.clear_cache(confirm=not args.no_confirm)
        
        elif args.command == 'cache-cleanup':
            manager.cleanup_expired_cache()
    
    except KeyboardInterrupt:
        manager.console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        manager.console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
