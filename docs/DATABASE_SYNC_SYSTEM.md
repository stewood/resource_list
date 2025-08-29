# Database Synchronization System

## Overview

The Database Synchronization System provides comprehensive functionality for syncing data between your development and staging environments. This is essential for testing, data migration, and keeping environments in sync during development.

## Features

### 🔄 **Sync Directions**
- **Development → Staging**: Sync local development data to staging environment
- **Staging → Development**: Sync staging data to local development environment

### 🛡️ **Safety Features**
- **Automatic Backups**: Creates backups before any sync operation
- **Confirmation Prompts**: Requires user confirmation for destructive operations
- **Dry-Run Mode**: Preview what would be synced without making changes
- **Force Mode**: Skip confirmations for automation (use with caution)

### 📊 **Data Validation**
- **Resource Count Verification**: Shows resource counts before and after sync
- **Database Information**: Displays detailed information about both databases
- **Integrity Checks**: Validates data during sync operations

### 🗂️ **Backup Management**
- **Sync-Specific Backups**: Separate backup directory for sync operations
- **Automatic Cleanup**: Configurable retention policies for sync backups
- **Backup Listing**: View all sync backup files with details

## Quick Start

### **Prerequisites**
1. **PostgreSQL 17**: Both environments must be running PostgreSQL 17
2. **Database Access**: Proper credentials for both development and staging
3. **Python Dependencies**: All project dependencies installed

### **Basic Usage**

#### **Simple Commands (Recommended)**
```bash
# Sync development data to staging (with confirmation)
./scripts/backup/sync.sh dev-to-staging

# Sync staging data to development (with confirmation)
./scripts/backup/sync.sh staging-to-dev

# Dry run to see what would be synced
./scripts/backup/sync.sh dev-to-staging --dry-run

# Force sync without confirmation
./scripts/backup/sync.sh staging-to-dev --force

# List sync backup files
./scripts/backup/sync.sh list

# Clean up old sync backups
./scripts/backup/sync.sh cleanup
```

#### **Advanced Commands**
```bash
# Use the Python script directly for more options
python scripts/backup/db_sync.py --help

# Custom retention period for cleanup
python scripts/backup/db_sync.py --cleanup --keep-days 3
```

## Detailed Usage

### **Development to Staging Sync**

#### **With Confirmation (Recommended)**
```bash
./scripts/backup/sync.sh dev-to-staging
```

**What Happens:**
1. Shows database information (resource counts)
2. Prompts for confirmation
3. Creates backup of staging database
4. Creates backup of development database
5. Restores development data to staging
6. Verifies sync completion

**Example Output:**
```
📊 DATABASE INFORMATION:
Development: 254 resources (localhost)
Staging: 254 resources (dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com)

⚠️  WARNING: This will overwrite staging database with development data!
   Staging currently has 254 resources
   Development has 254 resources

Are you sure you want to continue? (yes/no): yes

✅ SYNC COMPLETED:
   Staging now has 254 resources
   Backup files created:
     - staging_before_dev_sync_20250115_143022.sql
     - dev_for_staging_sync_20250115_143025.sql
```

#### **Dry Run Mode**
```bash
./scripts/backup/sync.sh dev-to-staging --dry-run
```

**What Happens:**
- Shows what would be synced without making changes
- No backups created
- No data modified

**Example Output:**
```
📊 DATABASE INFORMATION:
Development: 254 resources (localhost)
Staging: 254 resources (dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com)

🔍 DRY RUN - Would sync 254 resources from development to staging
```

#### **Force Mode (No Confirmation)**
```bash
./scripts/backup/sync.sh dev-to-staging --force
```

**Use Cases:**
- Automation scripts
- CI/CD pipelines
- When you're certain about the operation

### **Staging to Development Sync**

#### **With Confirmation (Recommended)**
```bash
./scripts/backup/sync.sh staging-to-dev
```

**What Happens:**
1. Shows database information (resource counts)
2. Prompts for confirmation
3. Creates backup of development database
4. Creates backup of staging database
5. Restores staging data to development
6. Verifies sync completion

#### **Dry Run Mode**
```bash
./scripts/backup/sync.sh staging-to-dev --dry-run
```

#### **Force Mode**
```bash
./scripts/backup/sync.sh staging-to-dev --force
```

## Backup Management

### **Sync Backup Organization**
```
backups/
├── sync_backups/           # Sync-specific backups
│   ├── staging_before_dev_sync_20250115_143022.sql
│   ├── dev_for_staging_sync_20250115_143025.sql
│   ├── dev_before_staging_sync_20250115_143030.sql
│   └── staging_for_dev_sync_20250115_143035.sql
├── databases/              # Regular database backups
└── files/                  # File system backups
```

### **Listing Sync Backups**
```bash
./scripts/backup/sync.sh list
```

**Output Example:**
```
================================================================================
SYNC BACKUP INVENTORY
================================================================================

  staging_before_dev_sync_20250115_143022.sql
    Date: 2025-01-15 14:30:22
    Size: 4.11 MB

  dev_for_staging_sync_20250115_143025.sql
    Date: 2025-01-15 14:30:25
    Size: 69.56 MB

  dev_before_staging_sync_20250115_143030.sql
    Date: 2025-01-15 14:30:30
    Size: 69.56 MB

  staging_for_dev_sync_20250115_143035.sql
    Date: 2025-01-15 14:30:35
    Size: 4.11 MB

💾 TOTAL SYNC BACKUP SIZE: 147.34 MB
================================================================================
```

### **Cleaning Up Sync Backups**
```bash
# Clean up backups older than 7 days (default)
./scripts/backup/sync.sh cleanup

# Clean up backups older than 3 days
./scripts/backup/sync.sh cleanup --keep-days 3
```

## Use Cases

### **Development Workflow**
1. **Testing New Features**: Sync staging data to development for testing
2. **Data Migration**: Sync development changes to staging
3. **Environment Reset**: Reset development environment with staging data
4. **Data Validation**: Compare data between environments

### **Testing Scenarios**
```bash
# Test with staging data
./scripts/backup/sync.sh staging-to-dev --dry-run
./scripts/backup/sync.sh staging-to-dev

# Deploy development changes to staging
./scripts/backup/sync.sh dev-to-staging --dry-run
./scripts/backup/sync.sh dev-to-staging
```

### **Automation**
```bash
# Automated sync in scripts (use with caution)
./scripts/backup/sync.sh dev-to-staging --force
./scripts/backup/sync.sh staging-to-dev --force
```

## Safety Considerations

### **Before Syncing**
1. **Verify Database Versions**: Ensure both environments use PostgreSQL 17
2. **Check Resource Counts**: Verify the data you're about to sync
3. **Use Dry Run**: Always test with `--dry-run` first
4. **Backup Verification**: Ensure backups are created successfully

### **During Sync**
1. **Monitor Progress**: Watch for any error messages
2. **Verify Completion**: Check resource counts after sync
3. **Test Functionality**: Verify the synced environment works correctly

### **After Syncing**
1. **Validate Data**: Check that all expected data is present
2. **Test Applications**: Ensure applications work with synced data
3. **Keep Backups**: Don't delete sync backups immediately

## Troubleshooting

### **Common Issues**

#### **Version Mismatch**
```
pg_dump: error: aborting because of server version mismatch
pg_dump: detail: server version: 17.6; pg_dump version: 16.9
```
**Solution**: Ensure both environments use PostgreSQL 17

#### **Connection Failed**
```
psql: error: connection to server at "host" failed
```
**Solution**: 
- Check database credentials
- Verify network connectivity
- Ensure database server is running

#### **Permission Denied**
```
psql: error: FATAL: permission denied for database
```
**Solution**: Verify database user permissions

#### **Backup Failed**
```
pg_dump: error: could not open output file
```
**Solution**: Check disk space and file permissions

### **Recovery Procedures**

#### **Restore from Sync Backup**
```bash
# Find the backup file
./scripts/backup/sync.sh list

# Restore using psql
psql -h localhost -U postgres -d resource_directory_dev < backups/sync_backups/dev_before_staging_sync_20250115_143030.sql
```

#### **Verify Database Integrity**
```bash
# Check resource count
psql -h localhost -U postgres -d resource_directory_dev -c "SELECT COUNT(*) FROM directory_resource;"
```

## Best Practices

### **Sync Frequency**
- **Development → Staging**: Before deploying new features
- **Staging → Development**: When testing with production-like data
- **Regular Testing**: Use dry-run mode to verify sync operations

### **Backup Management**
- **Keep Recent Backups**: Maintain at least 7 days of sync backups
- **Monitor Space**: Sync backups can be large
- **Regular Cleanup**: Use automated cleanup to manage disk space

### **Testing**
- **Always Dry Run**: Test sync operations before executing
- **Verify Data**: Check resource counts and data integrity
- **Test Applications**: Ensure applications work after sync

### **Automation**
- **Use Force Mode Carefully**: Only in automated scripts
- **Monitor Logs**: Check sync logs for errors
- **Error Handling**: Implement proper error handling in scripts

## Configuration

### **Database Configurations**
The sync system uses the same configurations as the backup system:

#### **Development Database**
```python
{
    'name': 'resource_directory_dev',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}
```

#### **Staging Database**
```python
{
    'name': 'isaiah58_resources',
    'user': 'isaiah58_user',
    'password': 'CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr',
    'host': 'dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com',
    'port': '5432'
}
```

### **Backup Settings**
- **Sync Backup Directory**: `backups/sync_backups/`
- **Default Retention**: 7 days
- **Logging**: Detailed logs in sync backup directory

## Integration with Backup System

### **Complementary Tools**
- **Backup System**: For regular database backups
- **Sync System**: For environment synchronization
- **Both Systems**: Use same database configurations

### **Workflow Integration**
```bash
# Regular backup
./scripts/backup/backup.sh all

# Environment sync
./scripts/backup/sync.sh dev-to-staging

# Cleanup old backups
./scripts/backup/backup.sh cleanup
./scripts/backup/sync.sh cleanup
```

## Support

For sync system issues:
1. Check sync logs in `backups/sync_backups/`
2. Verify database connectivity
3. Use dry-run mode to test operations
4. Review backup files for data integrity

---

**Last Updated**: 2025-01-15  
**Version**: 1.0.0  
**Status**: Production Ready
