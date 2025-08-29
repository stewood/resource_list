# GIS File Caching Guide

This guide explains the TIGER/Line file caching system implemented in the Resource Directory application.

## Overview

The GIS import system now includes intelligent file caching to avoid re-downloading the same TIGER/Line files multiple times. This significantly improves performance and reduces bandwidth usage.

## Features

- **Automatic Caching**: Files are cached automatically on first download
- **Smart Validation**: Cached files are validated for integrity
- **Expiration Management**: Files expire after 30 days (configurable)
- **Progress Tracking**: Download progress with Rich-based UI
- **Cache Management**: Tools to view, clear, and manage cached files

## Cache Structure

```
~/.tiger_cache/
├── files/           # Cached ZIP files
│   ├── STATE_2023.zip
│   ├── COUNTY_2023.zip
│   └── CITY_2023.zip
├── metadata/        # File metadata and validation info
│   ├── STATE_2023.json
│   ├── COUNTY_2023.json
│   └── CITY_2023.json
└── extracted/       # Extracted shapefiles
    ├── STATE_2023/
    ├── COUNTY_2023/
    └── CITY_2023/
```

## Usage

### Basic Import Commands

The caching is transparent to normal usage. All import commands automatically use cached files when available:

```bash
# These commands will use cached files if available
python scripts/geo_manager.py populate KY,IN,IL
python scripts/geo_manager.py kentucky-region
python scripts/geo_manager.py populate all
```

### Cache Management Commands

#### View Cache Status

```bash
# Show cache status in geo manager
python scripts/geo_manager.py cache-status

# Or use standalone cache manager
python scripts/cache_manager.py status
```

Example output:
```
TIGER/Line Cache Status
────────────────────────────────────────────────────────

Cache Directory: /home/user/.tiger_cache
Max Age: 30 days

Cached Files (3):
┌─────────┬──────┬──────────────┬─────────────────┬──────────┬─────────┐
│ Type    │ Year │ Size         │ Cached          │ Age      │ Status  │
├─────────┼──────┼──────────────┼─────────────────┼──────────┼─────────┤
│ STATE   │ 2023 │ 1,234,567    │ 2025-01-15 10:30│ 5 days   │ ✅ Valid│
│ COUNTY  │ 2023 │ 5,678,901    │ 2025-01-15 10:35│ 5 days   │ ✅ Valid│
│ CITY    │ 2023 │ 12,345,678   │ 2025-01-15 10:40│ 5 days   │ ✅ Valid│
└─────────┴──────┴──────────────┴─────────────────┴──────────┴─────────┘

Summary:
  • Total files: 3
  • Total size: 19,259,146 bytes (18.4 MB)
  • Valid files: 3
  • Expired files: 0
```

#### Clear Cache

```bash
# Clear all cached files
python scripts/geo_manager.py cache-clear

# Or use standalone cache manager
python scripts/cache_manager.py clear
```

#### Clean Up Expired Files

```bash
# Remove only expired files
python scripts/geo_manager.py cache-cleanup

# Or use standalone cache manager
python scripts/cache_manager.py cleanup
```

#### Download Specific Files

```bash
# Download specific files to cache
python scripts/cache_manager.py download STATE 2023
python scripts/cache_manager.py download COUNTY 2023
python scripts/cache_manager.py download CITY 2023
```

#### Validate Cache

```bash
# Validate all cached files
python scripts/cache_manager.py validate
```

## Configuration

### Cache Directory

By default, files are cached in `~/.tiger_cache`. You can specify a custom directory:

```python
from directory.utils.tiger_cache import TigerFileCache

# Use custom cache directory
cache = TigerFileCache(cache_dir='/path/to/custom/cache')
```

### Cache Expiration

Files expire after 30 days by default. You can change this:

```python
# Set expiration to 60 days
cache = TigerFileCache(max_age_days=60)
```

## File Types

The caching system supports three file types:

- **STATE**: State boundary files (`tl_YYYY_us_state.zip`)
- **COUNTY**: County boundary files (`tl_YYYY_us_county.zip`)
- **CITY**: City/place boundary files (`tl_YYYY_us_place.zip`)

## Performance Benefits

### Before Caching
- Each import operation downloads files from US Census Bureau
- Multiple imports of the same data = multiple downloads
- Slower import times
- Higher bandwidth usage

### After Caching
- Files downloaded once and reused
- Subsequent imports use cached files
- Faster import times
- Reduced bandwidth usage

### Example Performance Improvement

**First Import (Download + Process):**
```
Downloading STATE data: ~1.2 MB
Downloading COUNTY data: ~5.7 MB
Downloading CITY data: ~12.3 MB
Total: ~19.2 MB downloaded, 2-3 minutes
```

**Subsequent Imports (Cached):**
```
Using cached STATE data: ~1.2 MB
Using cached COUNTY data: ~5.7 MB
Using cached CITY data: ~12.3 MB
Total: 0 MB downloaded, 30-60 seconds
```

## Technical Details

### Cache Validation

The system validates cached files using:

1. **File Existence**: Check if file exists
2. **File Size**: Verify file size matches metadata
3. **Age Check**: Ensure file hasn't expired
4. **ZIP Integrity**: Validate ZIP file structure
5. **Shapefile Check**: Ensure ZIP contains shapefiles

### Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **Corrupted Files**: Automatic re-download
- **Expired Files**: Automatic cleanup
- **Disk Space**: Graceful handling of insufficient space

### Thread Safety

The caching system is thread-safe and can be used in concurrent operations.

## Troubleshooting

### Cache Issues

If you experience cache-related issues:

1. **Clear the cache**:
   ```bash
   python scripts/cache_manager.py clear
   ```

2. **Validate cached files**:
   ```bash
   python scripts/cache_manager.py validate
   ```

3. **Check disk space**:
   ```bash
   df -h ~/.tiger_cache
   ```

### Common Problems

#### "File not found" errors
- Clear cache and retry: `python scripts/cache_manager.py clear`

#### "Invalid file" errors
- Validate cache: `python scripts/cache_manager.py validate`
- Clear cache if validation fails

#### Slow performance
- Check if cache is being used: `python scripts/cache_manager.py status`
- Ensure cache directory has sufficient space

#### Network timeouts
- Check internet connection
- Try downloading specific files: `python scripts/cache_manager.py download STATE 2023`

## Integration with Import Commands

The caching system is integrated into all import commands:

- `import_states_enhanced`
- `import_counties_enhanced`
- `import_cities_enhanced`
- `geo_manager.py` commands

All commands automatically use cached files when available and fall back to downloading when needed.

## Best Practices

1. **Regular Cleanup**: Run `cache-cleanup` periodically to remove expired files
2. **Monitor Space**: Keep an eye on cache directory size
3. **Validate After Issues**: Run validation if you experience import problems
4. **Pre-download**: Download files before large import operations
5. **Backup Cache**: Consider backing up cache directory for offline operations

## API Reference

### TigerFileCache Class

```python
class TigerFileCache:
    def __init__(self, cache_dir=None, max_age_days=30):
        """Initialize cache with optional custom directory and expiration."""
    
    def get_file(self, file_type, year, progress_callback=None):
        """Get file from cache or download if not cached."""
    
    def is_cached(self, file_type, year):
        """Check if file is cached and valid."""
    
    def clear_cache(self, file_type=None, year=None):
        """Clear cache (all or specific file)."""
    
    def get_cache_info(self):
        """Get detailed cache information."""
    
    def cleanup_expired(self):
        """Remove expired cache files."""
```

## Migration from Non-Cached System

If you're upgrading from a system without caching:

1. **No Data Migration Required**: The system automatically starts caching on first use
2. **Backward Compatible**: All existing commands work the same way
3. **Performance Improvement**: Immediate performance benefits on subsequent runs
4. **Optional Cleanup**: You can clear old temporary files if desired

## Future Enhancements

Potential future improvements:

- **Compression**: Compress cached files to save space
- **CDN Integration**: Use CDN for faster downloads
- **Incremental Updates**: Only download changed files
- **Parallel Downloads**: Download multiple files simultaneously
- **Cache Sharing**: Share cache between multiple installations
