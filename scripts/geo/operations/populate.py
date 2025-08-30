"""
Populate Operations for Geographic Data Management

This module contains all populate-related operations extracted from geo_manager.py.

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

from django.core.management import call_command
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


class PopulateOperations:
    """Operations for populating geographic data."""
    
    def __init__(self, console: Console, logger: logging.Logger, state_mapping: Dict[str, str], all_state_fips: List[str]):
        """Initialize populate operations.
        
        Args:
            console: Rich console for output
            logger: Logger instance
            state_mapping: State abbreviation to FIPS code mapping
            all_state_fips: List of all state FIPS codes
        """
        self.console = console
        self.logger = logger
        self.state_mapping = state_mapping
        self.all_state_fips = all_state_fips
    
    def _parse_states(self, states_input: str) -> List[str]:
        """Parse states input into FIPS codes.
        
        Args:
            states_input: Comma-separated state codes (e.g., "KY,IN" or "21,18")
            
        Returns:
            List of FIPS codes
        """
        if not states_input:
            return []
        
        states = []
        for state_code in states_input.split(','):
            state_code = state_code.strip().upper()
            
            # If it's already a FIPS code (2 digits)
            if state_code.isdigit() and len(state_code) == 2:
                states.append(state_code)
            # If it's a state abbreviation, convert to FIPS
            elif state_code in self.state_mapping:
                states.append(self.state_mapping[state_code])
            else:
                self.console.print(f"[yellow]Warning: Unknown state code '{state_code}', skipping[/yellow]")
        
        return states
    
    def _get_latest_tiger_year(self) -> int:
        """Get the latest available TIGER/Line year.
        
        Returns:
            Latest TIGER/Line year
        """
        # For now, return 2023 as the latest year
        # This could be enhanced to check available years dynamically
        return 2023
    
    def _get_status_data(self) -> Dict[str, Any]:
        """Get current status data for geographic records.
        
        Returns:
            Dictionary with status information
        """
        states_count = CoverageArea.objects.filter(kind='STATE').count()
        counties_count = CoverageArea.objects.filter(kind='COUNTY').count()
        cities_count = CoverageArea.objects.filter(kind='CITY').count()
        
        return {
            'states': {'count': states_count},
            'counties': {'count': counties_count},
            'cities': {'count': cities_count}
        }
    
    def populate_data(self, states_input: str, year: int = 2023, clear_existing: bool = False):
        """Populate geographic data for specified states.
        
        Args:
            states_input: Comma-separated state codes
            year: TIGER/Line data year
            clear_existing: Whether to clear existing data first
        """
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
        """Simplified populate: Always import all states, optionally import counties/cities for specific states.
        
        Args:
            states_input: Comma-separated state codes for counties/cities
            clear_existing: Whether to clear existing data first
        """
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
            # Note: This would need to call clear_data from another operations class
            # For now, we'll just show the message
        
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
        """Import only all states (no counties or cities).
        
        Args:
            clear_existing: Whether to clear existing data first
        """
        # Auto-detect latest year
        year = self._get_latest_tiger_year()
        
        self.console.print(f"\n[blue]🌍 States-Only Import[/blue]")
        self.console.print(f"[blue]Importing:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            # Note: This would need to call clear_data from another operations class
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Importing states...", total=1)
            try:
                call_command('import_states_enhanced', all_states=True, year=year, clear_existing=clear_existing)
                progress.update(task, completed=1)
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
        results_table = Table(title="Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported all states and territories![/green]")
        self.console.print(f"[blue]Total:[/blue] {final_status['states']['count']:,} states and territories")
    
    def populate_kentucky_region(self, year: int = 2023, clear_existing: bool = False):
        """Populate Kentucky region data (Kentucky + bordering states).
        
        Args:
            year: TIGER/Line data year
            clear_existing: Whether to clear existing data first
        """
        # Kentucky and bordering states
        kentucky_region = ['21', '18', '39', '47', '54', '51', '37']  # KY, IN, OH, TN, WV, VA, NC
        state_names = ['Kentucky', 'Indiana', 'Ohio', 'Tennessee', 'West Virginia', 'Virginia', 'North Carolina']
        
        self.console.print(f"\n[blue]🌍 Kentucky Region Import[/blue]")
        self.console.print(f"[blue]Importing:[/blue] Kentucky + {len(state_names)-1} bordering states")
        self.console.print(f"[blue]States:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            # Note: This would need to call clear_data from another operations class
        
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
            task1 = progress.add_task("Importing states...", total=len(kentucky_region))
            try:
                call_command('import_states_enhanced', states=','.join(kentucky_region), year=year, clear_existing=clear_existing)
                progress.update(task1, completed=len(kentucky_region))
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties
            task2 = progress.add_task("Importing counties...", total=len(kentucky_region))
            try:
                call_command('import_counties_enhanced', states=','.join(kentucky_region), year=year, clear_existing=clear_existing)
                progress.update(task2, completed=len(kentucky_region))
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities
            task3 = progress.add_task("Importing cities...", total=len(kentucky_region))
            try:
                call_command('import_cities_enhanced', states=','.join(kentucky_region), year=year, clear_existing=clear_existing)
                progress.update(task3, completed=len(kentucky_region))
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
        results_table = Table(title="Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported Kentucky region data![/green]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
    
    def populate_kentucky_region_simple(self, clear_existing: bool = False):
        """Simplified Kentucky region populate: Always import all states, counties/cities for Kentucky region.
        
        Args:
            clear_existing: Whether to clear existing data first
        """
        # Auto-detect latest year
        year = self._get_latest_tiger_year()
        
        # Kentucky and bordering states
        kentucky_region = ['21', '18', '39', '47', '54', '51', '37']  # KY, IN, OH, TN, WV, VA, NC
        state_names = ['Kentucky', 'Indiana', 'Ohio', 'Tennessee', 'West Virginia', 'Virginia', 'North Carolina']
        
        self.console.print(f"\n[blue]🌍 Kentucky Region Import (Simple)[/blue]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories (always imported)")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        if clear_existing:
            self.console.print(f"\n[yellow]⚠️  Clearing existing data before import...[/yellow]")
            # Note: This would need to call clear_data from another operations class
        
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
                call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error importing states: {str(e)}[/red]")
                return
            
            # Import counties for Kentucky region
            task2 = progress.add_task("Importing counties...", total=1)
            try:
                call_command('import_counties_enhanced', states=','.join(kentucky_region), year=year, clear_existing=clear_existing)
                progress.update(task2, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error importing counties: {str(e)}[/red]")
                return
            
            # Import cities for Kentucky region
            task3 = progress.add_task("Importing cities...", total=1)
            try:
                call_command('import_cities_enhanced', states=','.join(kentucky_region), year=year, clear_existing=clear_existing)
                progress.update(task3, completed=1)
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
        results_table = Table(title="Import Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Imported", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Imported", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Imported", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully imported Kentucky region data![/green]")
        self.console.print(f"[blue]States:[/blue] All 57 states and territories")
        self.console.print(f"[blue]Counties & Cities:[/blue] Kentucky + {len(state_names)-1} bordering states")
