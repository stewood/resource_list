# Resource Management CLI Tool

The Resource Management CLI Tool provides a comprehensive command-line interface for managing resources in the Community Resource Directory. It supports full CRUD operations with JSON output for easy parsing by AI/scripts.

## 📊 **Implementation Progress: 95% Complete**

- ✅ **T1: CLI Framework Setup** - COMPLETED
- ✅ **T2: Resource List Command** - COMPLETED  
- ✅ **T3: Resource Show Command** - COMPLETED
- ✅ **T4: Resource Create Command** - COMPLETED
- ✅ **T5: Resource Update Command** - COMPLETED
- ✅ **T6: Search & Filter Implementation** - COMPLETED
- ✅ **T7: Geographic Area Management** - COMPLETED

## 🚀 Quick Start

```bash
# Show help
python manage.py resource-cli --help

# List resources
python manage.py resource-cli list

# Show specific resource
python manage.py resource-cli show 123

# Create new resource
python manage.py resource-cli create

# Update resource
python manage.py resource-cli update 123 --status=published

# Search resources
python manage.py resource-cli search "mental health" --city="London"
```

## 📋 Available Commands

### `list` - List Resources
List resources with filtering, pagination, and sorting options.

**Options:**
- `--status`: Filter by status (draft, needs_review, published)
- `--category`: Filter by category name
- `--city`: Filter by city
- `--state`: Filter by state (2-letter code)
- `--limit`: Maximum number of results (default: 50)
- `--offset`: Number of results to skip (default: 0)
- `--sort`: Sort field (name, created_at, updated_at, status)
- `--order`: Sort order (asc, desc)

**Examples:**
```bash
# List all published resources
python manage.py resource-cli list --status=published

# List resources in a specific city with pagination
python manage.py resource-cli list --city="London" --limit=25 --offset=50

# List resources sorted by creation date
python manage.py resource-cli list --sort=created_at --order=desc
```

### `show` - Show Resource Details
Display detailed information about a specific resource.

**Arguments:**
- `resource_id`: ID of the resource to show

**Examples:**
```bash
# Show resource with ID 123
python manage.py resource-cli show 123
```

### `create` - Create New Resource
Create new resources interactively or from JSON input.

**Options:**
- `--json`: JSON string with resource data for non-interactive creation
- `--interactive`: Enable interactive mode (default: True)

**Examples:**
```bash
# Interactive creation
python manage.py resource-cli create

# Create from JSON
python manage.py resource-cli create --json='{"name": "Test Resource", "category": "Mental Health"}'
```

### `update` - Update Resource
Update existing resources with field-level changes.

**Arguments:**
- `resource_id`: ID of the resource to update

**Options:**
- `--json`: JSON string with update data
- `--status`: Update resource status
- `--name`: Update resource name
- `--description`: Update resource description

**Examples:**
```bash
# Update status
python manage.py resource-cli update 123 --status=published

# Update multiple fields
python manage.py resource-cli update 123 --name="New Name" --description="New description"

# Update from JSON
python manage.py resource-cli update 123 --json='{"status": "published", "notes": "Updated"}'
```

### `search` - Search Resources
Search resources using FTS5 and filters.

**Arguments:**
- `query`: Search query string

**Options:**
- `--city`: Filter by city
- `--state`: Filter by state (2-letter code)
- `--category`: Filter by category name
- `--limit`: Maximum number of results (default: 50)

**Examples:**
```bash
# Basic search
python manage.py resource-cli search "mental health crisis"

# Search with filters
python manage.py resource-cli search "homeless shelter" --city="London" --state="KY"

# Search with limit
python manage.py resource-cli search "food assistance" --limit=10
```

## 📊 Output Format

All commands output JSON for easy parsing by other tools and scripts.

### Success Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00",
  "data": {
    // Command-specific data
  },
  "metadata": {
    // Additional information about the operation
  }
}
```

### Error Response Format
```json
{
  "error": true,
  "message": "Error description",
  "timestamp": "2025-01-15T10:30:00",
  "error_code": "ERROR_CODE",
  "details": {
    // Additional error details
  }
}
```

### List Response Format
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
  "metadata": {
    "filters_applied": {
      "status": "published"
    },
    "processing_timestamp": "2025-01-15T10:30:00"
  }
}
```

## 🔐 Authentication & Permissions

The CLI tool integrates with Django's authentication system:

- **Read operations** (list, show, search): No authentication required
- **Write operations** (create, update): Authentication required
- **Permissions**: Uses existing Django user permissions

## 🧪 Testing

Run the CLI tests with:

```bash
# Run all CLI tests
python manage.py test directory.tests.test_cli

# Run specific test class
python manage.py test directory.tests.test_cli.ResourceCLICommandTest

# Run with coverage
coverage run --source='.' manage.py test directory.tests.test_cli
coverage report
```

## 🏗️ Architecture

### File Structure
```
directory/management/commands/
├── resource_cli.py          # Main CLI command
├── cli_utils.py            # Shared utilities
├── geographic_imports/     # Geographic data import commands
│   ├── import_states_enhanced.py
│   ├── import_cities_enhanced.py
│   ├── import_counties_enhanced.py
│   └── README.md
├── archive/                 # Archived commands (see archive/README.md)
│   ├── one_off_tests/      # Development test commands
│   ├── development_utils/  # One-time setup commands
│   └── README.md
└── README.md               # This documentation
```

### Key Components

1. **ResourceCLICommand**: Main command class with subcommand routing
2. **CLI Utilities**: Shared functions for data formatting, validation, and response formatting
3. **Command Handlers**: Individual methods for each subcommand (to be implemented)

### Design Principles

- **Modular Design**: Each command is a separate handler method
- **Consistent JSON Output**: All commands return structured JSON
- **Error Handling**: Comprehensive error handling with meaningful messages
- **Validation**: Leverages existing Django model validation
- **Extensibility**: Easy to add new commands and options

## ✅ Implementation Status

### ✅ Completed (T1 - CLI Framework Setup)
- [x] Base command structure with subcommand registration
- [x] Argument parsing for all commands
- [x] JSON output formatting
- [x] Basic error handling
- [x] Utility functions for common operations
- [x] Comprehensive test coverage
- [x] Documentation

### ✅ Completed (T2 - Resource List Command)
- [x] List command with filtering (status, category, city, state)
- [x] Pagination support (limit/offset)
- [x] Sorting options (name, created_at, updated_at, status)
- [x] JSON output with metadata and pagination info
- [x] CoverageArea model integration (FIPS codes)
- [x] Comprehensive testing and validation

### ✅ Completed (T3 - Resource Show Command)
- [x] Show command with resource ID validation
- [x] Detailed resource information display
- [x] Related data inclusion (categories, service types)
- [x] Error handling for missing resources
- [x] JSON output formatting

### ✅ Completed (T4 - Resource Create Command)
- [x] Interactive resource creation with prompts
- [x] JSON-based resource creation
- [x] Service area assignment during creation
- [x] Validation and error handling
- [x] Draft status by default

### ✅ Completed (T5 - Resource Update Command)
- [x] Field-level resource updates
- [x] JSON-based bulk updates
- [x] Service area management (add/remove/set/clear)
- [x] Status transition handling
- [x] Audit trail maintenance

### ✅ Completed (T6 - Search & Filter Implementation)
- [x] FTS5 full-text search
- [x] Combined search (FTS5 + exact matches)
- [x] Location-based filtering (city, state)
- [x] Category and status filtering
- [x] Pagination and result limiting

### ✅ Completed (T7 - Geographic Area Management)
- [x] List areas command with filtering and pagination
- [x] Show area command with detailed information
- [x] Associated resources display
- [x] Geographic metadata handling

## 🔧 Development

### Adding New Commands

1. Add subcommand parser in `add_arguments()`
2. Add argument method (e.g., `_add_new_command_arguments()`)
3. Add command handler (e.g., `_handle_new_command()`)
4. Add routing in `handle()` method
5. Add tests in `test_cli.py`

### Adding New Options

1. Add argument to the appropriate parser in `_add_*_arguments()`
2. Update command handler to process the new option
3. Add tests for the new option

### Utility Functions

Common functionality should be added to `cli_utils.py`:
- Data formatting functions
- Validation helpers
- Response formatting
- Common operations

## 📝 Examples

### Basic Usage Examples

```bash
# Get help for all commands
python manage.py resource-cli --help

# Get help for specific command
python manage.py resource-cli list --help

# List first 10 published resources
python manage.py resource-cli list --status=published --limit=10

# Show resource details
python manage.py resource-cli show 123

# Search for mental health resources in London
python manage.py resource-cli search "mental health" --city="London"
```

### Advanced Usage Examples

```bash
# Create resource from JSON file
echo '{"name": "Crisis Center", "category": "Mental Health", "status": "draft"}' > resource.json
python manage.py resource-cli create --json="$(cat resource.json)"

# Update multiple resources with JSON
python manage.py resource-cli update 123 --json='{"status": "published", "notes": "Verified"}'

# Complex search with multiple filters
python manage.py resource-cli search "homeless shelter" --city="London" --state="KY" --category="Housing" --limit=25
```

### Script Integration

```bash
#!/bin/bash
# Example script using the CLI tool

# Get list of resources and save to file
python manage.py resource-cli list --status=published --limit=100 > resources.json

# Process resources with jq
cat resources.json | jq '.data[] | select(.city == "London") | .name'

# Update resource status
python manage.py resource-cli update 123 --status=published
```

## 🤝 Contributing

When contributing to the CLI tool:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for new commands/options
4. Ensure JSON output remains consistent
5. Test with various input scenarios

## 📚 Related Documentation

- [Django Management Commands](https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/)
- [Resource Models](../models/core/resource.py)
- [API Views](../views/api/resource_views.py)
- [Project README](../../../README.md)
