# 🔧 verify_cli.py Refactoring TODO

## 📋 Overview

This document tracks the refactoring of `directory/management/commands/verify_cli.py` from a monolithic 1107-line file into a well-structured, maintainable codebase following SOLID principles.

**Current State**: 1107 lines, single file, multiple responsibilities
**Target State**: ~200 lines main command, multiple focused service classes

---

## 🎯 Refactoring Goals

- [ ] **Single Responsibility**: Each class has one clear purpose
- [ ] **Testability**: Smaller, focused classes are easier to test
- [ ] **Maintainability**: Changes to one aspect don't affect others
- [ ] **Reusability**: Services can be used by other commands
- [ ] **Type Safety**: Data classes provide better type hints
- [ ] **Configuration**: Centralized configuration management
- [ ] **Error Handling**: Consistent error handling patterns

---

## 📊 Progress Tracking

**Overall Progress**: 0% (0/5 phases complete)

| Phase | Status | Progress | Notes |
|-------|--------|----------|-------|
| Phase 1 | ⏳ Pending | 0% | Extract utility functions and data models |
| Phase 2 | ⏳ Pending | 0% | Create service classes and move logic |
| Phase 3 | ⏳ Pending | 0% | Refactor the main command class |
| Phase 4 | ⏳ Pending | 0% | Add comprehensive tests |
| Phase 5 | ⏳ Pending | 0% | Update documentation |

---

## 🚀 Phase 1: Extract Utility Functions and Data Models

**Status**: ⏳ Pending  
**Estimated Time**: 2-3 hours  
**Dependencies**: None

### 📁 Files to Create

#### 1.1 Data Models
- [ ] **Create** `directory/models/verification_models.py`
  - [ ] `WebsiteDiscoveryResult` dataclass
  - [ ] `ResourceData` dataclass  
  - [ ] `VerificationResult` dataclass
  - [ ] `CursorAgentResult` dataclass
  - [ ] Import statements and type hints

#### 1.2 Utility Functions
- [ ] **Create** `directory/utils/verification_utils.py`
  - [ ] `calculate_days_since_verification(resource: Resource) -> Optional[int]`
  - [ ] `determine_verification_priority(resource: Resource) -> str`
  - [ ] `format_discovered_urls_for_prompt(website_discovery_data: Dict[str, Any]) -> str`
  - [ ] Import statements and docstrings

- [ ] **Create** `directory/utils/json_utils.py`
  - [ ] `extract_json_from_text(text: str) -> Dict[str, Any]`
  - [ ] `parse_website_discovery_result(raw_result: str) -> Dict[str, Any]`
  - [ ] `format_json_for_display(data: Any) -> str`
  - [ ] Error handling for JSON parsing

#### 1.3 Configuration
- [ ] **Create** `directory/config/verification_config.py`
  - [ ] `VerificationConfig` dataclass
  - [ ] Default timeout values
  - [ ] Display configuration
  - [ ] Process configuration

### 🔧 Tasks

1. [ ] **Extract data models** from existing code
   - [ ] Identify all data structures used in verify_cli.py
   - [ ] Create corresponding dataclasses with proper type hints
   - [ ] Add validation methods where needed

2. [ ] **Extract utility functions**
   - [ ] Move `_calculate_days_since_verification` to utils
   - [ ] Move `_determine_verification_priority` to utils
   - [ ] Move `_format_discovered_urls_for_prompt` to utils
   - [ ] Move JSON parsing functions to json_utils

3. [ ] **Create configuration management**
   - [ ] Extract hardcoded values (timeouts, limits, etc.)
   - [ ] Create configuration dataclass
   - [ ] Add environment variable support

4. [ ] **Update imports in verify_cli.py**
   - [ ] Add imports for new modules
   - [ ] Remove duplicate code
   - [ ] Test that existing functionality still works

### ✅ Acceptance Criteria

- [ ] All utility functions extracted to separate modules
- [ ] Data models created with proper type hints
- [ ] Configuration centralized
- [ ] Existing functionality preserved
- [ ] No circular imports
- [ ] All new modules have proper docstrings

---

## 🏗️ Phase 2: Create Service Classes and Move Logic

**Status**: ⏳ Pending  
**Estimated Time**: 4-5 hours  
**Dependencies**: Phase 1 complete

### 📁 Files to Create

#### 2.1 Website Discovery Service
- [ ] **Create** `directory/services/website_discovery_service.py`
  - [ ] `WebsiteDiscoveryService` class
  - [ ] `discover_websites(resource_data: ResourceData) -> WebsiteDiscoveryResult`
  - [ ] `_create_website_prompt(resource_data: ResourceData) -> str`
  - [ ] `_parse_website_discovery_result(raw_result: str) -> Dict[str, Any]`
  - [ ] Rich formatting integration
  - [ ] Error handling and logging

#### 2.2 Resource Verification Service
- [ ] **Create** `directory/services/resource_verification_service.py`
  - [ ] `ResourceVerificationService` class
  - [ ] `find_resources_needing_verification(limit: int = 1) -> List[Resource]`
  - [ ] `format_resource_for_verification(resource: Resource, verbose: bool = False) -> ResourceData`
  - [ ] `get_resource_by_id(resource_id: int) -> Resource`
  - [ ] Priority-based resource selection logic

#### 2.3 Cursor Agent Service
- [ ] **Create** `directory/services/cursor_agent_service.py`
  - [ ] `CursorAgentService` class
  - [ ] `call_cursor_agent(prompt: str, timeout_seconds: int = 180) -> CursorAgentResult`
  - [ ] `_smart_cursor_call(prompt: str, timeout_seconds: int = 180) -> str`
  - [ ] `_extract_and_display_json(tool_response: Any) -> None`
  - [ ] Streaming output handling
  - [ ] Process management and cleanup

#### 2.4 Output Formatter Service
- [ ] **Create** `directory/services/output_formatter.py`
  - [ ] `OutputFormatter` class
  - [ ] `format_success_response(message: str, data: Dict[str, Any]) -> str`
  - [ ] `format_error_response(message: str) -> str`
  - [ ] `display_website_discovery_summary(result: WebsiteDiscoveryResult) -> None`
  - [ ] Rich formatting integration
  - [ ] JSON formatting utilities

### 🔧 Tasks

1. [ ] **Create WebsiteDiscoveryService**
   - [ ] Move `_discover_websites` method logic
   - [ ] Move `_parse_website_discovery_result` method logic
   - [ ] Integrate with Rich formatting
   - [ ] Add proper error handling
   - [ ] Add logging

2. [ ] **Create ResourceVerificationService**
   - [ ] Move `_find_resources_needing_verification` method logic
   - [ ] Move `_format_resource_for_verification` method logic
   - [ ] Add resource retrieval by ID
   - [ ] Optimize database queries
   - [ ] Add caching where appropriate

3. [ ] **Create CursorAgentService**
   - [ ] Move `_smart_cursor_call` method logic
   - [ ] Move `_extract_and_display_json` method logic
   - [ ] Improve process management
   - [ ] Add better error handling
   - [ ] Add timeout management

4. [ ] **Create OutputFormatter**
   - [ ] Move output formatting logic
   - [ ] Integrate Rich formatting
   - [ ] Add JSON formatting utilities
   - [ ] Add error formatting

5. [ ] **Update verify_cli.py imports**
   - [ ] Import new service classes
   - [ ] Remove moved methods
   - [ ] Update method calls

### ✅ Acceptance Criteria

- [ ] All service classes created with proper interfaces
- [ ] Logic moved from main command to services
- [ ] Services are independently testable
- [ ] No circular dependencies
- [ ] Proper error handling in all services
- [ ] Rich formatting preserved
- [ ] Existing functionality maintained

---

## 🎯 Phase 3: Refactor the Main Command Class

**Status**: ⏳ Pending  
**Estimated Time**: 2-3 hours  
**Dependencies**: Phase 2 complete

### 📁 Files to Modify

#### 3.1 Main Command Refactoring
- [ ] **Refactor** `directory/management/commands/verify_cli.py`
  - [ ] Simplify `Command` class to orchestration only
  - [ ] Remove business logic (moved to services)
  - [ ] Keep only argument parsing and command routing
  - [ ] Add service initialization
  - [ ] Improve error handling

### 🔧 Tasks

1. [ ] **Simplify Command class**
   - [ ] Remove all business logic methods
   - [ ] Keep only `add_arguments` and `handle` methods
   - [ ] Add service initialization in `__init__`
   - [ ] Simplify `_handle_verify` method

2. [ ] **Update command routing**
   - [ ] Use services for all operations
   - [ ] Add proper error handling
   - [ ] Add logging
   - [ ] Maintain existing CLI interface

3. [ ] **Add service orchestration**
   - [ ] Initialize services in constructor
   - [ ] Pass configuration to services
   - [ ] Handle service errors gracefully
   - [ ] Add service health checks

4. [ ] **Improve error handling**
   - [ ] Add custom exception classes
   - [ ] Implement consistent error responses
   - [ ] Add error logging
   - [ ] Add graceful degradation

### ✅ Acceptance Criteria

- [ ] Main command class reduced to ~200 lines
- [ ] All business logic moved to services
- [ ] Command interface preserved
- [ ] Error handling improved
- [ ] Service orchestration working
- [ ] No functionality lost
- [ ] Code is more readable and maintainable

---

## 🧪 Phase 4: Add Comprehensive Tests

**Status**: ⏳ Pending  
**Estimated Time**: 3-4 hours  
**Dependencies**: Phase 3 complete

### 📁 Files to Create

#### 4.1 Unit Tests
- [ ] **Create** `directory/tests/test_verification_utils.py`
  - [ ] Test `calculate_days_since_verification`
  - [ ] Test `determine_verification_priority`
  - [ ] Test `format_discovered_urls_for_prompt`
  - [ ] Edge cases and error conditions

- [ ] **Create** `directory/tests/test_json_utils.py`
  - [ ] Test `extract_json_from_text`
  - [ ] Test `parse_website_discovery_result`
  - [ ] Test `format_json_for_display`
  - [ ] Invalid JSON handling

- [ ] **Create** `directory/tests/test_website_discovery_service.py`
  - [ ] Test `discover_websites` method
  - [ ] Test prompt creation
  - [ ] Test result parsing
  - [ ] Mock Cursor Agent calls

- [ ] **Create** `directory/tests/test_resource_verification_service.py`
  - [ ] Test `find_resources_needing_verification`
  - [ ] Test `format_resource_for_verification`
  - [ ] Test priority ordering
  - [ ] Database query optimization

- [ ] **Create** `directory/tests/test_cursor_agent_service.py`
  - [ ] Test `call_cursor_agent` method
  - [ ] Test timeout handling
  - [ ] Test process management
  - [ ] Mock subprocess calls

- [ ] **Create** `directory/tests/test_output_formatter.py`
  - [ ] Test success response formatting
  - [ ] Test error response formatting
  - [ ] Test Rich formatting integration
  - [ ] Test JSON formatting

#### 4.2 Integration Tests
- [ ] **Create** `directory/tests/test_verify_cli_integration.py`
  - [ ] Test full command execution
  - [ ] Test service integration
  - [ ] Test error handling
  - [ ] Test CLI argument parsing

### 🔧 Tasks

1. [ ] **Set up test infrastructure**
   - [ ] Create test base classes
   - [ ] Add test fixtures
   - [ ] Set up mocking utilities
   - [ ] Add test data factories

2. [ ] **Write unit tests**
   - [ ] Test all utility functions
   - [ ] Test all service methods
   - [ ] Test error conditions
   - [ ] Test edge cases

3. [ ] **Write integration tests**
   - [ ] Test full command workflow
   - [ ] Test service interactions
   - [ ] Test error propagation
   - [ ] Test CLI interface

4. [ ] **Add test coverage**
   - [ ] Aim for 90%+ coverage
   - [ ] Test all code paths
   - [ ] Test error handling
   - [ ] Test performance

5. [ ] **Set up CI/CD testing**
   - [ ] Add test commands to Makefile
   - [ ] Configure test runners
   - [ ] Add coverage reporting
   - [ ] Add test automation

### ✅ Acceptance Criteria

- [ ] All new modules have comprehensive tests
- [ ] Test coverage > 90%
- [ ] All edge cases covered
- [ ] Error conditions tested
- [ ] Integration tests passing
- [ ] Tests run in CI/CD
- [ ] Performance tests added

---

## 📚 Phase 5: Update Documentation

**Status**: ⏳ Pending  
**Estimated Time**: 1-2 hours  
**Dependencies**: Phase 4 complete

### 📁 Files to Create/Update

#### 5.1 Code Documentation
- [ ] **Update** `directory/management/commands/verify_cli.py`
  - [ ] Add comprehensive docstrings
  - [ ] Add usage examples
  - [ ] Add parameter documentation
  - [ ] Add return value documentation

- [ ] **Update** all service classes
  - [ ] Add class-level docstrings
  - [ ] Add method docstrings
  - [ ] Add parameter documentation
  - [ ] Add return value documentation

- [ ] **Update** utility modules
  - [ ] Add module-level docstrings
  - [ ] Add function docstrings
  - [ ] Add usage examples
  - [ ] Add type hints

#### 5.2 User Documentation
- [ ] **Create** `docs/CLI_VERIFICATION_GUIDE.md`
  - [ ] Command usage examples
  - [ ] Configuration options
  - [ ] Troubleshooting guide
  - [ ] Best practices

- [ ] **Update** `README.md`
  - [ ] Add refactoring information
  - [ ] Update architecture section
  - [ ] Add service documentation
  - [ ] Update development guide

### 🔧 Tasks

1. [ ] **Add code documentation**
   - [ ] Add docstrings to all classes and methods
   - [ ] Add type hints where missing
   - [ ] Add usage examples in docstrings
   - [ ] Add parameter and return documentation

2. [ ] **Create user documentation**
   - [ ] Write CLI usage guide
   - [ ] Document configuration options
   - [ ] Add troubleshooting section
   - [ ] Add best practices

3. [ ] **Update project documentation**
   - [ ] Update README with new architecture
   - [ ] Update development guide
   - [ ] Add service documentation
   - [ ] Update API documentation

4. [ ] **Add inline comments**
   - [ ] Add comments for complex logic
   - [ ] Add TODO comments for future improvements
   - [ ] Add performance notes
   - [ ] Add security considerations

### ✅ Acceptance Criteria

- [ ] All code has comprehensive docstrings
- [ ] User documentation complete
- [ ] Project documentation updated
- [ ] Examples and usage guides added
- [ ] Troubleshooting documentation complete
- [ ] Documentation is up-to-date and accurate

---

## 🎉 Final Validation

### ✅ Overall Acceptance Criteria

- [ ] **Functionality**: All existing functionality preserved
- [ ] **Performance**: No performance regression
- [ ] **Maintainability**: Code is easier to understand and modify
- [ ] **Testability**: All components are testable
- [ ] **Documentation**: Complete and accurate documentation
- [ ] **Code Quality**: Follows project coding standards
- [ ] **Error Handling**: Consistent and robust error handling
- [ ] **Type Safety**: Proper type hints throughout

### 📊 Success Metrics

- [ ] **Line Count**: Main command reduced from 1107 to ~200 lines
- [ ] **Test Coverage**: >90% test coverage
- [ ] **Cyclomatic Complexity**: Reduced complexity in all modules
- [ ] **Code Duplication**: Eliminated code duplication
- [ ] **Documentation Coverage**: 100% of public APIs documented

---

## 🔄 Maintenance and Updates

This TODO document should be updated as work progresses:

- [ ] Update status indicators (⏳ Pending → 🔄 In Progress → ✅ Complete)
- [ ] Add notes and observations
- [ ] Update time estimates based on actual work
- [ ] Add new tasks as they are discovered
- [ ] Mark completed items with completion date
- [ ] Add lessons learned section

---

## 📝 Notes and Observations

*This section will be updated as work progresses*

### Phase 1 Notes
- 

### Phase 2 Notes
- 

### Phase 3 Notes
- 

### Phase 4 Notes
- 

### Phase 5 Notes
- 

---

**Last Updated**: 2025-01-15  
**Next Review**: After Phase 1 completion
