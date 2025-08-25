# Cloud Migration Tools

This directory contains tools to migrate your Isaiah 58:10 Ministries Resource Directory from SQLite to PostgreSQL on Render.

## 🎯 Overview

The migration process moves your data from the local SQLite database to a PostgreSQL database hosted on Render, making it ready for cloud deployment.

## 📁 Files

- `migrate_to_cloud.py` - Main migration script (run this first)
- `export_sqlite_data.py` - Exports data from SQLite to JSON
- `import_to_postgresql.py` - Imports data from JSON to PostgreSQL
- `requirements_postgresql.txt` - PostgreSQL dependencies
- `cloud_settings.py` - Django settings for PostgreSQL connection

## 🚀 Quick Start

### 1. Run the Migration

```bash
cd /home/stewood/rl
python cloud/migrate_to_cloud.py
```

This script will:
1. Install PostgreSQL dependencies
2. Export your SQLite data to JSON files
3. Set up the PostgreSQL database schema
4. Import your data to PostgreSQL

### 2. Verify the Migration

After migration, you can verify the data was imported correctly:

```bash
python cloud/import_to_postgresql.py
```

## 📊 Database Details

**PostgreSQL Database on Render:**
- **Host**: `dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com`
- **Database**: `isaiah58_resources`
- **Username**: `isaiah58_user`
- **Password**: `CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr`
- **Plan**: Free ($0/month)

## 🔧 Manual Steps

If you prefer to run steps individually:

### Export Data
```bash
python cloud/export_sqlite_data.py
```

### Install Dependencies
```bash
pip install -r cloud/requirements_postgresql.txt
```

### Run Migrations
```bash
python manage.py migrate --settings=resource_directory.cloud_settings
```

### Import Data
```bash
python cloud/import_to_postgresql.py
```

## 📋 What Gets Migrated

The migration includes:
- ✅ User accounts and permissions
- ✅ Resource directory data
- ✅ Coverage areas and taxonomy
- ✅ Audit logs
- ✅ All Django system tables

## ⚠️ Important Notes

1. **Backup First**: Make sure you have a backup of your SQLite database
2. **Test Locally**: Test the migration before deploying to production
3. **Update Settings**: After migration, update your production settings to use PostgreSQL
4. **Environment Variables**: In production, use environment variables for database credentials

## 🆘 Troubleshooting

### Common Issues

1. **Import Error**: Make sure PostgreSQL dependencies are installed
2. **Connection Error**: Verify the database URL is correct
3. **Permission Error**: Check that the database user has proper permissions

### Getting Help

If you encounter issues:
1. Check the error messages in the console output
2. Verify your database connection details
3. Ensure all dependencies are installed correctly

## 🎉 Next Steps

After successful migration:
1. Test your application with the new PostgreSQL database
2. Update your production settings
3. Deploy to Render or your preferred cloud platform
4. Update your DNS to point to the new cloud deployment
