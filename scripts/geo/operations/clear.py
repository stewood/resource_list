"""
Clear Operations for Geographic Data Management

This module contains all clear-related operations extracted from geo_manager.py.

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


class ClearOperations:
    """Operations for clearing geographic data."""
    
    def __init__(self, console: Console, logger: logging.Logger):
        """Initialize clear operations.
        
        Args:
            console: Rich console for output
            logger: Logger instance
        """
        self.console = console
        self.logger = logger
    
    def clear_data(self, confirm: bool = False):
        """Clear all geographic data.
        
        Args:
            confirm: Whether to require user confirmation
        """
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
    
    def clear_states_only(self, confirm: bool = False):
        """Clear only state data.
        
        Args:
            confirm: Whether to require user confirmation
        """
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL state data![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Clearing state data...", total=None)
            
            try:
                # Get count before deletion
                states_count = CoverageArea.objects.filter(kind='STATE').count()
                
                # Delete state data
                CoverageArea.objects.filter(kind='STATE').delete()
                
                progress.update(task, description="✅ State data cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared:[/green]")
                self.console.print(f"  • {states_count:,} states")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing state data: {str(e)}[/red]")
                self.logger.error(f"Error clearing state data: {str(e)}")
    
    def clear_counties_only(self, confirm: bool = False):
        """Clear only county data.
        
        Args:
            confirm: Whether to require user confirmation
        """
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL county data![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Clearing county data...", total=None)
            
            try:
                # Get count before deletion
                counties_count = CoverageArea.objects.filter(kind='COUNTY').count()
                
                # Delete county data
                CoverageArea.objects.filter(kind='COUNTY').delete()
                
                progress.update(task, description="✅ County data cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared:[/green]")
                self.console.print(f"  • {counties_count:,} counties")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing county data: {str(e)}[/red]")
                self.logger.error(f"Error clearing county data: {str(e)}")
    
    def clear_cities_only(self, confirm: bool = False):
        """Clear only city data.
        
        Args:
            confirm: Whether to require user confirmation
        """
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL city data![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Clearing city data...", total=None)
            
            try:
                # Get count before deletion
                cities_count = CoverageArea.objects.filter(kind='CITY').count()
                
                # Delete city data
                CoverageArea.objects.filter(kind='CITY').delete()
                
                progress.update(task, description="✅ City data cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared:[/green]")
                self.console.print(f"  • {cities_count:,} cities")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing city data: {str(e)}[/red]")
                self.logger.error(f"Error clearing city data: {str(e)}")
    
    def clear_by_state(self, state_fips: str, confirm: bool = False):
        """Clear data for a specific state.
        
        Args:
            state_fips: FIPS code of the state to clear
            confirm: Whether to require user confirmation
        """
        if confirm:
            self.console.print(f"\n[red]⚠️  This will delete ALL data for state {state_fips}![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Clearing data for state {state_fips}...", total=None)
            
            try:
                # Get counts before deletion
                states_count = CoverageArea.objects.filter(kind='STATE', ext_ids__state_fips=state_fips).count()
                counties_count = CoverageArea.objects.filter(kind='COUNTY', ext_ids__state_fips=state_fips).count()
                cities_count = CoverageArea.objects.filter(kind='CITY', ext_ids__state_fips=state_fips).count()
                
                # Delete data for the state
                CoverageArea.objects.filter(ext_ids__state_fips=state_fips).delete()
                
                progress.update(task, description="✅ State data cleared successfully")
                
                self.console.print(f"\n[green]Successfully cleared data for state {state_fips}:[/green]")
                self.console.print(f"  • {states_count:,} states")
                self.console.print(f"  • {counties_count:,} counties")
                self.console.print(f"  • {cities_count:,} cities")
                self.console.print(f"  • Total: {states_count + counties_count + cities_count:,} records")
                
            except Exception as e:
                self.console.print(f"\n[red]Error clearing data for state {state_fips}: {str(e)}[/red]")
                self.logger.error(f"Error clearing data for state {state_fips}: {str(e)}")
