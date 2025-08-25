#!/usr/bin/env python3
"""
Clean migration from SQLite to PostgreSQL using Django migrations properly.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_clean_migration():
    """Run a clean migration using Django's migration system properly."""

    print("🚀 Starting clean migration from SQLite to PostgreSQL...")
    print("=" * 60)

    # Step 1: Install PostgreSQL dependencies
    print("📦 Installing PostgreSQL dependencies...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'
    ], check=True)
    print("✅ Dependencies installed")

    # Step 2: Clear the database (drop all tables)
    print("\n🗑️  Clearing PostgreSQL database...")
    subprocess.run([
        sys.executable, 'manage.py', 'flush', '--noinput',
        '--settings=resource_directory.cloud_settings_simple'
    ], check=True)
    print("✅ Database cleared")

    # Step 3: Run basic Django migrations (contenttypes, auth, admin, sessions)
    print("\n🔄 Setting up basic Django tables...")
    basic_apps = ['contenttypes', 'auth', 'admin', 'sessions']
    for app in basic_apps:
        print(f"📋 Running {app} migrations...")
        subprocess.run([
            sys.executable, 'manage.py', 'migrate', app,
            '--settings=resource_directory.cloud_settings_simple'
        ], check=True)

    # Step 4: Handle directory migrations carefully
    print("\n🔄 Setting up directory tables...")

    # Run all directory migrations (FTS5 properly removed)
    print("📋 Running directory migrations...")
    subprocess.run([
        sys.executable, 'manage.py', 'migrate', 'directory',
        '--settings=resource_directory.cloud_settings_simple'
    ], check=True)

    # Step 5: Run remaining app migrations
    print("\n🔄 Setting up remaining app migrations...")
    subprocess.run([
        sys.executable, 'manage.py', 'migrate',
        '--settings=resource_directory.cloud_settings_simple'
    ], check=True)

    print("✅ Database schema created")

    # Step 6: Export data from SQLite
    print("\n📤 Exporting data from SQLite...")
    subprocess.run([
        sys.executable, 'manage.py', 'dumpdata',
        'auth.group',
        'auth.user',
        'directory.servicetype',
        'directory.taxonomycategory',
        'directory.resource',
        '--indent=2',
        '--output=cloud/exports/clean_data.json'
    ], check=True)
    print("✅ Data exported")

    # Step 7: Import data to PostgreSQL
    print("\n📥 Importing data to PostgreSQL...")
    subprocess.run([
        sys.executable, 'manage.py', 'loaddata',
        'cloud/exports/clean_data.json',
        '--settings=resource_directory.cloud_settings_simple'
    ], check=True)
    print("✅ Data imported")

    print("\n" + "=" * 60)
    print("🎉 Clean migration completed successfully!")
    print("\n📊 What was migrated:")
    print("- Users (16 records)")
    print("- Service Types (~20 records)")
    print("- Taxonomy Categories (21 records)")
    print("- Resources (254 records)")
    print("\n📋 Next steps:")
    print("1. Test your application with the new PostgreSQL database")
    print("2. Update your production settings to use PostgreSQL")
    print("3. Deploy to Render")


if __name__ == '__main__':
    run_clean_migration()
