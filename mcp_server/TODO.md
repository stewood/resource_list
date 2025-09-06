# Community Resource Directory MCP Server - Development TODO

## 📋 Overview
This document tracks the development of the MCP (Model Context Protocol) server for the Community Resource Directory. The MCP server will provide AI/LLM access to resource management functionality while maintaining complete separation from the main Django application.

## 🎯 MVP Scope
**Phase 1 Focus**: Core CRUD operations, search, and taxonomy management
- ✅ Resource CRUD (Create, Read, Update, Archive)
- ✅ Advanced search with FTS5
- ✅ Category and service type listing
- ✅ Static resources for read-only data
- ✅ Audit trail preservation

## 📁 Project Structure
```
/home/stewood/rl/mcp/
├── __init__.py
├── server.py              # Main MCP server
├── TODO.md               # This file
├── tools/
│   ├── __init__.py
│   ├── resource_tools.py  # Resource CRUD operations
│   ├── search_tools.py    # Search and discovery
│   └── taxonomy_tools.py  # Categories and service types
├── resources/
│   ├── __init__.py
│   ├── static_resources.py # Static data resources
│   └── dynamic_resources.py # Dynamic resource templates
└── utils/
    ├── __init__.py
    └── helpers.py         # Shared utilities
```

## 🚀 Development Tasks

### Phase 1: Core MCP Infrastructure

#### 1. Set up MCP directory structure and basic FastMCP server
- [x] Create `/home/stewood/rl/mcp_server/` directory structure
- [x] Install FastMCP dependencies
- [x] Create basic `server.py` with FastMCP initialization
- [x] Set up Django model imports (Resource, TaxonomyCategory, ServiceType)
- [x] Create basic server configuration (no auth, stdio transport)
- [x] Test basic server startup

**Files to create:**
- `mcp/__init__.py`
- `mcp/server.py`
- `mcp/tools/__init__.py`
- `mcp/resources/__init__.py`
- `mcp/utils/__init__.py`

#### 2. Implement core CRUD tools (create, read, update, archive, list)
- [x] Create `mcp_server/tools/resource_tools.py`
- [x] Implement `create_resource` tool with full field validation
- [x] Implement `get_resource` tool with detailed resource info
- [x] Implement `update_resource` tool with field-level updates
- [x] Implement `archive_resource` tool (soft delete)
- [x] Implement `list_resources` tool with filtering and pagination
- [x] Add audit trail integration for all modification operations
- [x] Test all CRUD operations

**Key requirements:**
- All tools return structured JSON with success/error status
- Audit trail preservation for all modifications
- Integration with existing Django model validation
- Comprehensive error handling and validation feedback

#### 3. Implement search functionality with FTS5 integration
- [x] Create `mcp_server/tools/search_tools.py`
- [x] Implement `search_resources` tool using existing ResourceManager.search_combined()
- [x] Support multiple search types (fts, exact, combined)
- [x] Add geographic filtering (city, state, county)
- [x] Add service type and category filtering
- [x] Add emergency/24-hour service filtering
- [x] Test search functionality with various queries

**Integration points:**
- Use existing `ResourceManager.search_combined()` method
- Leverage existing FTS5 full-text search capabilities
- Maintain consistency with existing search behavior

#### 4. Implement category and service type listing tools
- [x] Create `mcp_server/tools/taxonomy_tools.py`
- [x] Implement `list_categories` tool with resource counts
- [x] Implement `list_service_types` tool with category filtering
- [x] Add resource count aggregation for each category/type
- [x] Test taxonomy tools

**Features:**
- Optional resource count inclusion
- Category filtering for service types
- Published resource filtering

#### 5. Create static resources for read-only data access
- [x] Create `mcp_server/resources/static_resources.py`
- [x] Implement `resource://categories` static resource
- [x] Implement `resource://service-types` static resource
- [x] Create `mcp_server/resources/dynamic_resources.py`
- [x] Implement `resource://resource/{id}` dynamic resource template
- [x] Test resource access

**Resource types:**
- Static resources for taxonomy data
- Dynamic resource templates for individual resources
- Consistent JSON formatting

#### 6. Integrate audit trail preservation with existing Django models
- [x] Create `mcp_server/utils/helpers.py`
- [x] Implement audit trail creation functions
- [x] Integrate with existing audit models
- [x] Ensure all modification operations create audit entries
- [x] Test audit trail functionality

**Audit requirements:**
- Create audit entries for all resource modifications
- Include user context (if available)
- Preserve change history
- Maintain data integrity

#### 7. Create basic tests for MCP tools and resources
- [x] Create test structure for MCP components
- [x] Test all CRUD operations
- [x] Test search functionality
- [x] Test taxonomy tools
- [x] Test static and dynamic resources
- [x] Test error handling and validation

**Testing approach:**
- Unit tests for individual tools
- Integration tests with Django models
- Error condition testing
- Validation testing

#### 8. Document MCP server usage and tool specifications
- [x] Create comprehensive tool documentation
- [x] Document resource specifications
- [x] Create usage examples
- [x] Document error handling
- [x] Create setup and deployment instructions

**Documentation needs:**
- Tool parameter specifications
- Return value formats
- Error handling patterns
- Usage examples
- Integration instructions

## 🔧 Technical Requirements

### Dependencies
- FastMCP framework
- Django model access (Resource, TaxonomyCategory, ServiceType)
- Existing ResourceManager and search capabilities
- Audit trail integration

### Key Constraints
- **MCP code isolation**: All MCP code must live in `/home/stewood/rl/mcp/` directory
- **No authentication**: All tools accessible without auth requirements
- **Audit trail preservation**: All modifications must create audit entries
- **Django integration**: Leverage existing models and validation
- **Error handling**: Comprehensive error reporting and validation feedback

### Integration Points
- Django models: `Resource`, `TaxonomyCategory`, `ServiceType`
- Existing managers: `ResourceManager` with FTS5 search
- Audit system: Existing audit trail models
- Validation: Django model validation and forms

## 📝 How to Keep This TODO Updated

### When Starting a Task
1. Mark the task as `[ ]` (in progress)
2. Add any sub-tasks or notes as needed
3. Update the status in your development environment

### When Completing a Task
1. Mark the task as `[x]` (completed)
2. Add completion date and any notes
3. Update any related documentation

### When Adding New Tasks
1. Add new tasks under the appropriate phase
2. Include clear acceptance criteria
3. Link to any related issues or requirements

### When Modifying Scope
1. Update the MVP scope section
2. Add/remove tasks as needed
3. Update technical requirements if necessary

### Regular Updates
- Review and update this document weekly
- Mark completed tasks
- Add new tasks as requirements evolve
- Update technical requirements as needed

## 🎯 Success Criteria

### Phase 1 Complete When:
- [x] All 8 core tools implemented and tested
- [x] All 3 static/dynamic resources working
- [x] Audit trail integration functional
- [x] Basic documentation complete
- [x] MCP server can be started and tools called
- [x] Integration with existing Django models working

### MVP Complete When:
- [x] LLMs can perform full CRUD operations on resources
- [x] Advanced search functionality accessible
- [x] Taxonomy data accessible
- [x] Audit trails preserved
- [x] Error handling comprehensive
- [x] Documentation complete

## 📞 Next Steps
1. ✅ **COMPLETED**: Set up MCP directory structure
2. ✅ **COMPLETED**: Install FastMCP and test basic server
3. ✅ **COMPLETED**: Implement CRUD tools
4. ✅ **COMPLETED**: Test integration with existing Django models
5. ✅ **COMPLETED**: Iterate and refine based on testing

## 🎉 Phase 1 Complete!

The Community Resource Directory MCP Server is now fully functional and ready for production use. All core functionality has been implemented, tested, and documented.

### What's Available:
- **15 MCP Tools**: Complete CRUD operations, search, and taxonomy management
- **4 MCP Resources**: Static and dynamic resource access
- **Comprehensive Testing**: All functionality verified and working
- **Full Documentation**: Complete setup and usage guide
- **Audit Trail Integration**: All changes tracked and logged
- **Error Handling**: Robust error handling and validation

### Ready for:
- LLM/AI integration
- Production deployment
- Client application development
- Further feature expansion

---

**Last Updated**: 2025-01-15  
**Version**: 1.0  
**Status**: ✅ **COMPLETE - PRODUCTION READY**
