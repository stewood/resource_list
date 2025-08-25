# Test Suite Cleanup Plan for PostgreSQL Migration

## Overview
After migrating from SQLite with GIS to PostgreSQL without GIS, we need to clean up the test suite to remove irrelevant tests and ensure all tests work with PostgreSQL.

## Files to Remove (GIS/Spatial Heavy)

### 1. `directory/tests/test_performance.py` - REMOVE
**Reason**: Heavily focused on spatial query performance testing with GIS geometries
- Contains spatial query performance tests
- Tests spatial index effectiveness
- Tests concurrent spatial queries
- All tests use GIS geometries (Point, Polygon, MultiPolygon)
- Not relevant for PostgreSQL without PostGIS

### 2. `directory/tests/test_location_search.py` - REMOVE
**Reason**: Comprehensive location search with spatial filtering
- Tests address geocoding with spatial filtering
- Tests spatial radius filtering
- Tests point-in-polygon queries
- Uses GIS geometries extensively
- Not relevant without GIS support

### 3. `directory/tests/test_location_search_simple.py` - REMOVE
**Reason**: Simplified version but still GIS-dependent
- Tests location-based search functionality
- Uses spatial queries and GIS geometries
- Not compatible with PostgreSQL without PostGIS

## Files to Simplify (Remove GIS/Spatial Tests)

### 1. `directory/tests/test_models.py` - SIMPLIFY
**Keep**: Basic model tests, validation tests, CRUD operations
**Remove**: 
- `CoverageAreaModelTestCase` (GIS geometry tests)
- `SpatialQueryTestCase` (spatial query functionality)
- `GeocodingServiceTestCase` (GIS-dependent geocoding)

### 2. `directory/tests/test_data_import.py` - SIMPLIFY
**Keep**: Basic data import tests, validation tests
**Remove**:
- `test_coordinate_system_conversion` (GIS SRID tests)
- Any tests using GIS geometries

### 3. `directory/tests/test_search.py` - SIMPLIFY
**Keep**: Basic search functionality, text search
**Remove**: Spatial search tests, location-based filtering

## Files to Keep (PostgreSQL Compatible)

### 1. `directory/tests/test_models.py` - KEEP (simplified)
- Basic model validation
- CRUD operations
- Field validation
- Relationship tests

### 2. `directory/tests/test_views.py` - KEEP
- View functionality
- HTTP responses
- Form handling

### 3. `directory/tests/test_forms.py` - KEEP
- Form validation
- Form processing

### 4. `directory/tests/test_api_endpoints.py` - KEEP
- API functionality
- JSON responses

### 5. `directory/tests/test_ui_components.py` - KEEP
- UI component tests
- Template rendering

### 6. `directory/tests/test_permissions.py` - KEEP
- Permission tests
- User access control

### 7. `directory/tests/test_workflows.py` - KEEP
- Business logic workflows
- Process testing

### 8. `directory/tests/test_integration.py` - KEEP
- Integration tests
- End-to-end workflows

### 9. `directory/tests/test_data_integrity.py` - KEEP
- Data integrity checks
- Validation rules

### 10. `directory/tests/test_versions.py` - KEEP
- Version control tests
- Audit trail tests

## Implementation Steps

### Step 1: Remove GIS-Heavy Test Files
1. Remove `test_performance.py`
2. Remove `test_location_search.py`
3. Remove `test_location_search_simple.py`

### Step 2: Simplify Remaining Test Files
1. Remove GIS-specific test methods from `test_models.py`
2. Remove spatial tests from `test_data_import.py`
3. Remove location-based tests from `test_search.py`

### Step 3: Update Test Settings
1. Use `test_settings_postgresql.py` instead of `test_settings.py`
2. Ensure all tests run against PostgreSQL
3. Remove GIS dependencies

### Step 4: Test PostgreSQL Compatibility
1. Run remaining tests with PostgreSQL
2. Fix any PostgreSQL-specific issues
3. Ensure all tests pass

## Expected Results

### Before Cleanup
- ~267 tests (many failing due to GIS dependencies)
- Heavy GIS/spatial focus
- SQLite-specific tests

### After Cleanup
- ~150-200 tests (PostgreSQL compatible)
- Focus on core functionality
- PostgreSQL-specific tests
- Faster test execution

## Files to Create/Update

### 1. Update `run_tests.py`
- Use PostgreSQL test settings
- Remove GIS dependencies

### 2. Create `test_postgresql_specific.py` (optional)
- PostgreSQL-specific functionality tests
- Database-specific features

### 3. Update documentation
- Remove references to GIS/spatial features
- Update test running instructions

## Success Criteria

- [ ] All tests run successfully with PostgreSQL
- [ ] No GIS/spatial dependencies in test suite
- [ ] Test execution time reduced
- [ ] All core functionality still tested
- [ ] PostgreSQL-specific features tested
