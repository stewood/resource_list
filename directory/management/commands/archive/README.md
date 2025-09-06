# Archived Management Commands

This directory contains management commands that were used for one-time operations, development/testing, or initial setup. These commands are no longer needed for regular production use but are preserved for reference and potential future use.

## 📁 Directory Structure

```
archive/
├── one_off_tests/          # Commands used for testing specific functionality
├── one_time_imports/       # Commands used for initial data import
├── development_utils/      # Commands used for development setup
└── README.md              # This documentation
```

## 🧪 One-Off Tests (`one_off_tests/`)

### `test_search.py`
- **Purpose**: Test FTS5 search functionality with sample queries
- **When Used**: During development to verify search implementation
- **Current Status**: No longer needed - search functionality is now integrated into main CLI
- **Usage**: `python manage.py test_search --query="shelter"`

### `create_test_boundaries.py`
- **Purpose**: Create test CoverageArea records with proper geometry for Kentucky counties and states
- **When Used**: During development to test service area functionality without requiring TIGER/Line data
- **Current Status**: No longer needed - production geographic data is now available
- **Usage**: `python manage.py create_test_boundaries`

## 📥 One-Time Imports (`one_time_imports/`)

### `import_states_enhanced.py`
- **Purpose**: Import state-level geographic data with enhanced metadata
- **When Used**: Initial setup to populate state information
- **Current Status**: Completed - states are now in the database
- **Usage**: `python manage.py import_states_enhanced`

### `import_cities_enhanced.py`
- **Purpose**: Import city-level geographic data with enhanced metadata
- **When Used**: Initial setup to populate city information
- **Current Status**: Completed - cities are now in the database
- **Usage**: `python manage.py import_cities_enhanced`

### `import_counties_enhanced.py`
- **Purpose**: Import county-level geographic data with enhanced metadata
- **When Used**: Initial setup to populate county information
- **Current Status**: Completed - counties are now in the database
- **Usage**: `python manage.py import_counties_enhanced`

### `import_csv_data.py`
- **Purpose**: Generic CSV importer for resource data
- **When Used**: Initial data migration or bulk import operations
- **Current Status**: Completed - data is now in the database
- **Usage**: `python manage.py import_csv_data --file=path/to/file.csv`

## ⚙️ Development Utilities (`development_utils/`)

### `setup_groups.py`
- **Purpose**: Set up user groups and permissions for the system
- **When Used**: Initial system setup and configuration
- **Current Status**: Completed - groups and permissions are configured
- **Usage**: `python manage.py setup_groups`

### `setup_service_types.py`
- **Purpose**: Configure service type taxonomies and categories
- **When Used**: Initial system setup to establish service type hierarchy
- **Current Status**: Completed - service types are configured
- **Usage**: `python manage.py setup_service_types`

### `setup_wal.py`
- **Purpose**: Configure SQLite database with WAL mode and optimal settings
- **When Used**: One-time database optimization setup
- **Current Status**: Completed - database is optimized
- **Usage**: `python manage.py setup_wal`

### `wait_for_db.py`
- **Purpose**: Pause execution until database is available
- **When Used**: During deployment to ensure database readiness
- **Current Status**: May be useful for future deployments
- **Usage**: `python manage.py wait_for_db`

## 🔄 When to Use Archived Commands

### **Never Use in Production:**
- `one_off_tests/` - These are development tools only
- `one_time_imports/` - Data is already imported

### **Use Only for New Deployments:**
- `development_utils/` - Only if setting up a completely new environment

### **Use for Data Recovery:**
- `one_time_imports/` - Only if you need to completely rebuild geographic data

## 🚨 Important Notes

1. **Data Duplication**: Running import commands again may create duplicate data
2. **Test Environment**: These commands were designed for development/testing environments
3. **Dependencies**: Some commands may have dependencies that are no longer available
4. **Backup**: Always backup your database before running any of these commands

## 📋 Restoration Process

If you need to restore any of these commands:

1. Move the file back to the main `commands/` directory
2. Check for any missing dependencies
3. Review the command for compatibility with current models
4. Test in a development environment first
5. Update any hardcoded paths or configurations

## 🔍 Finding Active Commands

For current production commands, see the main `commands/` directory:

- **`resource_cli.py`** - Main resource management CLI (45% complete)
- **`cli_utils.py`** - Shared CLI utilities
- **`check_data_quality.py`** - Ongoing data validation
- **`find_duplicates.py`** - Ongoing deduplication
- **`merge_duplicates.py`** - Ongoing cleanup
- **`fix_published_versions.py`** - Ongoing maintenance
- **`load_geojson.py`** - Geographic data management
- **`manage_geocoding_cache.py`** - Geocoding cache management

## 📅 Archive Date

**Archived**: January 2025  
**Reason**: Cleanup of development and one-time use commands  
**Maintained by**: Resource Directory Team
