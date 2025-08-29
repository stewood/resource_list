# Backup System

This directory contains the backup system for the Community Resource Directory project.

## Quick Start

### **Simple Commands**
```bash
# Backup local development database
./scripts/backup/backup.sh local

# Backup staging database on Render
./scripts/backup/backup.sh staging

# Backup all project files
./scripts/backup/backup.sh files

# Full backup (everything)
./scripts/backup/backup.sh all

# List all backups
./scripts/backup/backup.sh list

# Clean up old backups
./scripts/backup/backup.sh cleanup
```

### **Advanced Usage**
```bash
# Get help
./scripts/backup/backup.sh help

# Use Python script directly for more options
python scripts/backup/backup_manager.py --help
```

## Database Synchronization

### **Sync Commands**
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

### **Advanced Sync Usage**
```bash
# Get sync help
./scripts/backup/sync.sh help

# Use Python script directly for more options
python scripts/backup/db_sync.py --help
```

## Files

- `backup_manager.py` - Main backup management script
- `backup.sh` - Simple shell script wrapper
- `db_sync.py` - Database synchronization script
- `sync.sh` - Simple shell script wrapper for sync operations
- `README.md` - This file

## Documentation

For complete documentation, see: `docs/BACKUP_SYSTEM.md`

## Backup Storage

Backups are stored in the `backups/` directory with the following structure:

```
backups/
├── databases/          # Database backups (.sql.gz files)
├── files/             # File system backups (.tar.gz files)
├── sync_backups/      # Sync-specific backups (.sql files)
└── logs/              # Backup operation logs
```

## Prerequisites

1. **PostgreSQL Tools**: `pg_dump` must be installed
2. **Python Dependencies**: All project dependencies installed
3. **Database Access**: Proper credentials for local and staging databases

## Examples

### **Daily Development Backup**
```bash
./scripts/backup/backup.sh local --cleanup
```

### **Weekly Full Backup**
```bash
./scripts/backup/backup.sh all --cleanup --keep-days 7
```

### **Verify Backup Integrity**
```bash
python scripts/backup/backup_manager.py --verify backups/databases/local_db_backup_20250115_120000.sql.gz
```

---

**Last Updated**: 2025-01-15  
**Version**: 1.0.0
