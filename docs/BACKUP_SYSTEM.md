# Backup System Documentation

## Overview

The Community Resource Directory includes a comprehensive backup system that provides automated backup functionality for both local development and staging environments. The system supports database backups, file system backups, and automated backup management with retention policies.

## Features

### 🔄 **Backup Types**
- **Local Database**: PostgreSQL backup of development environment
- **Staging Database**: PostgreSQL backup of Render staging environment
- **File System**: Complete project files and directories backup
- **Full Backup**: All databases and files in one operation

### 🛡️ **Data Protection**
- **Compressed Storage**: All backups are automatically compressed (gzip)
- **Integrity Verification**: Built-in backup verification and corruption detection
- **Retention Management**: Automated cleanup of old backups
- **Detailed Logging**: Comprehensive logging of all backup operations

### 📊 **Backup Organization**
```
backups/
├── databases/          # Database backups (.sql.gz files)
├── files/             # File system backups (.tar.gz files)
└── logs/              # Backup operation logs
```

## Quick Start

### **Prerequisites**
1. **PostgreSQL Tools**: Ensure `pg_dump` is installed and accessible
2. **Python Dependencies**: All project dependencies installed
3. **Database Access**: Proper credentials for local and staging databases

### **Basic Usage**

#### **Simple Commands (Recommended)**
```bash
# Backup local development database
./scripts/backup/backup.sh local

# Backup staging database on Render
./scripts/backup/backup.sh staging

# Backup all project files
./scripts/backup/backup.sh files

# Full backup (everything)
./scripts/backup/backup.sh all

# List all available backups
./scripts/backup/backup.sh list

# Clean up old backups
./scripts/backup/backup.sh cleanup
```

#### **Advanced Commands**
```bash
# Use the Python script directly for more options
python scripts/backup/backup_manager.py --help

# Backup with custom retention
python scripts/backup/backup_manager.py --all --cleanup --keep-days 7

# Verify a specific backup file
python scripts/backup/backup_manager.py --verify backups/databases/local_db_backup_20250115_120000.sql.gz
```

## Detailed Usage

### **Database Backups**

#### **Local Development Database**
```bash
# Simple backup
./scripts/backup/backup.sh local

# With cleanup (keep last 30 days)
./scripts/backup/backup.sh local --cleanup

# With custom retention
./scripts/backup/backup.sh local --cleanup --keep-days 7
```

**What's Backed Up:**
- Complete PostgreSQL database dump
- All tables, data, and schema
- Compressed with gzip for storage efficiency
- Timestamped filename: `local_db_backup_YYYYMMDD_HHMMSS.sql.gz`

#### **Staging Database (Render)**
```bash
# Simple backup
./scripts/backup/backup.sh staging

# With cleanup
./scripts/backup/backup.sh staging --cleanup
```

**What's Backed Up:**
- Complete staging PostgreSQL database from Render
- SSL connection with authentication
- Compressed with gzip
- Timestamped filename: `staging_db_backup_YYYYMMDD_HHMMSS.sql.gz`

### **File System Backups**

```bash
# Backup all project files
./scripts/backup/backup.sh files
```

**What's Backed Up:**
- `directory/` - Main Django application
- `audit/` - Audit and versioning app
- `importer/` - Import/export functionality
- `resource_directory/` - Django settings
- `templates/` - HTML templates
- `static/` - Static files
- `media/` - User uploaded files
- Configuration files (requirements.txt, Dockerfile, etc.)
- Documentation files (README.md, RELEASE_NOTES.md, etc.)

**Archive Format:** `files_backup_YYYYMMDD_HHMMSS.tar.gz`

### **Full Backup Operations**

```bash
# Backup everything at once
./scripts/backup/backup.sh all

# Full backup with cleanup
./scripts/backup/backup.sh all --cleanup --keep-days 14
```

**What's Included:**
1. Local development database backup
2. Staging database backup
3. Complete file system backup
4. Optional cleanup of old backups

## Backup Management

### **Listing Backups**
```bash
./scripts/backup/backup.sh list
```

**Output Example:**
```
================================================================================
BACKUP INVENTORY
================================================================================

📊 DATABASE BACKUPS:
----------------------------------------
  local_db_backup_20250115_143022.sql.gz
    Date: 2025-01-15 14:30:22
    Size: 2.45 MB

  staging_db_backup_20250115_143025.sql.gz
    Date: 2025-01-15 14:30:25
    Size: 1.87 MB

📁 FILE BACKUPS:
----------------------------------------
  files_backup_20250115_143030.tar.gz
    Date: 2025-01-15 14:30:30
    Size: 15.23 MB

💾 TOTAL BACKUP SIZE: 19.55 MB
================================================================================
```

### **Backup Verification**
```bash
# Verify a specific backup file
python scripts/backup/backup_manager.py --verify backups/databases/local_db_backup_20250115_143022.sql.gz
```

**Verification Checks:**
- File existence and size
- Gzip integrity (for compressed files)
- Tar.gz archive integrity (for file backups)
- SQL file format validation (for database backups)

### **Cleanup Operations**
```bash
# Clean up old backups (keep last 30 days)
./scripts/backup/backup.sh cleanup

# Clean up with custom retention (keep last 7 days)
./scripts/backup/backup.sh cleanup --keep-days 7
```

**Cleanup Policy:**
- **Database Backups**: Keep last 30 days by default
- **File Backups**: Keep last 30 days by default
- **Log Files**: Keep last 7 days
- **Compressed Storage**: Automatic compression to save space

## Configuration

### **Database Configuration**
The backup system uses the following database configurations:

#### **Local Development**
```python
{
    'name': 'resource_directory_dev',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}
```

#### **Staging (Render)**
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
```python
{
    'retention_days': 30,      # Days to keep backups
    'compression': True        # Enable gzip compression
}
```

## Backup Restoration

### **Database Restoration**

#### **Local Database**
```bash
# Restore from compressed backup
gunzip -c backups/databases/local_db_backup_20250115_143022.sql.gz | psql -h localhost -U postgres -d resource_directory_dev
```

#### **Staging Database**
```bash
# Restore to staging (requires Render access)
gunzip -c backups/databases/staging_db_backup_20250115_143025.sql.gz | psql -h dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com -U isaiah58_user -d isaiah58_resources --sslmode=require
```

### **File Restoration**
```bash
# Extract file backup
tar -xzf backups/files/files_backup_20250115_143030.tar.gz

# Restore specific files/directories
tar -xzf backups/files/files_backup_20250115_143030.tar.gz directory/ templates/ static/
```

## Automation

### **Cron Jobs**
Set up automated backups using cron:

```bash
# Edit crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/project && ./scripts/backup/backup.sh all --cleanup

# Weekly cleanup on Sundays at 3 AM
0 3 * * 0 cd /path/to/project && ./scripts/backup/backup.sh cleanup --keep-days 7
```

### **Systemd Timer (Linux)**
Create a systemd service for automated backups:

```ini
# /etc/systemd/system/resource-directory-backup.service
[Unit]
Description=Resource Directory Backup
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/project
ExecStart=/path/to/project/scripts/backup/backup.sh all --cleanup
```

```ini
# /etc/systemd/system/resource-directory-backup.timer
[Unit]
Description=Run Resource Directory Backup daily
Requires=resource-directory-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Monitoring and Logging

### **Log Files**
All backup operations are logged to:
```
backups/logs/backup_YYYYMMDD_HHMMSS.log
```

### **Log Format**
```
2025-01-15 14:30:22 - INFO - Starting local database backup...
2025-01-15 14:30:25 - INFO - Local database backup completed: local_db_backup_20250115_143022.sql.gz (2.45 MB)
2025-01-15 14:30:25 - INFO - Starting staging database backup...
2025-01-15 14:30:28 - INFO - Staging database backup completed: staging_db_backup_20250115_143025.sql.gz (1.87 MB)
```

### **Exit Codes**
- `0`: Success
- `1`: Error occurred

## Troubleshooting

### **Common Issues**

#### **pg_dump Command Not Found**
```bash
# Install PostgreSQL client tools
sudo apt-get install postgresql-client  # Ubuntu/Debian
sudo yum install postgresql  # CentOS/RHEL
```

#### **Permission Denied**
```bash
# Make backup script executable
chmod +x scripts/backup/backup.sh
chmod +x scripts/backup/backup_manager.py
```

#### **Database Connection Failed**
- Verify database credentials in `backup_manager.py`
- Check if database server is running
- Ensure network connectivity for staging database

#### **Insufficient Disk Space**
```bash
# Check available space
df -h

# Clean up old backups
./scripts/backup/backup.sh cleanup --keep-days 7
```

### **Debug Mode**
```bash
# Run with verbose output
python scripts/backup/backup_manager.py --local-db --verbose
```

## Security Considerations

### **Credential Management**
- Database passwords are hardcoded in the backup script
- Consider using environment variables for production
- Ensure backup files are properly secured

### **Backup File Security**
```bash
# Set proper permissions on backup directory
chmod 750 backups/
chmod 640 backups/databases/*
chmod 640 backups/files/*
```

### **Network Security**
- Staging database backup uses SSL connection
- Local database backup uses localhost connection
- Consider firewall rules for backup operations

## Best Practices

### **Backup Frequency**
- **Development**: Daily or before major changes
- **Staging**: Daily automated backups
- **Production**: Multiple daily backups with off-site storage

### **Retention Policy**
- **Daily Backups**: Keep 7-14 days
- **Weekly Backups**: Keep 4-8 weeks
- **Monthly Backups**: Keep 6-12 months

### **Testing**
- Regularly test backup restoration
- Verify backup integrity
- Document restoration procedures

### **Monitoring**
- Monitor backup success/failure
- Track backup sizes and growth
- Alert on backup failures

## Support

For backup system issues:
1. Check log files in `backups/logs/`
2. Verify database connectivity
3. Ensure sufficient disk space
4. Review backup configuration

---

**Last Updated**: 2025-01-15  
**Version**: 1.0.0  
**Status**: Production Ready
