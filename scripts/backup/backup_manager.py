#!/usr/bin/env python3
"""
Backup Manager for Community Resource Directory

This script provides comprehensive backup functionality for both local development
and staging environments. It supports database backups, file backups, and
automated backup management with retention policies.

Features:
    - Local PostgreSQL database backup (development)
    - Remote PostgreSQL database backup (staging via Render)
    - File system backup (code, media, static files)
    - Automated backup rotation and retention
    - Compressed backup storage
    - Backup verification and integrity checks
    - Detailed logging and reporting

Usage:
    python scripts/backup/backup_manager.py --help
    python scripts/backup/backup_manager.py --local-db
    python scripts/backup/backup_manager.py --staging-db
    python scripts/backup/backup_manager.py --files
    python scripts/backup/backup_manager.py --all
    python scripts/backup/backup_manager.py --cleanup --keep-days 30

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import argparse
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import django
from django.conf import settings
from django.core.management import execute_from_command_line

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


class BackupManager:
    """Comprehensive backup management system for the Resource Directory project."""

    def __init__(self, backup_dir: str = "backups"):
        """Initialize the backup manager.
        
        Args:
            backup_dir: Directory to store backups (relative to project root)
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.backup_dir = self.project_root / backup_dir
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "databases").mkdir(exist_ok=True)
        (self.backup_dir / "files").mkdir(exist_ok=True)
        (self.backup_dir / "logs").mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Backup configuration
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
            },
            'retention_days': 30,
            'compression': True
        }

    def setup_logging(self):
        """Setup logging configuration."""
        log_file = self.backup_dir / "logs" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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

    def backup_local_database(self) -> bool:
        """Backup local development PostgreSQL database.
        
        Returns:
            True if backup successful, False otherwise
        """
        try:
            self.logger.info("Starting local database backup...")
            print("🔄 Starting local database backup...")
            
            timestamp = self.get_timestamp()
            backup_file = self.backup_dir / "databases" / f"local_db_backup_{timestamp}.sql"
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                f'--host={self.config["local_db"]["host"]}',
                f'--port={self.config["local_db"]["port"]}',
                f'--username={self.config["local_db"]["user"]}',
                f'--dbname={self.config["local_db"]["name"]}',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_file}'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config["local_db"]["password"]
            
            print(f"   📍 Target: {self.config['local_db']['host']}:{self.config['local_db']['port']}/{self.config['local_db']['name']}")
            print(f"   📁 Output: {backup_file.name}")
            
            # Execute backup with progress monitoring
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress based on file size
            tracker = FileProgressTracker("Backing up local database", backup_file)
            tracker.start()
            
            # Monitor the process
            while process.poll() is None:
                tracker.update("(backup in progress...)")
                time.sleep(1)  # Check every second
            
            # Wait for completion
            return_code = process.poll()
            
            if return_code == 0:
                # Compress backup if enabled
                if self.config['compression']:
                    print("   📦 Compressing backup file...")
                    compressed_file = backup_file.with_suffix('.sql.gz')
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()  # Remove uncompressed file
                    backup_file = compressed_file
                
                tracker.complete("✅ Backup completed successfully")
                self.logger.info(f"Local database backup completed: {backup_file.name}")
                return True
            else:
                _, stderr = process.communicate()
                self.logger.error(f"Local database backup failed: {stderr}")
                print(f"❌ Local database backup failed: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Local database backup error: {str(e)}")
            print(f"❌ Local database backup error: {str(e)}")
            return False

    def backup_staging_database(self) -> bool:
        """Backup staging PostgreSQL database on Render.
        
        Returns:
            True if backup successful, False otherwise
        """
        try:
            self.logger.info("Starting staging database backup...")
            print("🔄 Starting staging database backup...")
            
            timestamp = self.get_timestamp()
            backup_file = self.backup_dir / "databases" / f"staging_db_backup_{timestamp}.sql"
            
            # Build pg_dump command for remote database
            cmd = [
                'pg_dump',
                f'--host={self.config["staging_db"]["host"]}',
                f'--port={self.config["staging_db"]["port"]}',
                f'--username={self.config["staging_db"]["user"]}',
                f'--dbname={self.config["staging_db"]["name"]}',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_file}'
            ]
            
            # Set environment variables for remote connection
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config["staging_db"]["password"]
            env['PGSSLMODE'] = 'require'
            
            print(f"   📍 Target: {self.config['staging_db']['host']}:{self.config['staging_db']['port']}/{self.config['staging_db']['name']}")
            print(f"   📁 Output: {backup_file.name}")
            
            # Execute backup with progress monitoring
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress based on file size
            tracker = FileProgressTracker("Backing up staging database", backup_file)
            tracker.start()
            
            # Monitor the process
            while process.poll() is None:
                tracker.update("(backup in progress...)")
                time.sleep(1)  # Check every second
            
            # Wait for completion
            return_code = process.poll()
            
            if return_code == 0:
                # Compress backup if enabled
                if self.config['compression']:
                    print("   📦 Compressing backup file...")
                    compressed_file = backup_file.with_suffix('.sql.gz')
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()  # Remove uncompressed file
                    backup_file = compressed_file
                
                tracker.complete("✅ Backup completed successfully")
                self.logger.info(f"Staging database backup completed: {backup_file.name}")
                return True
            else:
                _, stderr = process.communicate()
                self.logger.error(f"Staging database backup failed: {stderr}")
                print(f"❌ Staging database backup failed: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Staging database backup error: {str(e)}")
            print(f"❌ Staging database backup error: {str(e)}")
            return False

    def backup_files(self) -> bool:
        """Backup important project files and directories.
        
        Returns:
            True if backup successful, False otherwise
        """
        try:
            self.logger.info("Starting file system backup...")
            
            timestamp = self.get_timestamp()
            backup_file = self.backup_dir / "files" / f"files_backup_{timestamp}.tar.gz"
            
            # Define directories and files to backup
            backup_items = [
                'directory',           # Main application
                'audit',              # Audit app
                'importer',           # Importer app
                'resource_directory', # Settings
                'templates',          # Templates
                'static',             # Static files
                'media',              # Media files (if exists)
                'requirements.txt',   # Dependencies
                'manage.py',          # Django management
                'Dockerfile',         # Docker configuration
                'docker-compose.yml', # Docker compose
                'README.md',          # Documentation
                'RELEASE_NOTES.md',   # Release notes
                'CONTRIBUTING.md',    # Contributing guide
            ]
            
            # Create tar.gz archive
            with tarfile.open(backup_file, 'w:gz') as tar:
                for item in backup_items:
                    item_path = self.project_root / item
                    if item_path.exists():
                        tar.add(item_path, arcname=item)
                        self.logger.info(f"Added to backup: {item}")
                    else:
                        self.logger.warning(f"Item not found, skipping: {item}")
            
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            self.logger.info(f"File system backup completed: {backup_file.name} ({file_size:.2f} MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"File system backup error: {str(e)}")
            return False

    def cleanup_old_backups(self, keep_days: int = None) -> bool:
        """Remove old backups based on retention policy.
        
        Args:
            keep_days: Number of days to keep backups (defaults to config)
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if keep_days is None:
                keep_days = self.config['retention_days']
            
            self.logger.info(f"Cleaning up backups older than {keep_days} days...")
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            total_size_freed = 0
            
            # Clean up database backups
            db_backup_dir = self.backup_dir / "databases"
            for backup_file in db_backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_size = backup_file.stat().st_size
                        backup_file.unlink()
                        deleted_count += 1
                        total_size_freed += file_size
                        self.logger.info(f"Deleted old backup: {backup_file.name}")
            
            # Clean up file backups
            files_backup_dir = self.backup_dir / "files"
            for backup_file in files_backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_size = backup_file.stat().st_size
                        backup_file.unlink()
                        deleted_count += 1
                        total_size_freed += file_size
                        self.logger.info(f"Deleted old backup: {backup_file.name}")
            
            # Clean up old logs (keep last 7 days)
            logs_backup_dir = self.backup_dir / "logs"
            log_cutoff = datetime.now() - timedelta(days=7)
            for log_file in logs_backup_dir.glob("*"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < log_cutoff:
                        log_file.unlink()
                        self.logger.info(f"Deleted old log: {log_file.name}")
            
            total_size_mb = total_size_freed / (1024 * 1024)
            self.logger.info(f"Cleanup completed: {deleted_count} files deleted, {total_size_mb:.2f} MB freed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            return False

    def list_backups(self) -> None:
        """List all available backups with details."""
        try:
            self.logger.info("Listing available backups...")
            
            print("\n" + "="*80)
            print("BACKUP INVENTORY")
            print("="*80)
            
            # Database backups
            print("\n📊 DATABASE BACKUPS:")
            print("-" * 40)
            db_backup_dir = self.backup_dir / "databases"
            if db_backup_dir.exists():
                for backup_file in sorted(db_backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                    if backup_file.is_file():
                        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                        print(f"  {backup_file.name}")
                        print(f"    Date: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Size: {file_size:.2f} MB")
                        print()
            else:
                print("  No database backups found")
            
            # File backups
            print("\n📁 FILE BACKUPS:")
            print("-" * 40)
            files_backup_dir = self.backup_dir / "files"
            if files_backup_dir.exists():
                for backup_file in sorted(files_backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                    if backup_file.is_file():
                        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                        print(f"  {backup_file.name}")
                        print(f"    Date: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Size: {file_size:.2f} MB")
                        print()
            else:
                print("  No file backups found")
            
            # Backup directory info
            total_size = sum(f.stat().st_size for f in self.backup_dir.rglob('*') if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            print(f"\n💾 TOTAL BACKUP SIZE: {total_size_mb:.2f} MB")
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {str(e)}")

    def verify_backup(self, backup_file: str) -> bool:
        """Verify the integrity of a backup file.
        
        Args:
            backup_file: Path to backup file to verify
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            self.logger.info(f"Verifying backup: {backup_path.name}")
            
            # Check file size
            file_size = backup_path.stat().st_size
            if file_size == 0:
                self.logger.error("Backup file is empty")
                return False
            
            # Check file extension and verify accordingly
            if backup_path.suffix == '.gz':
                # Verify gzip integrity
                try:
                    with gzip.open(backup_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB to test integrity
                    self.logger.info("Gzip backup file integrity verified")
                except Exception as e:
                    self.logger.error(f"Gzip backup file corrupted: {str(e)}")
                    return False
            
            elif backup_path.suffix == '.tar.gz':
                # Verify tar.gz integrity
                try:
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        tar.getmembers()  # Test archive integrity
                    self.logger.info("Tar.gz backup file integrity verified")
                except Exception as e:
                    self.logger.error(f"Tar.gz backup file corrupted: {str(e)}")
                    return False
            
            else:
                # Assume SQL file
                try:
                    with open(backup_path, 'r') as f:
                        first_line = f.readline().strip()
                        if not first_line.startswith('--') and not first_line.startswith('SET'):
                            self.logger.warning("SQL backup file may be corrupted (unexpected first line)")
                except Exception as e:
                    self.logger.error(f"SQL backup file error: {str(e)}")
                    return False
            
            self.logger.info(f"Backup verification successful: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification error: {str(e)}")
            return False

    def run_backup(self, backup_type: str, cleanup: bool = False, keep_days: int = None) -> bool:
        """Run the specified backup operation.
        
        Args:
            backup_type: Type of backup to run ('local-db', 'staging-db', 'files', 'all')
            cleanup: Whether to run cleanup after backup
            keep_days: Number of days to keep backups (for cleanup)
            
        Returns:
            True if all operations successful, False otherwise
        """
        success = True
        
        try:
            if backup_type in ['local-db', 'all']:
                if not self.backup_local_database():
                    success = False
            
            if backup_type in ['staging-db', 'all']:
                if not self.backup_staging_database():
                    success = False
            
            if backup_type in ['files', 'all']:
                if not self.backup_files():
                    success = False
            
            if cleanup:
                if not self.cleanup_old_backups(keep_days):
                    success = False
            
            if success:
                self.logger.info("Backup operation completed successfully")
            else:
                self.logger.error("Backup operation completed with errors")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Backup operation failed: {str(e)}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backup Manager for Community Resource Directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup local development database
  python scripts/backup/backup_manager.py --local-db
  
  # Backup staging database on Render
  python scripts/backup/backup_manager.py --staging-db
  
  # Backup all files and directories
  python scripts/backup/backup_manager.py --files
  
  # Full backup (all databases and files)
  python scripts/backup/backup_manager.py --all
  
  # Cleanup old backups (keep last 30 days)
  python scripts/backup/backup_manager.py --cleanup
  
  # Cleanup with custom retention (keep last 7 days)
  python scripts/backup/backup_manager.py --cleanup --keep-days 7
  
  # List all available backups
  python scripts/backup/backup_manager.py --list
  
  # Verify a specific backup file
  python scripts/backup/backup_manager.py --verify backups/databases/local_db_backup_20250115_120000.sql.gz
        """
    )
    
    # Backup type options
    backup_group = parser.add_mutually_exclusive_group(required=False)
    backup_group.add_argument('--local-db', action='store_true', 
                             help='Backup local development PostgreSQL database')
    backup_group.add_argument('--staging-db', action='store_true', 
                             help='Backup staging PostgreSQL database on Render')
    backup_group.add_argument('--files', action='store_true', 
                             help='Backup project files and directories')
    backup_group.add_argument('--all', action='store_true', 
                             help='Backup everything (local DB, staging DB, and files)')
    
    # Utility options
    parser.add_argument('--cleanup', action='store_true', 
                       help='Clean up old backups based on retention policy')
    parser.add_argument('--keep-days', type=int, default=30,
                       help='Number of days to keep backups (default: 30)')
    parser.add_argument('--list', action='store_true', 
                       help='List all available backups')
    parser.add_argument('--verify', type=str, metavar='FILE',
                       help='Verify integrity of a specific backup file')
    parser.add_argument('--backup-dir', type=str, default='backups',
                       help='Backup directory (default: backups)')
    
    args = parser.parse_args()
    
    # Initialize backup manager
    backup_manager = BackupManager(args.backup_dir)
    
    # Handle different operations
    if args.list:
        backup_manager.list_backups()
        return
    
    if args.verify:
        success = backup_manager.verify_backup(args.verify)
        sys.exit(0 if success else 1)
    
    if args.cleanup and not any([args.local_db, args.staging_db, args.files, args.all]):
        success = backup_manager.cleanup_old_backups(args.keep_days)
        sys.exit(0 if success else 1)
    
    # Determine backup type
    if args.all:
        backup_type = 'all'
    elif args.local_db:
        backup_type = 'local-db'
    elif args.staging_db:
        backup_type = 'staging-db'
    elif args.files:
        backup_type = 'files'
    else:
        # Default to local database backup if no type specified
        backup_type = 'local-db'
    
    # Run backup operation
    success = backup_manager.run_backup(backup_type, args.cleanup, args.keep_days)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
