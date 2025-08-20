# Geographic Data Update Scripts

This directory contains scripts for downloading and updating geographic data for the Resource Directory app.

## Overview

The Resource Directory app uses TIGER/Line data from the US Census Bureau to provide geographic boundaries for:
- **States** (56 US states and territories)
- **Counties** (3,200+ counties across the US)
- **Cities** (40,000+ cities and places across the US)

## Quick Start

### Check Current Data Status
```bash
./scripts/update_data.sh --status-only
```

### Update Existing Data (Recommended)
This will update existing records with new boundary data from the latest TIGER/Line release:
```bash
./scripts/update_data.sh --update-existing
```

### Import All US Data (Fresh Start)
This will clear existing data and import everything fresh:
```bash
./scripts/update_data.sh --all-states --clear-existing
```

## Scripts

### 1. `update_data.sh` (Recommended)
A user-friendly shell script wrapper that handles:
- Virtual environment activation
- Environment setup
- Error handling
- Colored output

**Usage:**
```bash
./scripts/update_data.sh [options]
```

**Options:**
- `--all-states` - Import data for all US states (default: KY and surrounding states)
- `--clear-existing` - Clear existing data before importing
- `--update-existing` - Update existing records with new data (default: skip existing)
- `--year YEAR` - TIGER/Line year to use (default: 2023)
- `--status-only` - Only show current data status
- `--help` - Show help message

### 2. `update_geographic_data.py`
The main Python script that orchestrates the data import process.

**Usage:**
```bash
source venv/bin/activate
GIS_ENABLED=1 python scripts/update_geographic_data.py [options]
```

## Data Coverage

### Default Coverage (Kentucky and Surrounding States)
When run without `--all-states`, the script imports data for:
- Kentucky (KY)
- Indiana (IN)
- Illinois (IL)
- Missouri (MO)
- Tennessee (TN)
- Virginia (VA)
- West Virginia (WV)
- Ohio (OH)

### Full Coverage (All US States)
When run with `--all-states`, the script imports data for all 56 US states and territories.

## Update Strategies

### 1. Skip Existing (Default)
- **Behavior**: Skips records that already exist
- **Use Case**: Initial import, when you don't want to overwrite existing data
- **Command**: `./scripts/update_data.sh`

### 2. Update Existing
- **Behavior**: Updates existing records with new boundary data
- **Use Case**: Keeping data current with latest TIGER/Line releases
- **Command**: `./scripts/update_data.sh --update-existing`

### 3. Clear and Reimport
- **Behavior**: Deletes all existing data and imports fresh
- **Use Case**: Complete reset, major data structure changes
- **Command**: `./scripts/update_data.sh --clear-existing`

## TIGER/Line Data

### What is TIGER/Line?
TIGER/Line (Topologically Integrated Geographic Encoding and Referencing) is a digital database of geographic features, such as roads, railroads, rivers, lakes, political boundaries, and census statistical boundaries, covering the entire United States.

### Update Frequency
- **Annual Release**: New TIGER/Line data is typically released in December
- **Boundary Changes**: County and city boundaries can change due to annexations, incorporations, etc.
- **Recommended**: Update data annually or when boundary changes are important

### Data Years
- **2023**: Latest stable release (default)
- **2024**: Latest release (may be in development)
- **2022**: Previous stable release

## Individual Import Commands

You can also run individual import commands directly:

### Import States
```bash
python manage.py import_states_simple --states 21,47,51 --update-existing
```

### Import Counties
```bash
python manage.py import_counties_simple --states 21,47,51 --update-existing
```

### Import Cities
```bash
python manage.py import_cities_simple --states 21,47,51 --update-existing
```

## Troubleshooting

### Common Issues

1. **GIS Not Enabled**
   ```
   Error: GIS is not enabled. Set GIS_ENABLED=1 in your environment.
   ```
   **Solution**: Ensure `GIS_ENABLED=1` is set in your environment.

2. **Virtual Environment Not Found**
   ```
   Error: Virtual environment not found.
   ```
   **Solution**: Create virtual environment with `python -m venv venv`

3. **ogr2ogr Not Found**
   ```
   Error: ogr2ogr command not found
   ```
   **Solution**: Install GDAL/OGR tools on your system

4. **Download Failures**
   ```
   Error: HTTP Error 404: Not Found
   ```
   **Solution**: Check if the TIGER/Line year is available, try a different year

### Log Files
The script creates a log file `geographic_data_update.log` in the project root with detailed information about the import process.

## Performance Considerations

### Data Sizes
- **States**: ~56 records, very fast
- **Counties**: ~3,200 records, moderate time
- **Cities**: ~40,000 records, longer time

### Memory Usage
- The script processes data in chunks to minimize memory usage
- Large imports may take significant time and memory

### Network Usage
- Downloads can be large (several GB for full US data)
- Consider running during off-peak hours for large imports

## Best Practices

1. **Regular Updates**: Run `--update-existing` monthly or quarterly
2. **Backup First**: Always backup your database before major updates
3. **Test Environment**: Test updates in a development environment first
4. **Monitor Logs**: Check the log file for any errors or warnings
5. **Verify Data**: After import, verify data quality and completeness

## Examples

### Daily Operations
```bash
# Check current data status
./scripts/update_data.sh --status-only

# Update existing data with latest boundaries
./scripts/update_data.sh --update-existing
```

### Initial Setup
```bash
# Import Kentucky and surrounding states
./scripts/update_data.sh

# Import all US data (takes longer)
./scripts/update_data.sh --all-states
```

### Maintenance
```bash
# Update to latest TIGER/Line year
./scripts/update_data.sh --year 2024 --update-existing

# Complete reset (use with caution)
./scripts/update_data.sh --all-states --clear-existing
```
