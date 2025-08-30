# Archived Cloud Migration Scripts

> **Status**: ARCHIVED - Replaced by `scripts/migrations/database_sync/db_sync.py`  
> **Date Archived**: 2025-08-30  
> **Reason**: Superseded by comprehensive database synchronization tool

## 📋 **Overview**

These scripts were used for migrating data between local development and staging environments. They have been **replaced by the comprehensive database synchronization tool** (`scripts/migrations/database_sync/db_sync.py`) which provides:

- ✅ **Complete database synchronization** (not just selective data)
- ✅ **Bidirectional sync** (dev↔staging)
- ✅ **Safety features** (backups, confirmations, dry-run)
- ✅ **Data validation** and integrity checks
- ✅ **Rollback capabilities**

## 🔄 **Archived Scripts**

### **GIS Migration Scripts**
- **`migrate_all_gis_data.py`** (11KB, 297 lines) - Complete GIS data migration
- **`migrate_gis_data.py`** (17KB, 460 lines) - Comprehensive data migration
- **`migrate_staging_only.py`** (6.6KB, 189 lines) - Staging-only updates
- **`migrate_service_areas.py`** (8.3KB, 238 lines) - Service areas migration

### **SQLite Migration Scripts**
- **`simple_data_migration.py`** (8.2KB, 223 lines) - SQLite to PostgreSQL export
- **`import_json_data.py`** (2.4KB, 73 lines) - JSON import to PostgreSQL

## 🚀 **Current Recommended Approach**

### **For Complete Environment Sync**
```bash
# Sync development data to staging
python scripts/migrations/database_sync/db_sync.py --dev-to-staging

# Sync staging data to development  
python scripts/migrations/database_sync/db_sync.py --staging-to-dev

# Dry run to see what would happen
python scripts/migrations/database_sync/db_sync.py --dev-to-staging --dry-run
```

## ⚠️ **Important Notes**

- **Do not use these archived scripts** for new migrations
- **Use `db_sync.py`** for all database synchronization needs
- These scripts are kept for **reference and historical purposes only**
- The export files in `cloud/exports/` are also obsolete and can be cleaned up

---

*Last updated: 2025-08-30*
