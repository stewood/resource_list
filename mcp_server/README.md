# Community Resource Directory MCP Server

A Model Context Protocol (MCP) server for the Community Resource Directory, providing AI/LLM access to resource management functionality while maintaining complete separation from the main Django application.

## 🎯 Overview

This MCP server enables AI assistants and LLMs to interact with the Community Resource Directory database through a standardized protocol. It provides comprehensive access to:

- **Resource CRUD Operations**: Create, read, update, and archive resources
- **Advanced Search**: Full-text search with FTS5 integration
- **Taxonomy Management**: Access to categories and service types
- **Static Resources**: Read-only data for categories and service types
- **Dynamic Resources**: Individual resource templates
- **Audit Trail**: Complete change tracking and history

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Django project with Community Resource Directory models
- Virtual environment activated

### Installation

1. **Install FastMCP**:
   ```bash
   pip install fastmcp==2.0.0
   ```

2. **Verify Installation**:
   ```bash
   python test_mcp_server.py
   ```

### Running the Server

#### Using FastMCP CLI
```bash
cd mcp_server
fastmcp run server.py
```

#### Using Python directly
```bash
cd mcp_server
python server.py
```

#### Using configuration file
```bash
cd mcp_server
fastmcp run fastmcp.json
```

## 🛠️ Available Tools

### Resource Management Tools

#### `create_resource_tool`
Create a new resource in the directory.

**Parameters:**
- `name` (str, required): Resource name
- `description` (str): Resource description
- `category_id` (int): Taxonomy category ID
- `service_type_ids` (list): List of service type IDs
- `phone` (str): Contact phone number
- `email` (str): Contact email address
- `website` (str): Resource website URL
- `address1` (str): Primary address line
- `address2` (str): Secondary address line
- `city` (str): City name
- `state` (str): State abbreviation (2 characters)
- `county` (str): County or parish name
- `postal_code` (str): ZIP or postal code
- `hours_of_operation` (str): Service hours and availability
- `is_emergency_service` (bool): Whether this is a crisis/emergency service
- `is_24_hour_service` (bool): Whether service is available 24/7
- `eligibility_requirements` (str): Qualification criteria
- `populations_served` (str): Target demographics
- `insurance_accepted` (str): Insurance plans accepted
- `cost_information` (str): Financial details
- `languages_available` (str): Languages supported
- `capacity` (str): Service capacity information
- `notes` (str): Internal notes (not visible to public)
- `created_by_user_id` (int): ID of the user creating the resource

#### `get_resource_tool`
Get detailed information about a specific resource.

**Parameters:**
- `resource_id` (int, required): ID of the resource to retrieve

#### `update_resource_tool`
Update an existing resource.

**Parameters:**
- `resource_id` (int, required): ID of the resource to update
- All other parameters are optional and will only update if provided

#### `archive_resource_tool`
Archive (soft delete) a resource.

**Parameters:**
- `resource_id` (int, required): ID of the resource to archive
- `archived_by_user_id` (int): ID of the user archiving the resource
- `reason` (str): Reason for archiving

#### `list_resources_tool`
List resources with optional filtering and pagination.

**Parameters:**
- `status` (str): Filter by status (draft, needs_review, published)
- `category_id` (int): Filter by category ID
- `service_type_id` (int): Filter by service type ID
- `city` (str): Filter by city name
- `state` (str): Filter by state abbreviation
- `is_emergency_service` (bool): Filter by emergency service flag
- `is_24_hour_service` (bool): Filter by 24-hour service flag
- `include_archived` (bool): Whether to include archived resources
- `limit` (int): Maximum number of results (default: 50, max: 100)
- `offset` (int): Number of results to skip for pagination

### Search Tools

#### `search_resources_tool`
Search resources using advanced search capabilities.

**Parameters:**
- `query` (str, required): Search query string
- `search_type` (str): Type of search (fts, exact, combined)
- `category_id` (int): Filter by category ID
- `service_type_id` (int): Filter by service type ID
- `city` (str): Filter by city name
- `state` (str): Filter by state abbreviation
- `county` (str): Filter by county name
- `is_emergency_service` (bool): Filter by emergency service flag
- `is_24_hour_service` (bool): Filter by 24-hour service flag
- `status` (str): Filter by status
- `limit` (int): Maximum number of results (default: 50, max: 100)
- `offset` (int): Number of results to skip for pagination

#### `search_emergency_services_tool`
Search for emergency and crisis services.

**Parameters:**
- `city` (str): Filter by city name
- `state` (str): Filter by state abbreviation
- `county` (str): Filter by county name
- `limit` (int): Maximum number of results (default: 50, max: 100)

#### `search_by_location_tool`
Search resources by geographic location.

**Parameters:**
- `city` (str): Filter by city name
- `state` (str): Filter by state abbreviation
- `county` (str): Filter by county name
- `category_id` (int): Filter by category ID
- `service_type_id` (int): Filter by service type ID
- `limit` (int): Maximum number of results (default: 50, max: 100)

### Taxonomy Tools

#### `list_categories_tool`
List all taxonomy categories with optional resource counts.

**Parameters:**
- `include_resource_count` (bool): Whether to include resource count for each category
- `published_only` (bool): Whether to count only published resources

#### `get_category_tool`
Get detailed information about a specific category.

**Parameters:**
- `category_id` (int, required): ID of the category to retrieve
- `include_resources` (bool): Whether to include list of resources in this category

#### `list_service_types_tool`
List service types with optional filtering and resource counts.

**Parameters:**
- `category_id` (int): Filter service types by category ID
- `include_resource_count` (bool): Whether to include resource count for each service type
- `published_only` (bool): Whether to count only published resources

#### `get_service_type_tool`
Get detailed information about a specific service type.

**Parameters:**
- `service_type_id` (int, required): ID of the service type to retrieve
- `include_resources` (bool): Whether to include list of resources with this service type

#### `get_taxonomy_summary_tool`
Get a summary of the taxonomy system.

**Parameters:** None

## 📚 Available Resources

### Static Resources

#### `resource://categories`
Static resource providing all taxonomy categories with resource counts.

#### `resource://service-types`
Static resource providing all service types with resource counts.

#### `resource://taxonomy-overview`
Static resource providing taxonomy overview with top categories and service types.

### Dynamic Resources

#### `resource://resource/{resource_id}`
Dynamic resource template for individual resources. Replace `{resource_id}` with the actual resource ID.

## 🔧 Configuration

### FastMCP Configuration

The server can be configured using `fastmcp.json`:

```json
{
  "$schema": "https://gofastmcp.com/schemas/fastmcp_config/v1.json",
  "entrypoint": {
    "file": "server.py",
    "object": "mcp"
  },
  "environment": {
    "requirements": "../requirements.txt"
  },
  "deployment": {
    "transport": "stdio",
    "log_level": "INFO"
  }
}
```

### Transport Options

- **stdio**: Standard input/output (default)
- **http**: HTTP transport for web-based clients
- **sse**: Server-sent events for real-time updates

## 🧪 Testing

Run the test script to verify all functionality:

```bash
python test_mcp_server.py
```

This will test:
- Server connection and Django integration
- Category listing
- Service type listing
- Resource listing
- Search functionality
- Taxonomy summary

## 📝 Response Format

All tools return responses in the following format:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": {
    // Tool-specific data
  }
}
```

### Success Response Example

```json
{
  "status": "success",
  "message": "Retrieved 5 resources",
  "data": {
    "resources": [
      {
        "id": 1,
        "name": "Example Resource",
        "description": "Resource description...",
        "status": "published",
        "category": "Mental Health",
        "service_types": ["Counseling", "Crisis Intervention"],
        "location": {
          "city": "London",
          "state": "KY",
          "county": "Laurel"
        },
        "contact": {
          "phone": "555-1234",
          "email": "contact@example.org",
          "website": "https://example.org"
        },
        "operational": {
          "is_emergency_service": true,
          "is_24_hour_service": false
        },
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "total_count": 254,
      "limit": 50,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### Error Response Example

```json
{
  "status": "error",
  "message": "Resource with ID 999 not found",
  "data": null
}
```

## 🔒 Security Considerations

- **No Authentication**: All tools are accessible without authentication
- **Audit Trail**: All modifications create audit log entries
- **Data Validation**: Comprehensive validation using Django model validation
- **Error Handling**: Detailed error messages without exposing sensitive information

## 🚀 Deployment

### Local Development

```bash
cd mcp_server
fastmcp run server.py
```

### Production Deployment

1. **Configure transport**: Use HTTP transport for production
2. **Set log level**: Use WARNING or ERROR for production
3. **Environment variables**: Configure Django settings appropriately
4. **Process management**: Use a process manager like systemd or supervisor

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["fastmcp", "run", "mcp_server/server.py"]
```

## 📊 Monitoring

The server provides comprehensive logging and monitoring:

- **Request logging**: All tool calls are logged
- **Error tracking**: Detailed error information
- **Performance metrics**: Response times and query performance
- **Audit trails**: Complete change history

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive docstrings
3. Include error handling
4. Update tests for new functionality
5. Maintain audit trail integration

## 📄 License

This MCP server is part of the Community Resource Directory project and follows the same licensing terms.

## 🆘 Support

For issues and questions:

1. Check the test script output
2. Review Django model integration
3. Verify FastMCP installation
4. Check audit log entries for errors

---

**Last Updated**: 2025-01-15  
**Version**: 1.0.0  
**Status**: Production Ready
