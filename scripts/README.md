# Scripts Directory

This directory contains utility scripts for managing the resource directory system.

## Geographic Data Management

The `geo_manager.py` script provides a beautiful, user-friendly CLI for managing geographic data with rich progress bars and status updates.

### Usage

```bash
# Navigate to the project root
cd /home/stewood/rl

# Activate the virtual environment
source venv/bin/activate

# Check current geographic data status
python scripts/geo_manager.py status

# Import Kentucky region (all states + KY + bordering states counties/cities)
python scripts/geo_manager.py kentucky-region --clear-existing

# Populate data for specific states
python scripts/geo_manager.py populate --states KY,IN,OH

# Populate data for all states
python scripts/geo_manager.py populate --states all

# Clear all geographic data
python scripts/geo_manager.py clear

# Update existing data for specific states
python scripts/geo_manager.py update --states KY --year 2023

# Show help
python scripts/geo_manager.py help
```

### Available Commands

#### Status
```bash
python scripts/geo_manager.py status
```
Shows current geographic data status with counts of states, counties, and cities.

#### Kentucky Region Import
```bash
python scripts/geo_manager.py kentucky-region [--clear-existing]
```
Imports all states plus counties and cities for Kentucky and its bordering states:
- Kentucky (KY)
- Indiana (IN)
- Illinois (IL)
- Missouri (MO)
- Tennessee (TN)
- Virginia (VA)
- West Virginia (WV)
- Ohio (OH)

This is the recommended command for a complete regional dataset.

#### Populate Data
```bash
python scripts/geo_manager.py populate --states STATE1,STATE2 [--clear-existing]
```
Populates geographic data for specific states.

**Examples:**
```bash
python scripts/geo_manager.py populate --states KY,IN,OH
python scripts/geo_manager.py populate --states all
```

#### Clear Data
```bash
python scripts/geo_manager.py clear
```
Clears all geographic data from the database.

#### Update Data
```bash
python scripts/geo_manager.py update --states STATE1,STATE2 [--year YEAR]
```
Updates existing geographic data for specific states.

**Examples:**
```bash
python scripts/geo_manager.py update --states KY --year 2023
```

### Features

- **Beautiful UI**: Rich progress bars and colored output
- **Real-time Progress**: Shows actual progress with ETA for downloads and imports
- **Optimized Downloads**: Downloads files only once when possible
- **Error Handling**: Clear error messages and graceful failure handling
- **Non-interactive**: Runs without requiring user confirmation
- **Comprehensive**: Handles states, counties, and cities in one tool

### State Abbreviations

The tool accepts both state abbreviations and FIPS codes:
- `KY` or `21` for Kentucky
- `IN` or `18` for Indiana
- `OH` or `39` for Ohio
- etc.

## Service Area Management Script

The `manage_service_areas.py` script provides a command-line interface for managing service areas for resources.

### Usage

```bash
# Navigate to the scripts directory
cd scripts

# Activate the virtual environment
source ../venv/bin/activate

# Run the script with various commands
python manage_service_areas.py [command] [options]
```

### Available Commands

#### Add Service Area
```bash
python manage_service_areas.py add <resource_id> <coverage_area_id>
```
Adds a service area to a resource.

**Example:**
```bash
python manage_service_areas.py add 54 27  # Add Kentucky to kynect Health Coverage
```

#### Remove Service Area
```bash
python manage_service_areas.py remove <resource_id> <coverage_area_id>
```
Removes a service area from a resource.

**Example:**
```bash
python manage_service_areas.py remove 54 27  # Remove Kentucky from kynect Health Coverage
```

#### List Service Areas
```bash
python manage_service_areas.py list <resource_id>
```
Lists all service areas for a specific resource.

**Example:**
```bash
python manage_service_areas.py list 54  # Show service areas for resource 54
```

#### Find Resource Without Service Areas
```bash
python manage_service_areas.py find-without-areas
```
Finds and displays detailed information about a resource that doesn't have any service areas configured.

#### Get Resource Details
```bash
python manage_service_areas.py details <resource_id>
```
Gets comprehensive details about a specific resource, including all its service areas.

**Example:**
```bash
python manage_service_areas.py details 54  # Get full details for resource 54
```

#### List Coverage Areas
```bash
python manage_service_areas.py list-coverage-areas [--kind KIND] [--limit LIMIT]
```
Lists available coverage areas in the system.

**Options:**
- `--kind`: Filter by coverage area type (CITY, COUNTY, STATE, POLYGON, RADIUS)
- `--limit`: Maximum number of results to show (default: 20)

**Examples:**
```bash
python manage_service_areas.py list-coverage-areas --kind STATE --limit 10
python manage_service_areas.py list-coverage-areas --kind COUNTY
```

### Coverage Area Types

The system supports these types of service areas:
- **CITY**: Municipal boundaries (e.g., "London, KY")
- **COUNTY**: County boundaries (e.g., "Laurel County")
- **STATE**: State boundaries (e.g., "Kentucky")
- **POLYGON**: Custom drawn boundaries
- **RADIUS**: Circular areas around a specific point

### Examples

1. **Add Kentucky state coverage to a resource:**
   ```bash
   python manage_service_areas.py add 54 27
   ```

2. **Find a resource that needs service areas:**
   ```bash
   python manage_service_areas.py find-without-areas
   ```

3. **List all state coverage areas:**
   ```bash
   python manage_service_areas.py list-coverage-areas --kind STATE
   ```

4. **Get full details about a resource:**
   ```bash
   python manage_service_areas.py details 54
   ```

### Notes

- The script automatically handles audit trails through the ResourceCoverage through model
- All changes are logged with the user who made them and timestamps
- The script includes error handling and validation
- Make sure to run from the scripts directory with the virtual environment activated
