"""
Progress tracking utilities for scripts.

This module provides reusable progress tracking classes for long-running operations
and file-based progress monitoring.

Classes:
    ProgressBar: Simple progress bar for operations with known totals
    FileProgressTracker: Track progress based on file size changes

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import time
from pathlib import Path


class ProgressBar:
    """Simple progress bar for long-running operations."""
    
    def __init__(self, description: str, total: int = 100):
        """Initialize progress bar.
        
        Args:
            description: Description to display with progress
            total: Total number of items/steps (default: 100)
        """
        self.description = description
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        
    def update(self, current: int, message: str = ""):
        """Update progress bar.
        
        Args:
            current: Current progress value
            message: Optional message to display
        """
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
        """Mark progress as complete.
        
        Args:
            message: Optional completion message
        """
        self.update(self.total, message)
        print()  # New line after completion


class FileProgressTracker:
    """Track progress based on file size changes."""
    
    def __init__(self, description: str, target_file: Path):
        """Initialize file progress tracker.
        
        Args:
            description: Description to display with progress
            target_file: Path to the file being tracked
        """
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
        """Update progress based on file size or time elapsed.
        
        Args:
            message: Optional message to display
        """
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
        """Mark progress as complete.
        
        Args:
            message: Optional completion message
        """
        if self.target_file.exists():
            final_size = self.target_file.stat().st_size / (1024 * 1024)
            elapsed = time.time() - self.start_time
            print(f"\r   ✅ Completed: {final_size:.2f} MB in {elapsed:.1f}s {message}")
        else:
            elapsed = time.time() - self.start_time
            print(f"\r   ❌ Failed: File not created after {elapsed:.1f}s {message}")
