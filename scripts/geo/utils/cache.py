"""
Cache Utilities for Geographic Data Management

This module contains all cache-related utilities extracted from geo_manager.py.

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

# Rich imports for beautiful UI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm
from rich.align import Align
from rich import box


class CacheUtilities:
    """Utilities for managing TIGER/Line file cache."""
    
    def __init__(self, console: Console, logger: logging.Logger, cache):
        """Initialize cache utilities.
        
        Args:
            console: Rich console for output
            logger: Logger instance
            cache: Cache instance for file operations
        """
        self.console = console
        self.logger = logger
        self.cache = cache
    
    def clear_cache(self, confirm: bool = False):
        """Clear all cached files.
        
        Args:
            confirm: Whether to require user confirmation
        """
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
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information.
        
        Returns:
            Dictionary with cache information
        """
        try:
            cache_info = self.cache.get_cache_info()
            return cache_info
        except Exception as e:
            self.logger.error(f"Error getting cache info: {str(e)}")
            return {
                'cache_dir': 'Unknown',
                'max_age_days': 30,
                'cached_files': []
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_info = self.cache.get_cache_info()
            cached_files = cache_info['cached_files']
            
            total_files = len(cached_files)
            total_size = sum(f['file_size'] for f in cached_files)
            expired_files = [f for f in cached_files if f['is_expired']]
            valid_files = [f for f in cached_files if not f['is_expired']]
            
            # Group by file type
            file_types = {}
            for file_info in cached_files:
                file_type = file_info['file_type']
                if file_type not in file_types:
                    file_types[file_type] = {
                        'count': 0,
                        'size': 0,
                        'expired': 0
                    }
                file_types[file_type]['count'] += 1
                file_types[file_type]['size'] += file_info['file_size']
                if file_info['is_expired']:
                    file_types[file_type]['expired'] += 1
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'expired_files': len(expired_files),
                'valid_files': len(valid_files),
                'file_types': file_types,
                'cache_dir': cache_info['cache_dir'],
                'max_age_days': cache_info['max_age_days']
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'total_files': 0,
                'total_size': 0,
                'expired_files': 0,
                'valid_files': 0,
                'file_types': {},
                'cache_dir': 'Unknown',
                'max_age_days': 30
            }
    
    def show_cache_stats(self):
        """Display cache statistics with beautiful formatting."""
        stats = self.get_cache_stats()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Cache Statistics[/bold blue]",
            box=box.ROUNDED
        ))
        
        # Show basic stats
        self.console.print(f"[blue]Cache Directory:[/blue] {stats['cache_dir']}")
        self.console.print(f"[blue]Max Age:[/blue] {stats['max_age_days']} days")
        
        # Create stats table
        stats_table = Table(title="Cache Overview", box=box.ROUNDED)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")
        
        stats_table.add_row("Total Files", f"{stats['total_files']:,}")
        stats_table.add_row("Total Size", f"{stats['total_size']:,} bytes ({stats['total_size'] / 1024 / 1024:.1f} MB)")
        stats_table.add_row("Valid Files", f"{stats['valid_files']:,}")
        stats_table.add_row("Expired Files", f"{stats['expired_files']:,}")
        
        self.console.print(stats_table)
        
        # Show file type breakdown
        if stats['file_types']:
            self.console.print("\n[blue]📁 File Type Breakdown:[/blue]")
            type_table = Table(title="Files by Type", box=box.ROUNDED)
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="green", justify="right")
            type_table.add_column("Size", style="yellow", justify="right")
            type_table.add_column("Expired", style="red", justify="right")
            
            for file_type, type_stats in stats['file_types'].items():
                type_table.add_row(
                    file_type,
                    f"{type_stats['count']:,}",
                    f"{type_stats['size']:,} bytes",
                    f"{type_stats['expired']:,}"
                )
            
            self.console.print(type_table)
        
        # Show recommendations
        if stats['expired_files'] > 0:
            self.console.print(f"\n[yellow]💡 Found {stats['expired_files']} expired files. Run 'cache-cleanup' to remove them.[/yellow]")
        elif stats['total_files'] == 0:
            self.console.print(f"\n[blue]💡 No cached files found. Files will be cached automatically on first download.[/blue]")
        else:
            self.console.print(f"\n[green]✅ Cache is in good condition with {stats['valid_files']} valid files.[/green]")
    
    def validate_cache_integrity(self) -> Dict[str, Any]:
        """Validate cache integrity and report issues.
        
        Returns:
            Dictionary with validation results
        """
        try:
            cache_info = self.cache.get_cache_info()
            cached_files = cache_info['cached_files']
            
            issues = []
            valid_files = 0
            
            for file_info in cached_files:
                file_path = Path(cache_info['cache_dir']) / file_info['filename']
                
                # Check if file exists
                if not file_path.exists():
                    issues.append(f"Missing file: {file_info['filename']}")
                    continue
                
                # Check file size
                actual_size = file_path.stat().st_size
                if actual_size != file_info['file_size']:
                    issues.append(f"Size mismatch for {file_info['filename']}: expected {file_info['file_size']}, got {actual_size}")
                    continue
                
                # Check if file is readable
                try:
                    with open(file_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB to test
                except Exception as e:
                    issues.append(f"Unreadable file {file_info['filename']}: {str(e)}")
                    continue
                
                valid_files += 1
            
            return {
                'total_files': len(cached_files),
                'valid_files': valid_files,
                'issues': issues,
                'integrity_score': (valid_files / len(cached_files) * 100) if cached_files else 100
            }
            
        except Exception as e:
            self.logger.error(f"Error validating cache integrity: {str(e)}")
            return {
                'total_files': 0,
                'valid_files': 0,
                'issues': [f"Validation error: {str(e)}"],
                'integrity_score': 0
            }
    
    def show_cache_integrity_report(self):
        """Display cache integrity report."""
        validation = self.validate_cache_integrity()
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Cache Integrity Report[/bold blue]",
            box=box.ROUNDED
        ))
        
        # Create integrity table
        integrity_table = Table(title="Integrity Check Results", box=box.ROUNDED)
        integrity_table.add_column("Metric", style="cyan")
        integrity_table.add_column("Value", style="green", justify="right")
        
        integrity_table.add_row("Total Files", f"{validation['total_files']:,}")
        integrity_table.add_row("Valid Files", f"{validation['valid_files']:,}")
        integrity_table.add_row("Issues Found", f"{len(validation['issues']):,}")
        integrity_table.add_row("Integrity Score", f"{validation['integrity_score']:.1f}%")
        
        self.console.print(integrity_table)
        
        # Show issues if any
        if validation['issues']:
            self.console.print(f"\n[red]⚠️  Issues Found:[/red]")
            for issue in validation['issues']:
                self.console.print(f"  • {issue}")
            
            self.console.print(f"\n[yellow]💡 Consider running 'cache-clear' to rebuild the cache.[/yellow]")
        else:
            self.console.print(f"\n[green]✅ Cache integrity check passed! All files are valid.[/green]")
    
    def get_cache_recommendations(self) -> List[str]:
        """Get recommendations for cache management.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        stats = self.get_cache_stats()
        validation = self.validate_cache_integrity()
        
        # Check for expired files
        if stats['expired_files'] > 0:
            recommendations.append(f"Run cache cleanup to remove {stats['expired_files']} expired files")
        
        # Check for integrity issues
        if validation['issues']:
            recommendations.append("Run cache integrity check and consider clearing cache")
        
        # Check cache size
        if stats['total_size'] > 1024 * 1024 * 100:  # 100MB
            recommendations.append("Cache size is large, consider cleanup of old files")
        
        # Check for empty cache
        if stats['total_files'] == 0:
            recommendations.append("Cache is empty, files will be downloaded on first use")
        
        return recommendations
    
    def show_cache_recommendations(self):
        """Display cache management recommendations."""
        recommendations = self.get_cache_recommendations()
        
        if not recommendations:
            self.console.print("\n[green]✅ Cache is in optimal condition. No recommendations.[/green]")
            return
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold blue]Cache Management Recommendations[/bold blue]",
            box=box.ROUNDED
        ))
        
        for i, recommendation in enumerate(recommendations, 1):
            self.console.print(f"{i}. {recommendation}")
        
        self.console.print(f"\n[blue]💡 Use the appropriate cache commands to address these recommendations.[/blue]")
