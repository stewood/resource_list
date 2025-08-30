"""
Update Operations for Geographic Data Management

This module contains all update-related operations extracted from geo_manager.py.

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


class UpdateOperations:
    """Operations for updating geographic data."""
    
    def __init__(self, console: Console, logger: logging.Logger, state_mapping: Dict[str, str], all_state_fips: List[str]):
        """Initialize update operations.
        
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
    
    def update_states(self, states_input: str = None, year: int = None):
        """Update state data for specified states or all states.
        
        Args:
            states_input: Comma-separated state codes (if None, updates all states)
            year: TIGER/Line data year (if None, uses latest)
        """
        if year is None:
            year = self._get_latest_tiger_year()
        
        if states_input:
            states = self._parse_states(states_input)
            if not states:
                self.console.print("[red]No valid states specified. Use format: KY,IN or 21,18[/red]")
                return
            
            state_names = [k for k, v in self.state_mapping.items() if v in states]
            self.console.print(f"\n[blue]Updating states:[/blue] {', '.join(state_names)}")
        else:
            self.console.print(f"\n[blue]Updating all states[/blue]")
        
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Updating states...", total=1)
            try:
                if states_input:
                    call_command('import_states_enhanced', states=','.join(states), year=year, update_existing=True)
                else:
                    call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating states: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.console.print(f"\n[green]✅ States updated successfully![/green]")
        self.console.print(f"[blue]Duration:[/blue] {str(duration).split('.')[0]}")
    
    def update_counties(self, states_input: str, year: int = None):
        """Update county data for specified states.
        
        Args:
            states_input: Comma-separated state codes
            year: TIGER/Line data year (if None, uses latest)
        """
        if year is None:
            year = self._get_latest_tiger_year()
        
        states = self._parse_states(states_input)
        if not states:
            self.console.print("[red]No valid states specified. Use format: KY,IN or 21,18[/red]")
            return
        
        state_names = [k for k, v in self.state_mapping.items() if v in states]
        self.console.print(f"\n[blue]Updating counties for:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Updating counties...", total=1)
            try:
                call_command('import_counties_enhanced', states=','.join(states), year=year, update_existing=True)
                progress.update(task, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating counties: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.console.print(f"\n[green]✅ Counties updated successfully![/green]")
        self.console.print(f"[blue]Duration:[/blue] {str(duration).split('.')[0]}")
    
    def update_cities(self, states_input: str, year: int = None):
        """Update city data for specified states.
        
        Args:
            states_input: Comma-separated state codes
            year: TIGER/Line data year (if None, uses latest)
        """
        if year is None:
            year = self._get_latest_tiger_year()
        
        states = self._parse_states(states_input)
        if not states:
            self.console.print("[red]No valid states specified. Use format: KY,IN or 21,18[/red]")
            return
        
        state_names = [k for k, v in self.state_mapping.items() if v in states]
        self.console.print(f"\n[blue]Updating cities for:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Updating cities...", total=1)
            try:
                call_command('import_cities_enhanced', states=','.join(states), year=year, update_existing=True)
                progress.update(task, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.console.print(f"\n[green]✅ Cities updated successfully![/green]")
        self.console.print(f"[blue]Duration:[/blue] {str(duration).split('.')[0]}")
    
    def update_all_data(self, states_input: str = None, year: int = None):
        """Update all geographic data (states, counties, cities) for specified states.
        
        Args:
            states_input: Comma-separated state codes (if None, updates all states)
            year: TIGER/Line data year (if None, uses latest)
        """
        if year is None:
            year = self._get_latest_tiger_year()
        
        if states_input:
            states = self._parse_states(states_input)
            if not states:
                self.console.print("[red]No valid states specified. Use format: KY,IN or 21,18[/red]")
                return
            
            state_names = [k for k, v in self.state_mapping.items() if v in states]
            self.console.print(f"\n[blue]Updating all data for:[/blue] {', '.join(state_names)}")
        else:
            self.console.print(f"\n[blue]Updating all data for all states[/blue]")
        
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Update states
            task1 = progress.add_task("Updating states...", total=1)
            try:
                if states_input:
                    call_command('import_states_enhanced', states=','.join(states), year=year, update_existing=True)
                else:
                    call_command('import_states_enhanced', all_states=True, year=year, update_existing=True)
                progress.update(task1, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating states: {str(e)}[/red]")
                return
            
            # Update counties
            task2 = progress.add_task("Updating counties...", total=1)
            try:
                if states_input:
                    call_command('import_counties_enhanced', states=','.join(states), year=year, update_existing=True)
                else:
                    # For all states, we need to process them in batches
                    for state_fips in self.all_state_fips:
                        call_command('import_counties_enhanced', states=state_fips, year=year, update_existing=True)
                progress.update(task2, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating counties: {str(e)}[/red]")
                return
            
            # Update cities
            task3 = progress.add_task("Updating cities...", total=1)
            try:
                if states_input:
                    call_command('import_cities_enhanced', states=','.join(states), year=year, update_existing=True)
                else:
                    # For all states, we need to process them in batches
                    for state_fips in self.all_state_fips:
                        call_command('import_cities_enhanced', states=state_fips, year=year, update_existing=True)
                progress.update(task3, completed=1)
            except Exception as e:
                self.console.print(f"\n[red]Error updating cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Update Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Update Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Updated", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Updated", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Updated", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully updated geographic data![/green]")
    
    def update_kentucky_region(self, year: int = None):
        """Update Kentucky region data (Kentucky + bordering states).
        
        Args:
            year: TIGER/Line data year (if None, uses latest)
        """
        if year is None:
            year = self._get_latest_tiger_year()
        
        # Kentucky and bordering states
        kentucky_region = ['21', '18', '39', '47', '54', '51', '37']  # KY, IN, OH, TN, WV, VA, NC
        state_names = ['Kentucky', 'Indiana', 'Ohio', 'Tennessee', 'West Virginia', 'Virginia', 'North Carolina']
        
        self.console.print(f"\n[blue]🌍 Updating Kentucky Region[/blue]")
        self.console.print(f"[blue]States:[/blue] {', '.join(state_names)}")
        self.console.print(f"[blue]Using TIGER/Line data from year:[/blue] {year}")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Update states
            task1 = progress.add_task("Updating states...", total=len(kentucky_region))
            try:
                call_command('import_states_enhanced', states=','.join(kentucky_region), year=year, update_existing=True)
                progress.update(task1, completed=len(kentucky_region))
            except Exception as e:
                self.console.print(f"\n[red]Error updating states: {str(e)}[/red]")
                return
            
            # Update counties
            task2 = progress.add_task("Updating counties...", total=len(kentucky_region))
            try:
                call_command('import_counties_enhanced', states=','.join(kentucky_region), year=year, update_existing=True)
                progress.update(task2, completed=len(kentucky_region))
            except Exception as e:
                self.console.print(f"\n[red]Error updating counties: {str(e)}[/red]")
                return
            
            # Update cities
            task3 = progress.add_task("Updating cities...", total=len(kentucky_region))
            try:
                call_command('import_cities_enhanced', states=','.join(kentucky_region), year=year, update_existing=True)
                progress.update(task3, completed=len(kentucky_region))
            except Exception as e:
                self.console.print(f"\n[red]Error updating cities: {str(e)}[/red]")
                return
        
        # Calculate duration and show results
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get final status
        final_status = self._get_status_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]✅ Kentucky Region Update Complete![/bold green]",
            box=box.ROUNDED
        ))
        
        # Create results table
        results_table = Table(title="Update Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("States Updated", f"{final_status['states']['count']:,}")
        results_table.add_row("Counties Updated", f"{final_status['counties']['count']:,}")
        results_table.add_row("Cities Updated", f"{final_status['cities']['count']:,}")
        results_table.add_row("Total Records", f"{final_status['states']['count'] + final_status['counties']['count'] + final_status['cities']['count']:,}")
        results_table.add_row("Duration", str(duration).split('.')[0])
        
        self.console.print(results_table)
        
        self.console.print(f"\n[green]🎉 Successfully updated Kentucky region data![/green]")
        self.console.print(f"[blue]States:[/blue] Kentucky + {len(state_names)-1} bordering states")
