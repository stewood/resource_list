# Scripts Directory

This directory contains utility scripts for managing the resource directory system, organized by functionality.

## Directory Structure

```
scripts/
├── development/     # Development and testing scripts
├── deployment/      # Deployment and environment setup scripts
├── data/           # Data management and migration scripts
├── geo/            # Geographic data management (refactored)
├── migrations/     # Database migration scripts
├── backup/         # Backup and restore scripts
└── README.md       # This documentation
```

## Development Scripts (`development/`)

Scripts for development workflow, testing, and development environment management.

### Available Scripts

- **`analyze_dependencies.py`** - Analyze code dependencies and create dependency reports
- **`cache_manager.py`** - Manage application cache and cache-related operations
- **`run_tests.py`** - Run test suites and generate test reports
- **`setup_dev_environment.sh`** - Set up development environment
- **`start_dev.sh`** - Start development server and services
- **`reset_dev_environment.sh`** - Reset development environment to clean state

### Usage Examples

```bash
# Run dependency analysis
python scripts/development/analyze_dependencies.py

# Manage cache
python scripts/development/cache_manager.py

# Set up development environment
./scripts/development/setup_dev_environment.sh

# Start development server
./scripts/development/start_dev.sh
```

## Deployment Scripts (`deployment/`)

Scripts for deploying the application to different environments.

### Available Scripts

- **`deploy_to_staging.sh`** - Deploy application to staging environment
- **`setup_gis.sh`** - Set up GIS components for deployment

### Usage Examples

```bash
# Deploy to staging
./scripts/deployment/deploy_to_staging.sh

# Set up GIS for deployment
./scripts/deployment/setup_gis.sh
```

## Data Scripts (`data/`)

Scripts for managing data, migrations, and data-related operations.

### Available Scripts

- **`restore_resource_coverage.py`** - Restore resource coverage data
- **`update_existing_resources.py`** - Update existing resource data
- **`manage_service_areas.py`** - Manage service areas for resources
- **`init-db.sql`** - Database initialization SQL script
- **`migrate_sqlite_to_dev.sh`** - Migrate data from SQLite to development environment
- **`update_data.sh`** - Update data in the system
- **`reset_admin_password.py`** - Reset admin user password
- **`find_next_verification.py`** - Find resources needing verification
- **`create_national_coverage.py`** - Create national coverage areas

### Usage Examples

```bash
# Restore resource coverage
python scripts/data/restore_resource_coverage.py

# Update existing resources
python scripts/data/update_existing_resources.py

# Manage service areas
python scripts/data/manage_service_areas.py add 54 27

# Initialize database
psql -f scripts/data/init-db.sql

# Migrate from SQLite
./scripts/data/migrate_sqlite_to_dev.sh

# Reset admin password
python scripts/data/reset_admin_password.py
```

## Geographic Data Management (`geo/`)

The geographic data management system has been refactored into a modular structure.

### Available Scripts

- **`manager.py`** - Main geographic data manager CLI
- **`operations/`** - Geographic operations (populate, clear, update, status)
- **`utils/`** - Geographic utilities (cache, validation)

### Usage

```bash
# Navigate to the project root
cd /home/stewood/rl

# Activate the virtual environment
source venv/bin/activate

# Check current geographic data status
python scripts/geo/manager.py status

# Import Kentucky region (all states + KY + bordering states counties/cities)
python scripts/geo/manager.py kentucky-region --clear-existing

# Populate data for specific states
python scripts/geo/manager.py populate --states KY,IN,OH

# Populate data for all states
python scripts/geo/manager.py populate --states all

# Clear all geographic data
python scripts/geo/manager.py clear

# Update existing data for specific states
python scripts/geo/manager.py update --states KY --year 2023

# Show help
python scripts/geo/manager.py help
```

### Available Commands

#### Status
```bash
python scripts/geo/manager.py status
```
Shows current geographic data status with counts of states, counties, and cities.

#### Kentucky Region Import
```bash
python scripts/geo/manager.py kentucky-region [--clear-existing]
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
python scripts/geo/manager.py populate --states STATE1,STATE2 [--clear-existing]
```
Populates geographic data for specific states.

**Examples:**
```bash
python scripts/geo/manager.py populate --states KY,IN,OH
python scripts/geo/manager.py populate --states all
```

#### Clear Data
```bash
python scripts/geo/manager.py clear
```
Clears all geographic data from the database.

#### Update Data
```bash
python scripts/geo/manager.py update --states STATE1,STATE2 [--year YEAR]
```
Updates existing geographic data for specific states.

**Examples:**
```bash
python scripts/geo/manager.py update --states KY --year 2023
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

## Service Area Management

The `manage_service_areas.py` script provides a command-line interface for managing service areas for resources.

### Usage

```bash
# Navigate to the scripts directory
cd scripts

# Activate the virtual environment
source ../venv/bin/activate

# Run the script with various commands
python data/manage_service_areas.py [command] [options]
```

### Available Commands

#### Add Service Area
```bash
python data/manage_service_areas.py add <resource_id> <coverage_area_id>
```
Adds a service area to a resource.

**Example:**
```bash
python data/manage_service_areas.py add 54 27  # Add Kentucky to kynect Health Coverage
```

#### Remove Service Area
```bash
python data/manage_service_areas.py remove <resource_id> <coverage_area_id>
```
Removes a service area from a resource.

**Example:**
```bash
python data/manage_service_areas.py remove 54 27  # Remove Kentucky from kynect Health Coverage
```

#### List Service Areas
```bash
python data/manage_service_areas.py list <resource_id>
```
Lists all service areas for a specific resource.

**Example:**
```bash
python data/manage_service_areas.py list 54  # Show service areas for resource 54
```

#### Find Resource Without Service Areas
```bash
python data/manage_service_areas.py find-without-areas
```
Finds and displays detailed information about a resource that doesn't have any service areas configured.

#### Get Resource Details
```bash
python data/manage_service_areas.py details <resource_id>
```
Gets comprehensive details about a specific resource, including all its service areas.

**Example:**
```bash
python data/manage_service_areas.py details 54  # Get full details for resource 54
```

#### List Coverage Areas
```bash
python data/manage_service_areas.py list-coverage-areas [--kind KIND] [--limit LIMIT]
```
Lists available coverage areas in the system.

**Options:**
- `--kind`: Filter by coverage area type (CITY, COUNTY, STATE, POLYGON, RADIUS)
- `--limit`: Maximum number of results to show (default: 20)

**Examples:**
```bash
python data/manage_service_areas.py list-coverage-areas --kind STATE --limit 10
python data/manage_service_areas.py list-coverage-areas --kind COUNTY
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
   python data/manage_service_areas.py add 54 27
   ```

2. **Find a resource that needs service areas:**
   ```bash
   python data/manage_service_areas.py find-without-areas
   ```

3. **List all state coverage areas:**
   ```bash
   python data/manage_service_areas.py list-coverage-areas --kind STATE
   ```

4. **Get full details about a resource:**
   ```bash
   python data/manage_service_areas.py details 54
   ```

### Notes

- The script automatically handles audit trails through the ResourceCoverage through model
- All changes are logged with the user who made them and timestamps
- The script includes error handling and validation
- Make sure to run from the scripts directory with the virtual environment activated
