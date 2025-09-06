# Resource Management CLI Documentation

## 📋 Overview

The Resource Management CLI (`resource_cli`) is a comprehensive command-line interface for managing resources in the Community Resource Directory. This tool provides full CRUD operations, advanced search capabilities, and geographic area management through a JSON-based interface.

**Target Audience**: Data managers, administrators, and staff who need to review, create, update, and manage resource records.

## 🚀 Quick Start

```bash
# Show general help
python manage.py resource_cli --help

# Show help for a specific command
python manage.py resource_cli list --help
python manage.py resource_cli create --help
python manage.py resource_cli update --help
```

## 📊 Available Commands

### 1. **`list`** - List Resources
Display resources with filtering, pagination, and sorting options.

**Basic Usage:**
```bash
python manage.py resource_cli list
```

**With Filters:**
```bash
# Filter by status
python manage.py resource_cli list --status=published

# Filter by location
python manage.py resource_cli list --city="London" --state="KY"

# Filter by category
python manage.py resource_cli list --category="Mental Health"

# Combine filters
python manage.py resource_cli list --status=published --city="London" --state="KY"
```

**Pagination and Sorting:**
```bash
# Pagination
python manage.py resource_cli list --limit=25 --offset=50

# Sorting
python manage.py resource_cli list --sort=created_at --order=desc
python manage.py resource_cli list --sort=name --order=asc
```

**Available Options:**
- `--status`: Filter by status (`draft`, `needs_review`, `published`)
- `--category`: Filter by category name (e.g., "Mental Health", "Housing")
- `--city`: Filter by city name (e.g., "London", "Lexington")
- `--state`: Filter by state using 2-letter code (e.g., "KY", "TN")
- `--limit`: Maximum results per page (default: 50, max: 1000)
- `--offset`: Number of results to skip (default: 0)
- `--sort`: Sort field (`name`, `created_at`, `updated_at`, `status`)
- `--order`: Sort order (`asc`, `desc`)

### 2. **`show`** - Display Resource Details
Show comprehensive information about a specific resource by ID.

**Usage:**
```bash
python manage.py resource_cli show 123
```

**What It Shows:**
- Basic resource information (name, description, status)
- Contact details (phone, email, website)
- Location information (address, city, state, county)
- Service details (hours, eligibility, populations served)
- Coverage areas and service types
- Audit information (created/updated dates, users)

### 3. **`create`** - Create New Resources
Create new resources interactively or from JSON input.

**Interactive Mode (Default):**
```bash
python manage.py resource_cli create
```

**JSON Mode:**
```bash
python manage.py resource_cli create --json='{"name":"Crisis Center","city":"London","state":"KY"}'
```

**With Service Areas:**
```bash
python manage.py resource_cli create --json='{"name":"Test Resource"}' --service-areas="Kentucky,London KY"
```

**Available Options:**
- `--json`: JSON string with resource data
- `--interactive`: Enable interactive mode (default: True)
- `--service-areas`: Comma-separated service area names/IDs
- `--no-interactive-areas`: Disable service area prompts

**Required Fields:**
- `name`: Resource name
- `category`: Service category (selected from available options)

**JSON Format Example:**
```json
{
  "name": "Crisis Center",
  "description": "24/7 mental health crisis intervention",
  "city": "London",
  "state": "KY",
  "phone": "555-1234",
  "email": "crisis@example.com",
  "is_emergency_service": true,
  "is_24_hour_service": true,
  "service_areas": ["Kentucky", "London KY"]
}
```

### 4. **`update`** - Update Existing Resources
Update existing resources with field-level changes or bulk updates.

**Individual Field Updates:**
```bash
# Update status
python manage.py resource_cli update 123 --status=published

# Update contact information
python manage.py resource_cli update 123 --phone="555-9876" --city="Lexington"

# Update service flags
python manage.py resource_cli update 123 --is_emergency_service=true
```

**Bulk Updates with JSON:**
```bash
python manage.py resource_cli update 123 --json='{"status":"published","phone":"555-1234","notes":"Updated contact info"}'
```

**Service Area Management:**
```bash
# Add service areas
python manage.py resource_cli update 123 --add-areas="Kentucky,Laurel County"

# Remove service areas
python manage.py resource_cli update 123 --remove-areas="London KY"

# Replace all service areas
python manage.py resource_cli update 123 --set-areas="Kentucky,Laurel County"

# Clear all service areas
python manage.py resource_cli update 123 --clear-areas
```

**Available Update Fields:**
- **Basic Info**: `--name`, `--description`, `--status`
- **Contact**: `--phone`, `--email`, `--website`
- **Location**: `--address1`, `--address2`, `--city`, `--state`, `--county`, `--postal_code`
- **Services**: `--hours_of_operation`, `--eligibility_requirements`, `--populations_served`
- **Flags**: `--is_emergency_service`, `--is_24_hour_service`
- **Additional**: `--insurance_accepted`, `--cost_information`, `--languages_available`, `--capacity`, `--source`, `--notes`

**Status Workflow:**
- `draft` → `needs_review` → `published`
- Resources start as `draft` by default
- Only `published` resources are visible to the public

### 5. **`search`** - Search Resources
Search resources using FTS5 full-text search with advanced filtering.

**Basic Search:**
```bash
python manage.py resource_cli search "mental health"
```

**Search with Filters:**
```bash
# Location-based search
python manage.py resource_cli search "crisis intervention" --city="London"

# Category and status filtering
python manage.py resource_cli search "addiction treatment" --category="Mental Health" --status=published

# Multiple filters
python manage.py resource_cli search "health services" --city="Lexington" --state="KY" --limit=10
```

**Search Methods:**
- **FTS5**: Full-text search across names, descriptions, and content
- **Exact**: Phone, email, website, and postal code matching
- **Combined**: Results from both methods with deduplication

**Available Options:**
- `query`: Search query string (required)
- `--city`: Filter by city name
- `--state`: Filter by state (2-letter code)
- `--category`: Filter by category name
- `--status`: Filter by resource status
- `--limit`: Maximum results (default: 50, max: 1000)

### 6. **`list-areas`** - List Service Areas
List available coverage areas with filtering and pagination.

**Basic Usage:**
```bash
python manage.py resource_cli list-areas
```

**With Filters:**
```bash
# Filter by type
python manage.py resource_cli list-areas --kind=COUNTY

# Search by name
python manage.py resource_cli list-areas --search="Kentucky"

# Pagination and sorting
python manage.py resource_cli list-areas --kind=COUNTY --limit=25 --sort=name --order=asc
```

**Available Options:**
- `--kind`: Filter by area type (`CITY`, `COUNTY`, `STATE`, `POLYGON`, `RADIUS`)
- `--search`: Search for areas containing text in name
- `--limit`: Maximum results per page (default: 50)
- `--offset`: Number of results to skip
- `--sort`: Sort field (`name`, `kind`, `created_at`, `updated_at`)
- `--order`: Sort order (`asc`, `desc`)

### 7. **`show-area`** - Show Area Details
Display detailed information about a specific coverage area.

**Usage:**
```bash
python manage.py resource_cli show-area 27
```

**What It Shows:**
- Area information (name, type, geometry)
- External identifiers (FIPS codes)
- Associated resources
- Creation and update metadata

## 📝 Data Format and Structure

### Resource Fields

**Basic Information:**
- `id`: Unique resource identifier
- `name`: Resource name (required)
- `description`: Detailed description
- `status`: Current status (`draft`, `needs_review`, `published`)

**Contact Information:**
- `phone`: Phone number (automatically formatted)
- `email`: Email address
- `website`: Website URL

**Location:**
- `address1`, `address2`: Street address
- `city`: City name
- `state`: State (2-letter code)
- `county`: County name
- `postal_code`: ZIP/postal code

**Service Details:**
- `hours_of_operation`: Operating hours
- `is_emergency_service`: Emergency service flag
- `is_24_hour_service`: 24-hour service flag
- `eligibility_requirements`: Who can use the service
- `populations_served`: Target populations
- `insurance_accepted`: Insurance information
- `cost_information`: Cost details
- `languages_available`: Available languages
- `capacity`: Service capacity

**Metadata:**
- `source`: Data source
- `notes`: Additional notes
- `verification_frequency_days`: How often to verify
- `created_at`, `updated_at`: Timestamps
- `created_by`, `updated_by`: User information

### Service Areas

**Types:**
- `STATE`: State-level coverage
- `COUNTY`: County-level coverage
- `CITY`: City-level coverage
- `POLYGON`: Custom geographic boundaries
- `RADIUS`: Circular coverage areas

**Identification:**
- Can be specified by name (e.g., "Kentucky", "London KY")
- Can be specified by ID (e.g., "27", "42")
- FIPS codes are automatically handled

## 🔧 Advanced Usage Examples

### Bulk Operations

**Create Multiple Resources:**
```bash
# Create from JSON file
echo '{"name":"Resource 1","city":"London"}' > resource1.json
python manage.py resource_cli create --json="$(cat resource1.json)"

# Create with service areas
python manage.py resource_cli create --json='{"name":"Resource 2"}' --service-areas="Kentucky,Laurel County"
```

**Update Multiple Fields:**
```bash
# Update status and contact info
python manage.py resource_cli update 123 --status=published --phone="555-1234" --notes="Verified and updated"

# Bulk update from JSON
python manage.py resource_cli update 123 --json='{"status":"published","phone":"555-1234","notes":"Updated"}'
```

### Data Validation and Quality

**Check Resource Status:**
```bash
# List all draft resources
python manage.py resource_cli list --status=draft

# List resources needing review
python manage.py resource_cli list --status=needs_review

# List published resources
python manage.py resource_cli list --status=published
```

**Geographic Filtering:**
```bash
# Resources in specific city
python manage.py resource_cli list --city="London" --state="KY"

# Resources in specific county
python manage.py resource_cli list --city="London" --state="KY"

# Resources by state
python manage.py resource_cli list --state="KY"
```

### Search and Discovery

**Find Specific Services:**
```bash
# Emergency services
python manage.py resource_cli search "emergency" --status=published

# Mental health resources
python manage.py resource_cli search "mental health crisis" --city="London"

# 24-hour services
python manage.py resource_cli search "24 hour" --status=published
```

**Category-Based Search:**
```bash
# Housing resources
python manage.py resource_cli list --category="Housing"

# Food assistance
python manage.py resource_cli search "food" --category="Food Assistance"
```

## 📊 Output Format

All commands output JSON with consistent structure:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00",
  "data": {
    // Command-specific data
  },
  "metadata": {
    // Additional information
  }
}
```

**Error Response:**
```json
{
  "error": true,
  "message": "Error description",
  "timestamp": "2025-01-15T10:30:00"
}
```

**List Response with Pagination:**
```json
{
  "data": [
    // Array of resource objects
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 150,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "status": "published"
  }
}
```

## 🚨 Common Issues and Solutions

### Authentication Errors
- **Problem**: "Authentication required for write operations"
- **Solution**: Ensure you're running the command in an authenticated environment

### Resource Not Found
- **Problem**: "Resource with ID 123 not found"
- **Solution**: Verify the resource ID exists using `python manage.py resource_cli list`

### Invalid Status Transitions
- **Problem**: Cannot update status from `draft` to `published`
- **Solution**: Use intermediate status: `draft` → `needs_review` → `published`

### Service Area Issues
- **Problem**: "Service area 'Unknown Area' not found"
- **Solution**: Use `python manage.py resource_cli list-areas` to see available areas

### JSON Parsing Errors
- **Problem**: "Invalid JSON input"
- **Solution**: Validate JSON syntax and ensure proper escaping of quotes

## 🔍 Best Practices

### For Data Entry
1. **Start with Draft Status**: Create resources as drafts first
2. **Use Interactive Mode**: Use interactive creation for new resources
3. **Validate Service Areas**: Check available areas before assignment
4. **Complete Required Fields**: Ensure name and category are provided

### For Updates
1. **Check Current Status**: Use `show` command to see current state
2. **Follow Status Workflow**: Respect the draft → needs_review → published flow
3. **Use JSON for Bulk Updates**: Use JSON input for multiple field changes
4. **Maintain Audit Trail**: Updates are automatically tracked

### For Search and Discovery
1. **Use Specific Terms**: Be specific in search queries
2. **Combine Filters**: Use multiple filters for precise results
3. **Check Pagination**: Use limit/offset for large result sets
4. **Verify Results**: Use `show` command to verify resource details

## 📚 Related Documentation

- **Models**: `directory/models/core/resource.py`
- **API Views**: `directory/views/api/resource_views.py`
- **CLI Utilities**: `directory/management/commands/cli_utils.py`
- **Project README**: `README.md`

## 🆘 Getting Help

**Command Help:**
```bash
python manage.py resource_cli --help
python manage.py resource_cli <command> --help
```

**Examples:**
```bash
# See all available examples
python manage.py resource_cli --help

# See examples for specific command
python manage.py resource_cli create --help
```

**Error Messages:**
- All errors include descriptive messages
- Check the error message for specific guidance
- Use `--help` for command-specific options

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Maintained by**: Resource Directory Team
