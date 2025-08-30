#!/usr/bin/env python3
"""
TIGER/Line Cache Manager

A standalone script for managing cached TIGER/Line GIS data files.

Features:
- View cache status and information
- Clear all cached files
- Clean up expired files
- Download specific files to cache
- Validate cached files

Usage:
    python scripts/cache_manager.py status
    python scripts/cache_manager.py clear
    python scripts/cache_manager.py cleanup
    python scripts/cache_manager.py download STATE 2023
    python scripts/cache_manager.py validate

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')

import django
django.setup()

from directory.utils.tiger_cache import TigerFileCache
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import box
from datetime import datetime


class CacheManager:
    """Standalone cache management utility."""
    
    def __init__(self):
        """Initialize the cache manager."""
        self.console = Console()
        self.cache = TigerFileCache()
    
    def show_status(self):
        """Display detailed cache status."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]TIGER/Line Cache Manager[/bold blue]",
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
        cache_table.add_column("State", style="magenta", justify="center")
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
            
            # Get state display
            state_display = file_info.get('state_fips', 'N/A')
            
            # Status
            status = "✅ Valid" if not file_info['is_expired'] else "⚠️ Expired"
            
            cache_table.add_row(
                file_info['file_type'],
                str(file_info['year']),
                state_display,
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
            self.console.print(f"\n[yellow]💡 Run 'cleanup' to remove expired files.[/yellow]")
    
    def clear_cache(self, confirm: bool = True):
        """Clear all cached files."""
        if confirm:
            self.console.print("\n[red]⚠️  This will delete ALL cached TIGER/Line files![/red]")
            if not Confirm.ask("Are you sure you want to continue?"):
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
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
    
    def cleanup_expired(self):
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
    
    def download_file(self, file_type: str, year: int, state_fips: str = None):
        """Download a specific file to cache."""
        valid_types = ['STATE', 'COUNTY', 'CITY']
        
        if file_type not in valid_types:
            self.console.print(f"[red]Invalid file type: {file_type}[/red]")
            self.console.print(f"[blue]Valid types: {', '.join(valid_types)}[/blue]")
            return
        
        # For CITY files, state_fips is required
        if file_type == 'CITY' and not state_fips:
            self.console.print(f"[red]State FIPS code required for CITY files[/red]")
            self.console.print(f"[blue]Example: python scripts/cache_manager.py download CITY 2022 21[/blue]")
            return
        
        if state_fips:
            self.console.print(f"\n[blue]Downloading {file_type} data for year {year}, state {state_fips}...[/blue]")
        else:
            self.console.print(f"\n[blue]Downloading {file_type} data for year {year}...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Downloading...", total=None)
            
            try:
                # Download with progress callback
                def progress_callback(downloaded, total, filename):
                    if total > 0:
                        progress.update(task, description=f"Downloading {filename} ({downloaded:,}/{total:,} bytes)")
                
                file_path = self.cache.get_file(file_type, year, progress_callback, state_fips)
                
                progress.update(task, description="✅ Download completed")
                
                file_size = file_path.stat().st_size
                if state_fips:
                    self.console.print(f"\n[green]Successfully downloaded {file_type} data for year {year}, state {state_fips}:[/green]")
                else:
                    self.console.print(f"\n[green]Successfully downloaded {file_type} data for year {year}:[/green]")
                self.console.print(f"  • File: {file_path}")
                self.console.print(f"  • Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
                
            except Exception as e:
                if state_fips:
                    self.console.print(f"\n[red]Error downloading {file_type} data for year {year}, state {state_fips}: {str(e)}[/red]")
                else:
                    self.console.print(f"\n[red]Error downloading {file_type} data: {str(e)}[/red]")
    
    def validate_cache(self):
        """Validate all cached files."""
        cache_info = self.cache.get_cache_info()
        
        if not cache_info['cached_files']:
            self.console.print("\n[yellow]No cached files to validate.[/yellow]")
            return
        
        self.console.print(f"\n[blue]Validating {len(cache_info['cached_files'])} cached files...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Validating files...", total=len(cache_info['cached_files']))
            
            valid_count = 0
            invalid_count = 0
            
            for file_info in cache_info['cached_files']:
                progress.update(task, description=f"Validating {file_info['file_type']}_{file_info['year']}...")
                
                try:
                    # Check if file exists and is valid
                    state_fips = file_info.get('state_fips')
                    cache_path = self.cache.get_cache_path(file_info['file_type'], file_info['year'], state_fips)
                    
                    if not cache_path.exists():
                        self.console.print(f"\n[red]❌ {file_info['file_type']}_{file_info['year']}: File missing[/red]")
                        invalid_count += 1
                    elif not self.cache._validate_downloaded_file(cache_path, file_info['file_type'], file_info['year']):
                        self.console.print(f"\n[red]❌ {file_info['file_type']}_{file_info['year']}: Invalid file[/red]")
                        invalid_count += 1
                    else:
                        valid_count += 1
                    
                    progress.advance(task)
                    
                except Exception as e:
                    self.console.print(f"\n[red]❌ {file_info['file_type']}_{file_info['year']}: Error - {str(e)}[/red]")
                    invalid_count += 1
                    progress.advance(task)
            
            progress.update(task, description="✅ Validation completed")
            
            self.console.print(f"\n[blue]Validation Results:[/blue]")
            self.console.print(f"  • Valid files: {valid_count}")
            self.console.print(f"  • Invalid files: {invalid_count}")
            
            if invalid_count == 0:
                self.console.print(f"\n[green]✅ All cached files are valid![/green]")
            else:
                self.console.print(f"\n[yellow]⚠️ {invalid_count} files have issues. Consider clearing cache.[/yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TIGER/Line Cache Manager - Manage cached GIS data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cache_manager.py status
  python scripts/cache_manager.py clear
  python scripts/cache_manager.py cleanup
  python scripts/cache_manager.py download STATE 2023
  python scripts/cache_manager.py validate
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'clear', 'cleanup', 'download', 'validate'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'file_type',
        nargs='?',
        choices=['STATE', 'COUNTY', 'CITY'],
        help='File type for download command'
    )
    
    parser.add_argument(
        'year',
        nargs='?',
        type=int,
        help='Year for download command'
    )
    
    parser.add_argument(
        'state_fips',
        nargs='?',
        type=str,
        help='State FIPS code for download command (required for CITY files)'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = CacheManager()
    
    try:
        if args.command == 'status':
            manager.show_status()
        
        elif args.command == 'clear':
            manager.clear_cache(confirm=not args.no_confirm)
        
        elif args.command == 'cleanup':
            manager.cleanup_expired()
        
        elif args.command == 'download':
            if not args.file_type or not args.year:
                manager.console.print("[red]Download command requires file_type and year arguments[/red]")
                return
            manager.download_file(args.file_type, args.year, args.state_fips)
        
        elif args.command == 'validate':
            manager.validate_cache()
    
    except KeyboardInterrupt:
        manager.console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        manager.console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
