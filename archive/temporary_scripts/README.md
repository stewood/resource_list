# Temporary Scripts Archive

This directory contains one-time scripts that were used during development and migration phases of the Homeless Resource Directory project. These scripts are preserved for reference but are no longer needed for daily development.

## Script Categories

### **Coverage Analysis Scripts**
- `analyze_resources_without_coverage.py` - Analyzed resources that lacked coverage area assignments
- `check_kentucky_coverage.py` - Checked coverage for Kentucky-specific resources
- `check_us_coverage.py` - Checked coverage for US-wide resources
- `check_resource_coverage.py` - General resource coverage checking
- `check_resources_without_coverage.py` - Identified resources without any coverage areas

### **Migration Scripts**
- `import_coverage_areas_from_json.py` - Imported coverage areas from JSON data files
- `migrate_gis_data.py` - Migrated GIS data to PostgreSQL
- `migrate_gis_data_batch.py` - Batch migration of GIS data
- `simple_coverage_import.py` - Simple coverage area import utility

### **Data Fix Scripts**
- `comprehensive_geometry_fix.py` - Fixed geometry issues in coverage areas
- `final_geometry_fix.py` - Final geometry corrections
- `fix_resource_coverage.py` - Fixed resource coverage assignments
- `manual_kentucky_import.py` - Manual import of Kentucky-specific data

### **Debug and Test Scripts**
- `debug_migration.py` - Debugging migration issues
- `debug_state_import.py` - Debugging state data import
- `test_fips.py` - Testing FIPS code functionality
- `test_migration.py` - Testing migration processes

## Usage Notes

These scripts were used during the development phase to:
1. **Migrate data** from SQLite to PostgreSQL
2. **Import coverage areas** from various sources
3. **Fix data quality issues** in the database
4. **Test functionality** during development
5. **Debug issues** during migration

## Current Status

All migration and data import tasks have been completed successfully. The main application now uses:
- PostgreSQL database with spatial extensions
- 7,829 coverage areas covering 83.5% of resources
- Automated data quality processes
- Production-ready deployment pipeline

## Preservation

These scripts are preserved for:
- **Historical reference** - Understanding the migration process
- **Troubleshooting** - If similar issues arise in the future
- **Documentation** - Showing the evolution of the data import process

---

**Last Updated**: 2025-01-15
**Status**: Archived - No longer needed for daily development
**Total Files**: 17 scripts
**Total Size**: ~100KB
