"""
Validation Utilities for Geographic Data Management

This module contains all validation and utility functions extracted from geo_manager.py.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

import os
import sys
import logging
import urllib.request
from typing import List, Dict, Any, Optional, Tuple
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


class ValidationUtilities:
    """Utilities for validation and common operations."""
    
    def __init__(self, console: Console, logger: logging.Logger, state_mapping: Dict[str, str]):
        """Initialize validation utilities.
        
        Args:
            console: Rich console for output
            logger: Logger instance
            state_mapping: State abbreviation to FIPS code mapping
        """
        self.console = console
        self.logger = logger
        self.state_mapping = state_mapping
    
    def parse_states(self, states_input: str) -> List[str]:
        """Parse state input (e.g., 'KY,IN' or '21,18') into FIPS codes.
        
        Args:
            states_input: Comma-separated state codes
            
        Returns:
            List of FIPS codes
        """
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
    
    def validate_state_codes(self, state_codes: List[str]) -> Tuple[List[str], List[str]]:
        """Validate state codes and return valid and invalid ones.
        
        Args:
            state_codes: List of state codes to validate
            
        Returns:
            Tuple of (valid_codes, invalid_codes)
        """
        valid_codes = []
        invalid_codes = []
        
        for code in state_codes:
            if code in self.state_mapping or code in self.state_mapping.values():
                valid_codes.append(code)
            else:
                invalid_codes.append(code)
        
        return valid_codes, invalid_codes
    
    def get_state_name(self, state_fips: str) -> str:
        """Get state name from FIPS code.
        
        Args:
            state_fips: FIPS code of the state
            
        Returns:
            State name or FIPS code if not found
        """
        # Convert FIPS to state name if possible
        state_names = {v: k for k, v in self.state_mapping.items()}
        return state_names.get(state_fips, state_fips)
    
    def get_latest_tiger_year(self) -> int:
        """Auto-detect the latest available TIGER/Line year.
        
        Returns:
            Latest TIGER/Line year
        """
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
    
    def validate_tiger_year(self, year: int) -> bool:
        """Validate if a TIGER/Line year is available.
        
        Args:
            year: Year to validate
            
        Returns:
            True if year is available, False otherwise
        """
        try:
            # Test if the states file exists for the given year
            url = f"https://www2.census.gov/geo/tiger/TIGER{year}/STATE/tl_{year}_us_state.zip"
            response = urllib.request.urlopen(url, timeout=5)
            return response.getcode() == 200
        except:
            return False
    
    def get_available_tiger_years(self) -> List[int]:
        """Get list of available TIGER/Line years.
        
        Returns:
            List of available years
        """
        current_year = datetime.now().year
        available_years = []
        
        # Check the last 10 years
        for year in range(current_year, current_year - 10, -1):
            if self.validate_tiger_year(year):
                available_years.append(year)
        
        return available_years
    
    def validate_coverage_area_data(self) -> Dict[str, Any]:
        """Validate coverage area data integrity.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'total_records': 0,
            'states_count': 0,
            'counties_count': 0,
            'cities_count': 0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Count records by type
            states = CoverageArea.objects.filter(kind='STATE')
            counties = CoverageArea.objects.filter(kind='COUNTY')
            cities = CoverageArea.objects.filter(kind='CITY')
            
            validation_results['states_count'] = states.count()
            validation_results['counties_count'] = counties.count()
            validation_results['cities_count'] = cities.count()
            validation_results['total_records'] = validation_results['states_count'] + validation_results['counties_count'] + validation_results['cities_count']
            
            # Check for common issues
            if validation_results['states_count'] == 0:
                validation_results['issues'].append("No state records found")
            
            if validation_results['counties_count'] == 0:
                validation_results['warnings'].append("No county records found")
            
            if validation_results['cities_count'] == 0:
                validation_results['warnings'].append("No city records found")
            
            # Check for records without geometry
            states_without_geom = states.filter(geometry__isnull=True).count()
            counties_without_geom = counties.filter(geometry__isnull=True).count()
            cities_without_geom = cities.filter(geometry__isnull=True).count()
            
            if states_without_geom > 0:
                validation_results['issues'].append(f"{states_without_geom} state records without geometry")
            
            if counties_without_geom > 0:
                validation_results['warnings'].append(f"{counties_without_geom} county records without geometry")
            
            if cities_without_geom > 0:
                validation_results['warnings'].append(f"{cities_without_geom} city records without geometry")
            
            # Check for records without names
            states_without_name = states.filter(name__isnull=True).count()
            counties_without_name = counties.filter(name__isnull=True).count()
            cities_without_name = cities.filter(name__isnull=True).count()
            
            if states_without_name > 0:
                validation_results['issues'].append(f"{states_without_name} state records without names")
            
            if counties_without_name > 0:
                validation_results['warnings'].append(f"{counties_without_name} county records without names")
            
            if cities_without_name > 0:
                validation_results['warnings'].append(f"{cities_without_name} city records without names")
            
        except Exception as e:
            validation_results['issues'].append(f"Error during validation: {str(e)}")
            self.logger.error(f"Error validating coverage area data: {str(e)}")
        
        return validation_results
    
    def show_validation_report(self):
        """Display validation report with beautiful formatting."""
        validation = self.validate_coverage_area_data()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Coverage Area Data Validation Report[/bold blue]",
            box=box.ROUNDED
        ))
        
        # Create validation table
        validation_table = Table(title="Data Validation Results", box=box.ROUNDED)
        validation_table.add_column("Metric", style="cyan")
        validation_table.add_column("Value", style="green", justify="right")
        
        validation_table.add_row("Total Records", f"{validation['total_records']:,}")
        validation_table.add_row("States", f"{validation['states_count']:,}")
        validation_table.add_row("Counties", f"{validation['counties_count']:,}")
        validation_table.add_row("Cities", f"{validation['cities_count']:,}")
        validation_table.add_row("Issues Found", f"{len(validation['issues']):,}")
        validation_table.add_row("Warnings", f"{len(validation['warnings']):,}")
        
        self.console.print(validation_table)
        
        # Show issues if any
        if validation['issues']:
            self.console.print(f"\n[red]⚠️  Issues Found:[/red]")
            for issue in validation['issues']:
                self.console.print(f"  • {issue}")
        
        # Show warnings if any
        if validation['warnings']:
            self.console.print(f"\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in validation['warnings']:
                self.console.print(f"  • {warning}")
        
        # Show summary
        if not validation['issues'] and not validation['warnings']:
            self.console.print(f"\n[green]✅ Data validation passed! All records are valid.[/green]")
        elif not validation['issues']:
            self.console.print(f"\n[green]✅ Data validation passed with {len(validation['warnings'])} warnings.[/green]")
        else:
            self.console.print(f"\n[red]❌ Data validation failed with {len(validation['issues'])} issues.[/red]")
    
    def validate_state_coverage(self, state_fips: str) -> Dict[str, Any]:
        """Validate coverage for a specific state.
        
        Args:
            state_fips: FIPS code of the state to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'state_fips': state_fips,
            'state_name': self.get_state_name(state_fips),
            'state_record': None,
            'counties_count': 0,
            'cities_count': 0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check state record
            state_record = CoverageArea.objects.filter(kind='STATE', ext_ids__state_fips=state_fips).first()
            if state_record:
                validation_results['state_record'] = state_record
            else:
                validation_results['issues'].append(f"State record not found for {state_fips}")
            
            # Count counties and cities
            counties = CoverageArea.objects.filter(kind='COUNTY', ext_ids__state_fips=state_fips)
            cities = CoverageArea.objects.filter(kind='CITY', ext_ids__state_fips=state_fips)
            
            validation_results['counties_count'] = counties.count()
            validation_results['cities_count'] = cities.count()
            
            # Check for common issues
            if validation_results['counties_count'] == 0:
                validation_results['warnings'].append("No county records found")
            
            if validation_results['cities_count'] == 0:
                validation_results['warnings'].append("No city records found")
            
            # Check for records without geometry
            counties_without_geom = counties.filter(geometry__isnull=True).count()
            cities_without_geom = cities.filter(geometry__isnull=True).count()
            
            if counties_without_geom > 0:
                validation_results['warnings'].append(f"{counties_without_geom} county records without geometry")
            
            if cities_without_geom > 0:
                validation_results['warnings'].append(f"{cities_without_geom} city records without geometry")
            
        except Exception as e:
            validation_results['issues'].append(f"Error during validation: {str(e)}")
            self.logger.error(f"Error validating state coverage for {state_fips}: {str(e)}")
        
        return validation_results
    
    def show_state_validation_report(self, state_fips: str):
        """Display validation report for a specific state."""
        validation = self.validate_state_coverage(state_fips)
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold blue]State Validation Report: {validation['state_name']} ({state_fips})[/bold blue]",
            box=box.ROUNDED
        ))
        
        # Create validation table
        validation_table = Table(title="State Coverage Validation", box=box.ROUNDED)
        validation_table.add_column("Metric", style="cyan")
        validation_table.add_column("Value", style="green", justify="right")
        
        validation_table.add_row("State Record", "✅ Found" if validation['state_record'] else "❌ Missing")
        validation_table.add_row("Counties", f"{validation['counties_count']:,}")
        validation_table.add_row("Cities", f"{validation['cities_count']:,}")
        validation_table.add_row("Issues", f"{len(validation['issues']):,}")
        validation_table.add_row("Warnings", f"{len(validation['warnings']):,}")
        
        self.console.print(validation_table)
        
        # Show issues if any
        if validation['issues']:
            self.console.print(f"\n[red]⚠️  Issues Found:[/red]")
            for issue in validation['issues']:
                self.console.print(f"  • {issue}")
        
        # Show warnings if any
        if validation['warnings']:
            self.console.print(f"\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in validation['warnings']:
                self.console.print(f"  • {warning}")
        
        # Show summary
        if not validation['issues'] and not validation['warnings']:
            self.console.print(f"\n[green]✅ State validation passed! All records are valid.[/green]")
        elif not validation['issues']:
            self.console.print(f"\n[green]✅ State validation passed with {len(validation['warnings'])} warnings.[/green]")
        else:
            self.console.print(f"\n[red]❌ State validation failed with {len(validation['issues'])} issues.[/red]")
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics for geographic data.
        
        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            'total_records': 0,
            'records_with_geometry': 0,
            'records_with_names': 0,
            'records_with_ext_ids': 0,
            'geometry_quality': 0.0,
            'name_quality': 0.0,
            'ext_id_quality': 0.0,
            'overall_quality': 0.0
        }
        
        try:
            # Get all coverage areas
            all_records = CoverageArea.objects.all()
            total_records = all_records.count()
            
            if total_records == 0:
                return metrics
            
            metrics['total_records'] = total_records
            
            # Count records with geometry
            records_with_geom = all_records.filter(geometry__isnull=False).count()
            metrics['records_with_geometry'] = records_with_geom
            metrics['geometry_quality'] = (records_with_geom / total_records) * 100
            
            # Count records with names
            records_with_names = all_records.filter(name__isnull=False).exclude(name='').count()
            metrics['records_with_names'] = records_with_names
            metrics['name_quality'] = (records_with_names / total_records) * 100
            
            # Count records with ext_ids
            records_with_ext_ids = all_records.filter(ext_ids__isnull=False).exclude(ext_ids={}).count()
            metrics['records_with_ext_ids'] = records_with_ext_ids
            metrics['ext_id_quality'] = (records_with_ext_ids / total_records) * 100
            
            # Calculate overall quality
            metrics['overall_quality'] = (metrics['geometry_quality'] + metrics['name_quality'] + metrics['ext_id_quality']) / 3
            
        except Exception as e:
            self.logger.error(f"Error calculating data quality metrics: {str(e)}")
        
        return metrics
    
    def show_data_quality_report(self):
        """Display data quality report."""
        metrics = self.get_data_quality_metrics()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Data Quality Report[/bold blue]",
            box=box.ROUNDED
        ))
        
        # Create quality table
        quality_table = Table(title="Data Quality Metrics", box=box.ROUNDED)
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("Value", style="green", justify="right")
        quality_table.add_column("Quality", style="yellow", justify="right")
        
        quality_table.add_row("Total Records", f"{metrics['total_records']:,}", "")
        quality_table.add_row("With Geometry", f"{metrics['records_with_geometry']:,}", f"{metrics['geometry_quality']:.1f}%")
        quality_table.add_row("With Names", f"{metrics['records_with_names']:,}", f"{metrics['name_quality']:.1f}%")
        quality_table.add_row("With External IDs", f"{metrics['records_with_ext_ids']:,}", f"{metrics['ext_id_quality']:.1f}%")
        quality_table.add_row("Overall Quality", "", f"{metrics['overall_quality']:.1f}%")
        
        self.console.print(quality_table)
        
        # Show quality assessment
        if metrics['overall_quality'] >= 90:
            self.console.print(f"\n[green]✅ Excellent data quality! ({metrics['overall_quality']:.1f}%)[/green]")
        elif metrics['overall_quality'] >= 75:
            self.console.print(f"\n[blue]✅ Good data quality! ({metrics['overall_quality']:.1f}%)[/blue]")
        elif metrics['overall_quality'] >= 50:
            self.console.print(f"\n[yellow]⚠️  Fair data quality. ({metrics['overall_quality']:.1f}%)[/yellow]")
        else:
            self.console.print(f"\n[red]❌ Poor data quality. ({metrics['overall_quality']:.1f}%)[/red]")
