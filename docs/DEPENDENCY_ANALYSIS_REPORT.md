# Dependency Analysis Report

Generated on: 2025-08-30 13:37:54

## Summary

- Total Python files: 229
- Total dependencies: 228
- Average dependencies per file: 1.9
- Circular dependency cycles: 3

## Largest Files

- `directory/models/managers/resource_managers.py`: 1098 lines
- `directory/services/ai/tools/verification.py`: 965 lines
- `directory/services/geocoding.py`: 863 lines
- `directory/tests/test_api_endpoints.py`: 825 lines
- `directory/management/commands/import_states_enhanced.py`: 822 lines
- `directory/management/commands/import_counties_enhanced.py`: 819 lines
- `scripts/backup/backup_manager.py`: 721 lines
- `scripts/migrations/database_sync/db_sync.py`: 719 lines
- `directory/tests/test_ui_components.py`: 714 lines
- `directory/views/api/area_views.py`: 711 lines

## Circular Dependencies

### Cycle 1

- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### Cycle 2

- `archive/cli_review_tools/auto_update_random.py`
- `archive/cli_review_tools/auto_update_random.py`

### Cycle 3

- `directory/management/commands/import_csv_data.py`
- `directory/management/commands/import_csv_data.py`

## Dependency Graph

### archive/cli_review_tools/auto_update_random.py

- `archive/cli_review_tools/auto_update_random.py`
- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cli_review_tools/check_notes_cleanup.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cli_review_tools/update_resource_noninteractive.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cli_review_tools/update_specific_resource.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/clean_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/direct_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/export_sqlite_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/import_json_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/migrate_all_gis_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/migrate_gis_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/migrate_service_areas.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/migrate_sqlite_to_dev.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/migrate_staging_only.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/quick_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/simple_data_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/cloud_migrations/simple_sqlite_to_postgres.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/gis_development_scripts/check_duplicates.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/gis_development_scripts/investigate_duplicates.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/analyze_resources_without_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/check_kentucky_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/check_resource_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/check_resources_without_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/check_us_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/comprehensive_geometry_fix.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/debug_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/debug_state_import.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/final_geometry_fix.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/fix_resource_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/import_coverage_areas_from_json.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/manual_kentucky_import.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/migrate_gis_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/migrate_gis_data_batch.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/simple_coverage_import.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### archive/temporary_scripts/test_fips.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### archive/temporary_scripts/test_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### audit/models.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### audit/views.py

- `directory/management/commands/import_csv_data.py`

### config/api_keys.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/management/commands/check_data_quality.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/management/commands/find_duplicates.py

- `directory/management/commands/import_csv_data.py`

### directory/management/commands/import_cities_enhanced.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### directory/management/commands/import_counties_enhanced.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### directory/management/commands/import_csv_data.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `directory/management/commands/import_csv_data.py`

### directory/management/commands/import_states_enhanced.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### directory/management/commands/load_geojson.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/management/commands/merge_duplicates.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/models/analytics/audit.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/models/geographic/coverage_area.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/services/ai/core/review_service.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/services/ai/reports/generator.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/services/ai/tools/response_parser.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/services/ai/tools/verification.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/services/ai/tools/web_scraper.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/services/ai/utils/helpers.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/services/geocoding.py

- `archive/cli_review_tools/auto_update_random.py`

### directory/templatetags/directory_extras.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/tests/test_ai_service_integration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### directory/tests/test_api_endpoints.py

- `archive/old_migrations/__init__.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/tests/test_ui_components.py

- `archive/old_migrations/__init__.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/tests/utilities/test_national_coverage_update.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### directory/utils/data_quality.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/utils/duplicate_resolution.py

- `directory/management/commands/import_csv_data.py`

### directory/utils/duplicate_utils.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### directory/utils/export_utils.py

- `directory/management/commands/import_csv_data.py`

### directory/utils/tiger_cache.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/views/ai_api_views.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/views/ai_review_views.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/views/api/area_views.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/views/api/base.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### directory/views/api/resource_views.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### docs/verification/find_next_verification.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### docs/verification/update_resource_verification.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### importer/forms.py

- `archive/old_migrations/__init__.py`
- `directory/management/commands/import_csv_data.py`

### importer/models.py

- `archive/old_migrations/__init__.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `directory/management/commands/import_csv_data.py`

### importer/views.py

- `archive/old_migrations/__init__.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `directory/management/commands/import_csv_data.py`

### manage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### resource_directory/asgi.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/cloud_settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/cloud_settings_backup.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/cloud_settings_gis.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/cloud_settings_simple.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/development_settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/production_settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/staging_settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/test_settings.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### resource_directory/wsgi.py

- `archive/old_migrations/0002_add_postgresql_search.py`

### scripts/backup/backup_manager.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/add_essential_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/create_national_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/find_next_verification.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/fix_coverage_area_centers.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/fix_staging_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/fix_staging_coverage_centers.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/import_missing_associations.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/manage_service_areas.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/reset_admin_password.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/restore_resource_coverage.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/data/update_existing_resources.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/analyze_dependencies.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/cache_manager.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/debug_ai_service.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/debug_api_response.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/run_tests.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/test_duckduckgo.py

- `archive/temporary_scripts/import_coverage_areas_from_json.py`

### scripts/development/test_enhanced_web_search.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/test_gis_migration.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/test_migration_safety.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `archive/temporary_scripts/import_coverage_areas_from_json.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/development/test_postgis_connection.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/manager.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/operations/clear.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/operations/populate.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/operations/status.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/operations/update.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/utils/cache.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/geo/utils/validation.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

### scripts/migrations/database_sync/db_sync.py

- `archive/old_migrations/0002_add_postgresql_search.py`
- `scripts/development/enhanced_system_summary.py`

