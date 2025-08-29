"""
TIGER/Line File Caching Utility

This module provides intelligent caching for TIGER/Line GIS data files to avoid
re-downloading the same files multiple times. It includes file validation,
cache management, and automatic cleanup.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Usage:
    from directory.utils.tiger_cache import TigerFileCache
    
    cache = TigerFileCache()
    file_path = cache.get_file('STATE', 2023)
"""

import os
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class TigerFileCache:
    """Intelligent caching system for TIGER/Line files."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_age_days: int = 30):
        """
        Initialize the TIGER file cache.
        
        Args:
            cache_dir: Directory to store cached files (default: ~/.tiger_cache)
            max_age_days: Maximum age of cached files in days (default: 30)
        """
        self.max_age_days = max_age_days
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / '.tiger_cache'
        
        # Create cache directory structure
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / 'files').mkdir(exist_ok=True)
        (self.cache_dir / 'metadata').mkdir(exist_ok=True)
        
        # File type configurations
        self.file_types = {
            'STATE': {
                'url_template': 'https://www2.census.gov/geo/tiger/TIGER{year}/STATE/tl_{year}_us_state.zip',
                'filename_template': 'tl_{year}_us_state.zip',
                'extract_pattern': '*.shp'
            },
            'COUNTY': {
                'url_template': 'https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip',
                'filename_template': 'tl_{year}_us_county.zip',
                'extract_pattern': '*.shp'
            },
            'CITY': {
                'url_template': 'https://www2.census.gov/geo/tiger/TIGER{year}/PLACE/tl_{year}_{state_fips}_place.zip',
                'filename_template': 'tl_{year}_{state_fips}_place.zip',
                'extract_pattern': '*.shp',
                'state_specific': True
            }
        }
    
    def get_cache_key(self, file_type: str, year: int, state_fips: str = None) -> str:
        """Generate a cache key for a file type and year."""
        if state_fips and self.file_types[file_type].get('state_specific', False):
            return f"{file_type}_{year}_{state_fips}"
        return f"{file_type}_{year}"
    
    def get_cache_path(self, file_type: str, year: int, state_fips: str = None) -> Path:
        """Get the cache path for a specific file."""
        cache_key = self.get_cache_key(file_type, year, state_fips)
        return self.cache_dir / 'files' / f"{cache_key}.zip"
    
    def get_metadata_path(self, file_type: str, year: int, state_fips: str = None) -> Path:
        """Get the metadata path for a specific file."""
        cache_key = self.get_cache_key(file_type, year, state_fips)
        return self.cache_dir / 'metadata' / f"{cache_key}.json"
    
    def is_cached(self, file_type: str, year: int, state_fips: str = None) -> bool:
        """Check if a file is cached and valid."""
        cache_path = self.get_cache_path(file_type, year, state_fips)
        metadata_path = self.get_metadata_path(file_type, year, state_fips)
        
        if not cache_path.exists() or not metadata_path.exists():
            return False
        
        # Check if file is too old
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata['cached_at'])
            if datetime.now() - cached_time > timedelta(days=self.max_age_days):
                logger.info(f"Cache expired for {file_type}_{year}")
                return False
            
            # Verify file integrity
            if metadata.get('file_size') != cache_path.stat().st_size:
                logger.info(f"File size mismatch for {file_type}_{year}")
                return False
            
            return True
            
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Error reading cache metadata for {file_type}_{year}: {e}")
            return False
    
    def get_cached_file(self, file_type: str, year: int, state_fips: str = None) -> Optional[Path]:
        """Get a cached file if it exists and is valid."""
        if self.is_cached(file_type, year, state_fips):
            cache_path = self.get_cache_path(file_type, year, state_fips)
            logger.info(f"Using cached file: {cache_path}")
            return cache_path
        return None
    
    def download_and_cache(self, file_type: str, year: int, progress_callback=None, state_fips: str = None) -> Path:
        """
        Download a file and cache it.
        
        Args:
            file_type: Type of file (STATE, COUNTY, CITY)
            year: Year of the data
            progress_callback: Optional callback for download progress
            state_fips: State FIPS code (required for state-specific files like cities)
            
        Returns:
            Path to the cached file
        """
        if file_type not in self.file_types:
            raise ValueError(f"Unknown file type: {file_type}")
        
        config = self.file_types[file_type]
        
        # Handle state-specific files
        if config.get('state_specific', False):
            if not state_fips:
                raise ValueError(f"State FIPS code required for {file_type} files")
            url = config['url_template'].format(year=year, state_fips=state_fips)
            filename = config['filename_template'].format(year=year, state_fips=state_fips)
        else:
            url = config['url_template'].format(year=year)
            filename = config['filename_template'].format(year=year)
        
        cache_path = self.get_cache_path(file_type, year, state_fips)
        metadata_path = self.get_metadata_path(file_type, year, state_fips)
        
        logger.info(f"Downloading {file_type} data for year {year}")
        
        # Download the file
        try:
            import urllib.request
            import urllib.error
            
            # Create temporary file for download
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download with progress tracking
            with urllib.request.urlopen(url) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded_size, total_size, filename)
            
            # Validate downloaded file
            if not self._validate_downloaded_file(Path(temp_path), file_type, year):
                os.unlink(temp_path)
                raise Exception(f"Downloaded file validation failed for {file_type}_{year}")
            
            # Move to cache location
            shutil.move(temp_path, cache_path)
            
            # Create metadata
            metadata = {
                'file_type': file_type,
                'year': year,
                'url': url,
                'filename': filename,
                'file_size': Path(cache_path).stat().st_size,
                'cached_at': datetime.now().isoformat(),
                'checksum': self._calculate_checksum(Path(cache_path))
            }
            
            # Add state_fips to metadata if applicable
            if state_fips:
                metadata['state_fips'] = state_fips
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Successfully cached {file_type} data for year {year}")
            return Path(cache_path)
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise Exception(f"Failed to download {file_type} data for year {year}: {str(e)}")
    
    def get_file(self, file_type: str, year: int, progress_callback=None, state_fips: str = None) -> Path:
        """
        Get a file from cache or download it if not cached.
        
        Args:
            file_type: Type of file (STATE, COUNTY, CITY)
            year: Year of the data
            progress_callback: Optional callback for download progress
            state_fips: State FIPS code (required for state-specific files like cities)
            
        Returns:
            Path to the file (cached or newly downloaded)
        """
        # Check if file is already cached
        cached_file = self.get_cached_file(file_type, year, state_fips)
        if cached_file:
            return cached_file
        
        # Download and cache the file
        return self.download_and_cache(file_type, year, progress_callback, state_fips)
    
    def get_city_file(self, year: int, state_fips: str, progress_callback=None) -> Path:
        """
        Get a city file for a specific state from cache or download it.
        
        Args:
            year: Year of the data
            state_fips: State FIPS code
            progress_callback: Optional callback for download progress
            
        Returns:
            Path to the cached file
        """
        return self.get_file('CITY', year, progress_callback, state_fips)
    
    def extract_shapefile(self, file_type: str, year: int, state_fips: str = None) -> Path:
        """
        Extract shapefile from cached ZIP file.
        
        Args:
            file_type: Type of file (STATE, COUNTY, CITY)
            year: Year of the data
            state_fips: State FIPS code (required for state-specific files)
            
        Returns:
            Path to the extracted shapefile
        """
        cache_path = self.get_file(file_type, year, state_fips=state_fips)
        config = self.file_types[file_type]
        
        # Create extraction directory
        if state_fips and config.get('state_specific', False):
            extract_dir = self.cache_dir / 'extracted' / f"{file_type}_{year}_{state_fips}"
        else:
            extract_dir = self.cache_dir / 'extracted' / f"{file_type}_{year}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract if not already extracted
        if not list(extract_dir.glob('*.shp')):
            logger.info(f"Extracting {file_type} data for year {year}")
            with zipfile.ZipFile(cache_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        # Find the shapefile
        shp_files = list(extract_dir.glob('*.shp'))
        if not shp_files:
            raise Exception(f"No shapefile found in extracted {file_type} data for year {year}")
        
        return shp_files[0]
    
    def clear_cache(self, file_type: Optional[str] = None, year: Optional[int] = None):
        """
        Clear cached files.
        
        Args:
            file_type: Specific file type to clear (None for all)
            year: Specific year to clear (None for all)
        """
        if file_type and year:
            # Clear specific file
            cache_path = self.get_cache_path(file_type, year)
            metadata_path = self.get_metadata_path(file_type, year)
            extract_dir = self.cache_dir / 'extracted' / f"{file_type}_{year}"
            
            if cache_path.exists():
                cache_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
                
            logger.info(f"Cleared cache for {file_type}_{year}")
        else:
            # Clear all cache
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            (self.cache_dir / 'files').mkdir(exist_ok=True)
            (self.cache_dir / 'metadata').mkdir(exist_ok=True)
            logger.info("Cleared all cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached files."""
        info = {
            'cache_dir': str(self.cache_dir),
            'max_age_days': self.max_age_days,
            'cached_files': []
        }
        
        metadata_dir = self.cache_dir / 'metadata'
        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob('*.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Check if file still exists
                    state_fips = metadata.get('state_fips')
                    cache_path = self.get_cache_path(metadata['file_type'], metadata['year'], state_fips)
                    if cache_path.exists():
                        cached_time = datetime.fromisoformat(metadata['cached_at'])
                        age_days = (datetime.now() - cached_time).days
                        
                        file_info = {
                            'file_type': metadata['file_type'],
                            'year': metadata['year'],
                            'file_size': metadata['file_size'],
                            'cached_at': metadata['cached_at'],
                            'age_days': age_days,
                            'is_expired': age_days > self.max_age_days
                        }
                        
                        # Add state_fips info for state-specific files
                        if state_fips:
                            file_info['state_fips'] = state_fips
                        
                        info['cached_files'].append(file_info)
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {e}")
        
        return info
    
    def _validate_downloaded_file(self, file_path: Path, file_type: str, year: int) -> bool:
        """Validate a downloaded file."""
        try:
            # Check if it's a valid ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Check if it contains expected files
                file_list = zip_ref.namelist()
                if not any(f.endswith('.shp') for f in file_list):
                    return False
                
                # Check file size (should be reasonable)
                if file_path.stat().st_size < 1000:  # Less than 1KB is suspicious
                    return False
                
                return True
        except zipfile.BadZipFile:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def cleanup_expired(self):
        """Remove expired cache files."""
        info = self.get_cache_info()
        expired_files = [f for f in info['cached_files'] if f['is_expired']]
        
        for file_info in expired_files:
            self.clear_cache(file_info['file_type'], file_info['year'])
        
        if expired_files:
            logger.info(f"Cleaned up {len(expired_files)} expired cache files")
        else:
            logger.info("No expired cache files to clean up")
