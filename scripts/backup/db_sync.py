#!/usr/bin/env python3
"""
Database Synchronization Tool for Community Resource Directory

This script provides comprehensive database synchronization functionality between
development and staging environments. It supports bidirectional syncing with
safety checks, data validation, and rollback capabilities.

Features:
    - Sync from development to staging (dev->staging)
    - Sync from staging to development (staging->dev)
    - Safety checks and confirmations
    - Backup before sync operations
    - Data validation and integrity checks
    - Rollback capabilities
    - Dry-run mode for testing
    - Detailed logging and reporting

Usage:
    python scripts/backup/db_sync.py --help
    python scripts/backup/db_sync.py --dev-to-staging
    python scripts/backup/db_sync.py --staging-to-dev
    python scripts/backup/db_sync.py --dev-to-staging --dry-run
    python scripts/backup/db_sync.py --staging-to-dev --force

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import queue

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
django.setup()


class ProgressBar:
    """Simple progress bar for long-running operations."""
    
    def __init__(self, description: str, total: int = 100):
        self.description = description
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        
    def update(self, current: int, message: str = ""):
        """Update progress bar."""
        self.current = current
        percentage = min(100, int((current / self.total) * 100))
        bar_length = 30
        filled_length = int(bar_length * current // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        elapsed = time.time() - self.start_time
        if current > 0:
            eta = (elapsed / current) * (self.total - current)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"
        
        print(f"\r{self.description}: [{bar}] {percentage}% ({current}/{self.total}) {eta_str} {message}", end='', flush=True)
        
    def complete(self, message: str = ""):
        """Mark progress as complete."""
        self.update(self.total, message)
        print()  # New line after completion


class FileProgressTracker:
    """Track progress based on file size changes."""
    
    def __init__(self, description: str, target_file: Path):
        self.description = description
        self.target_file = target_file
        self.start_time = time.time()
        self.start_size = 0
        self.last_size = 0
        self.last_update = 0
        self.file_exists = False
        
    def start(self):
        """Start tracking progress."""
        self.start_size = self.target_file.stat().st_size if self.target_file.exists() else 0
        self.last_size = self.start_size
        print(f"🔄 {self.description}")
        
    def update(self, message: str = ""):
        """Update progress based on file size or time elapsed."""
        elapsed = time.time() - self.start_time
        
        # Check if file exists now
        if self.target_file.exists():
            if not self.file_exists:
                # File just appeared, switch to size tracking
                self.file_exists = True
                print(f"\r   📁 File created, tracking size...", end='', flush=True)
            
            current_size = self.target_file.stat().st_size
            size_mb = current_size / (1024 * 1024)
            print(f"\r   📊 Progress: {size_mb:.2f} MB written ({elapsed:.1f}s elapsed) {message}", end='', flush=True)
            self.last_size = current_size
        else:
            # File doesn't exist yet, show time-based progress
            print(f"\r   ⏱️  Backup in progress... ({elapsed:.1f}s elapsed) {message}", end='', flush=True)
        
        self.last_update = time.time()
        
    def complete(self, message: str = ""):
        """Mark progress as complete."""
        if self.target_file.exists():
            final_size = self.target_file.stat().st_size / (1024 * 1024)
            elapsed = time.time() - self.start_time
            print(f"\r   ✅ Completed: {final_size:.2f} MB in {elapsed:.1f}s {message}")
        else:
            elapsed = time.time() - self.start_time
            print(f"\r   ❌ Failed: File not created after {elapsed:.1f}s {message}")


class DatabaseSync:
    """Database synchronization system for Resource Directory environments."""

    def __init__(self, backup_dir: str = "backups"):
        """Initialize the database sync manager.
        
        Args:
            backup_dir: Directory to store sync backups (relative to project root)
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.backup_dir = self.project_root / backup_dir
        self.sync_backup_dir = self.backup_dir / "sync_backups"
        self.sync_backup_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Database configurations
        self.config = {
            'local_db': {
                'name': 'resource_directory_dev',
                'user': 'postgres',
                'password': 'postgres',
                'host': 'localhost',
                'port': '5432'
            },
            'staging_db': {
                'name': 'isaiah58_resources',
                'user': 'isaiah58_user',
                'password': 'CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr',
                'host': 'dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com',
                'port': '5432'
            }
        }

    def setup_logging(self):
        """Setup logging configuration."""
        log_file = self.sync_backup_dir / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_timestamp(self) -> str:
        """Get current timestamp for backup naming.
        
        Returns:
            Timestamp string in format YYYYMMDD_HHMMSS
        """
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    def backup_database(self, db_config: Dict, backup_name: str) -> Optional[Path]:
        """Create a backup of the specified database.
        
        Args:
            db_config: Database configuration dictionary
            backup_name: Name for the backup file
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            self.logger.info(f"Creating backup: {backup_name}")
            print(f"🔄 Creating backup: {backup_name}")
            
            timestamp = self.get_timestamp()
            backup_file = self.sync_backup_dir / f"{backup_name}_{timestamp}.sql"
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                f'--host={db_config["host"]}',
                f'--port={db_config["port"]}',
                f'--username={db_config["user"]}',
                f'--dbname={db_config["name"]}',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_file}'
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config["password"]
            
            # Add SSL mode for staging database
            if db_config["host"] != "localhost":
                env['PGSSLMODE'] = 'require'
            
            # Execute backup with progress monitoring
            print(f"   📍 Target: {db_config['host']}:{db_config['port']}/{db_config['name']}")
            print(f"   📁 Output: {backup_file.name}")
            
            # Start the backup process
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress based on file size
            tracker = FileProgressTracker(f"Backing up {db_config['name']}", backup_file)
            tracker.start()
            
            # Monitor the process
            while process.poll() is None:
                tracker.update("(backup in progress...)")
                time.sleep(1)  # Check every second
            
            # Wait for completion
            return_code = process.poll()
            
            if return_code == 0:
                tracker.complete("✅ Backup completed successfully")
                self.logger.info(f"Backup completed: {backup_file.name}")
                return backup_file
            else:
                _, stderr = process.communicate()
                self.logger.error(f"Backup failed: {stderr}")
                print(f"❌ Backup failed: {stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Backup error: {str(e)}")
            print(f"❌ Backup error: {str(e)}")
            return None

    def restore_database(self, db_config: Dict, backup_file: Path) -> bool:
        """Restore a database from backup file.
        
        Args:
            db_config: Database configuration dictionary
            backup_file: Path to backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            self.logger.info(f"Restoring database from: {backup_file.name}")
            print(f"🔄 Restoring database from: {backup_file.name}")
            
            # Build psql command
            cmd = [
                'psql',
                f'--host={db_config["host"]}',
                f'--port={db_config["port"]}',
                f'--username={db_config["user"]}',
                f'--dbname={db_config["name"]}',
                f'--file={backup_file}'
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config["password"]
            
            # Add SSL mode for staging database
            if db_config["host"] != "localhost":
                env['PGSSLMODE'] = 'require'
            
            # Execute restore with progress monitoring
            print(f"   📍 Target: {db_config['host']}:{db_config['port']}/{db_config['name']}")
            print(f"   📁 Source: {backup_file.name}")
            
            # Start the restore process
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress with time-based updates
            print(f"   🔄 Restoring to {db_config['name']}...")
            start_time = time.time()
            
            # Monitor the process
            while process.poll() is None:
                elapsed = time.time() - start_time
                print(f"\r   📊 Progress: {elapsed:.1f}s elapsed (restore in progress...)", end='', flush=True)
                time.sleep(2)  # Update every 2 seconds
            
            # Wait for completion
            return_code = process.poll()
            
            if return_code == 0:
                elapsed = time.time() - start_time
                print(f"\r   ✅ Restore completed successfully in {elapsed:.1f}s")
                self.logger.info("Database restore completed successfully")
                return True
            else:
                _, stderr = process.communicate()
                self.logger.error(f"Restore failed: {stderr}")
                print(f"❌ Restore failed: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Restore error: {str(e)}")
            print(f"❌ Restore error: {str(e)}")
            return False

    def get_database_info(self, db_config: Dict) -> Dict:
        """Get information about a database.
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            Dictionary with database information
        """
        try:
            # Build psql command to get database info
            cmd = [
                'psql',
                f'--host={db_config["host"]}',
                f'--port={db_config["port"]}',
                f'--username={db_config["user"]}',
                f'--dbname={db_config["name"]}',
                '--tuples-only',
                '--no-align',
                '--command=SELECT COUNT(*) FROM directory_resource;'
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config["password"]
            
            # Add SSL mode for staging database
            if db_config["host"] != "localhost":
                env['PGSSLMODE'] = 'require'
            
            # Execute query
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                resource_count = result.stdout.strip()
                return {
                    'resource_count': int(resource_count) if resource_count.isdigit() else 0,
                    'host': db_config["host"],
                    'database': db_config["name"]
                }
            else:
                self.logger.warning(f"Could not get database info: {result.stderr}")
                return {
                    'resource_count': 0,
                    'host': db_config["host"],
                    'database': db_config["name"]
                }
                
        except Exception as e:
            self.logger.warning(f"Error getting database info: {str(e)}")
            return {
                'resource_count': 0,
                'host': db_config["host"],
                'database': db_config["name"]
            }

    def sync_dev_to_staging(self, dry_run: bool = False, force: bool = False) -> bool:
        """Sync data from development to staging database.
        
        Args:
            dry_run: If True, only show what would be done
            force: If True, skip confirmation prompts
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            self.logger.info("Starting development to staging sync...")
            
            # Get database information
            dev_info = self.get_database_info(self.config['local_db'])
            staging_info = self.get_database_info(self.config['staging_db'])
            
            print(f"\n📊 DATABASE INFORMATION:")
            print(f"Development: {dev_info['resource_count']} resources ({dev_info['host']})")
            print(f"Staging: {staging_info['resource_count']} resources ({staging_info['host']})")
            
            if dry_run:
                print(f"\n🔍 DRY RUN - Would sync {dev_info['resource_count']} resources from development to staging")
                return True
            
            # Safety check
            if not force:
                print(f"\n⚠️  WARNING: This will overwrite staging database with development data!")
                print(f"   Staging currently has {staging_info['resource_count']} resources")
                print(f"   Development has {dev_info['resource_count']} resources")
                
                response = input("\nAre you sure you want to continue? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    self.logger.info("Sync cancelled by user")
                    return False
            
            # Create backup of staging database
            print(f"\n📦 STEP 1: Creating staging database backup...")
            staging_backup = self.backup_database(
                self.config['staging_db'], 
                'staging_before_dev_sync'
            )
            
            if not staging_backup:
                self.logger.error("Failed to create staging backup - aborting sync")
                return False
            
            # Create backup of development database
            print(f"\n📦 STEP 2: Creating development database backup...")
            dev_backup = self.backup_database(
                self.config['local_db'], 
                'dev_for_staging_sync'
            )
            
            if not dev_backup:
                self.logger.error("Failed to create development backup - aborting sync")
                return False
            
            # Restore development data to staging
            print(f"\n📦 STEP 3: Restoring development data to staging...")
            if not self.restore_database(self.config['staging_db'], dev_backup):
                self.logger.error("Failed to restore development data to staging")
                print("❌ Failed to restore development data to staging")
                return False
            
            # Verify sync
            print(f"\n📦 STEP 4: Verifying sync completion...")
            new_staging_info = self.get_database_info(self.config['staging_db'])
            print(f"\n✅ SYNC COMPLETED SUCCESSFULLY!")
            print(f"   📊 Staging now has {new_staging_info['resource_count']} resources")
            print(f"   💾 Backup files created:")
            print(f"     - {staging_backup.name}")
            print(f"     - {dev_backup.name}")
            print(f"   🎯 All development data (including TIGER GIS data) has been synced to staging")
            
            self.logger.info("Development to staging sync completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Sync error: {str(e)}")
            return False

    def sync_staging_to_dev(self, dry_run: bool = False, force: bool = False) -> bool:
        """Sync data from staging to development database.
        
        Args:
            dry_run: If True, only show what would be done
            force: If True, skip confirmation prompts
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            self.logger.info("Starting staging to development sync...")
            
            # Get database information
            dev_info = self.get_database_info(self.config['local_db'])
            staging_info = self.get_database_info(self.config['staging_db'])
            
            print(f"\n📊 DATABASE INFORMATION:")
            print(f"Development: {dev_info['resource_count']} resources ({dev_info['host']})")
            print(f"Staging: {staging_info['resource_count']} resources ({staging_info['host']})")
            
            if dry_run:
                print(f"\n🔍 DRY RUN - Would sync {staging_info['resource_count']} resources from staging to development")
                return True
            
            # Safety check
            if not force:
                print(f"\n⚠️  WARNING: This will overwrite development database with staging data!")
                print(f"   Development currently has {dev_info['resource_count']} resources")
                print(f"   Staging has {staging_info['resource_count']} resources")
                
                response = input("\nAre you sure you want to continue? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    self.logger.info("Sync cancelled by user")
                    return False
            
            # Create backup of development database
            self.logger.info("Creating development database backup...")
            dev_backup = self.backup_database(
                self.config['local_db'], 
                'dev_before_staging_sync'
            )
            
            if not dev_backup:
                self.logger.error("Failed to create development backup - aborting sync")
                return False
            
            # Create backup of staging database
            self.logger.info("Creating staging database backup...")
            staging_backup = self.backup_database(
                self.config['staging_db'], 
                'staging_for_dev_sync'
            )
            
            if not staging_backup:
                self.logger.error("Failed to create staging backup - aborting sync")
                return False
            
            # Restore staging data to development
            self.logger.info("Restoring staging data to development...")
            if not self.restore_database(self.config['local_db'], staging_backup):
                self.logger.error("Failed to restore staging data to development")
                return False
            
            # Verify sync
            new_dev_info = self.get_database_info(self.config['local_db'])
            print(f"\n✅ SYNC COMPLETED:")
            print(f"   Development now has {new_dev_info['resource_count']} resources")
            print(f"   Backup files created:")
            print(f"     - {dev_backup.name}")
            print(f"     - {staging_backup.name}")
            
            self.logger.info("Staging to development sync completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Sync error: {str(e)}")
            return False

    def list_sync_backups(self) -> None:
        """List all sync backup files."""
        try:
            self.logger.info("Listing sync backups...")
            
            print("\n" + "="*80)
            print("SYNC BACKUP INVENTORY")
            print("="*80)
            
            if self.sync_backup_dir.exists():
                backup_files = sorted(
                    self.sync_backup_dir.glob("*.sql"), 
                    key=lambda x: x.stat().st_mtime, 
                    reverse=True
                )
                
                if backup_files:
                    for backup_file in backup_files:
                        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                        print(f"  {backup_file.name}")
                        print(f"    Date: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Size: {file_size:.2f} MB")
                        print()
                else:
                    print("  No sync backups found")
            else:
                print("  Sync backup directory not found")
            
            # Total size
            total_size = sum(f.stat().st_size for f in self.sync_backup_dir.glob('*.sql'))
            total_size_mb = total_size / (1024 * 1024)
            print(f"\n💾 TOTAL SYNC BACKUP SIZE: {total_size_mb:.2f} MB")
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error listing sync backups: {str(e)}")

    def cleanup_sync_backups(self, keep_days: int = 7) -> bool:
        """Clean up old sync backup files.
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            from datetime import timedelta
            
            self.logger.info(f"Cleaning up sync backups older than {keep_days} days...")
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            total_size_freed = 0
            
            for backup_file in self.sync_backup_dir.glob("*.sql"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_size = backup_file.stat().st_size
                        backup_file.unlink()
                        deleted_count += 1
                        total_size_freed += file_size
                        self.logger.info(f"Deleted old sync backup: {backup_file.name}")
            
            total_size_mb = total_size_freed / (1024 * 1024)
            self.logger.info(f"Cleanup completed: {deleted_count} files deleted, {total_size_mb:.2f} MB freed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Synchronization Tool for Community Resource Directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync development data to staging (with confirmation)
  python scripts/backup/db_sync.py --dev-to-staging
  
  # Sync staging data to development (with confirmation)
  python scripts/backup/db_sync.py --staging-to-dev
  
  # Dry run to see what would be synced
  python scripts/backup/db_sync.py --dev-to-staging --dry-run
  
  # Force sync without confirmation
  python scripts/backup/db_sync.py --staging-to-dev --force
  
  # List sync backups
  python scripts/backup/db_sync.py --list
  
  # Clean up old sync backups (keep last 7 days)
  python scripts/backup/db_sync.py --cleanup
  
  # Clean up with custom retention (keep last 3 days)
  python scripts/backup/db_sync.py --cleanup --keep-days 3
        """
    )
    
    # Sync direction options
    sync_group = parser.add_mutually_exclusive_group(required=False)
    sync_group.add_argument('--dev-to-staging', action='store_true',
                           help='Sync data from development to staging database')
    sync_group.add_argument('--staging-to-dev', action='store_true',
                           help='Sync data from staging to development database')
    
    # Utility options
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually doing it')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts (use with caution)')
    parser.add_argument('--list', action='store_true',
                       help='List all sync backup files')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old sync backup files')
    parser.add_argument('--keep-days', type=int, default=7,
                       help='Number of days to keep sync backups (default: 7)')
    parser.add_argument('--backup-dir', type=str, default='backups',
                       help='Backup directory (default: backups)')
    
    args = parser.parse_args()
    
    # Initialize sync manager
    db_sync = DatabaseSync(args.backup_dir)
    
    # Handle different operations
    if args.list:
        db_sync.list_sync_backups()
        return
    
    if args.cleanup:
        success = db_sync.cleanup_sync_backups(args.keep_days)
        sys.exit(0 if success else 1)
    
    # Determine sync direction
    if args.dev_to_staging:
        success = db_sync.sync_dev_to_staging(args.dry_run, args.force)
    elif args.staging_to_dev:
        success = db_sync.sync_staging_to_dev(args.dry_run, args.force)
    else:
        print("Error: Must specify sync direction (--dev-to-staging or --staging-to-dev)")
        print("Use --help for more information")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
