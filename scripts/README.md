# Scripts Directory

This directory contains utility scripts for managing the resource directory system.

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

## Geographic Data Update Script

The `update_geographic_data.py` script manages TIGER/Line data imports and now includes automatic maintenance of national coverage areas.

### Usage

```bash
# Navigate to the project root
cd /home/stewood/rl

# Activate the virtual environment
source venv/bin/activate

# Check current data status (includes national coverage areas)
python scripts/update_geographic_data.py --status-only

# Update existing data (maintains national coverage areas)
python scripts/update_geographic_data.py --update-existing

# Import all states (creates and maintains national coverage areas)
python scripts/update_geographic_data.py --all-states

# Clear and reimport all data
python scripts/update_geographic_data.py --all-states --clear-existing
```

### National Coverage Area Integration

The geographic data update script now automatically:

1. **Maintains National Coverage Areas**: After importing state data, it updates the metadata for national coverage areas
2. **Tracks Updates**: Records when national coverage areas were last updated
3. **Validates Coverage**: Ensures national coverage areas exist and are properly configured
4. **Reports Status**: Shows national coverage area status in data status reports

### National Coverage Areas Maintained

- **National (Lower 48 States)** - ID: 7854
- **United States (All States and Territories)** - ID: 7855

These areas are automatically updated with metadata including:
- `last_updated`: Timestamp of last maintenance
- `available_states`: Count of available states in database
- `update_source`: Source of the update (geographic_data_update)

### Integration with TIGER/Line Updates

When you run geographic data updates, the system will:
1. Import/update individual state, county, and city boundaries
2. Automatically maintain national coverage area metadata
3. Report the status of all coverage areas including national ones
4. Warn if national coverage areas are missing

This ensures that your national coverage areas stay synchronized with your underlying geographic data.
