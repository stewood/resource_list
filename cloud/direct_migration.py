#!/usr/bin/env python3
"""
Direct SQLite to PostgreSQL Migration Script

This script uses direct SQL commands to copy data from SQLite to PostgreSQL,
bypassing Django ORM issues.

Usage:
    python cloud/direct_migration.py
"""

import os
import sys
import sqlite3
import psycopg2
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Direct SQLite to PostgreSQL Migration")
    print("========================================")
    
    # Connect to SQLite
    sqlite_db = project_root / 'data' / 'db.sqlite3'
    if not sqlite_db.exists():
        print(f"❌ SQLite database not found at {sqlite_db}")
        return
    
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="resource_directory_dev",
            user="postgres",
            password="postgres"
        )
        pg_cursor = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return
    
    # Clear existing data
    print("\n🧹 Clearing existing data...")
    try:
        pg_cursor.execute("DELETE FROM directory_resource_service_types")
        pg_cursor.execute("DELETE FROM directory_resourcecoverage")
        pg_cursor.execute("DELETE FROM directory_resource")
        pg_cursor.execute("DELETE FROM directory_servicetype")
        pg_cursor.execute("DELETE FROM directory_coveragearea")
        pg_cursor.execute("DELETE FROM directory_taxonomycategory")
        pg_conn.commit()
        print("✅ Cleared existing data")
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return
    
    # Get admin user ID
    pg_cursor.execute("SELECT id FROM auth_user WHERE username = 'admin' LIMIT 1")
    result = pg_cursor.fetchone()
    if result:
        admin_user_id = result[0]
        print(f"✅ Found admin user with ID: {admin_user_id}")
    else:
        print("❌ No admin user found")
        return
    
    # Import taxonomy categories
    print("\n📂 Importing taxonomy categories...")
    sqlite_cursor.execute("SELECT id, name, description FROM directory_taxonomycategory")
    categories = sqlite_cursor.fetchall()
    
    for cat_id, name, description in categories:
        slug = name.lower().replace(' ', '-').replace('&', 'and')
        now = datetime.now()
        pg_cursor.execute(
            "INSERT INTO directory_taxonomycategory (id, name, slug, description, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            [cat_id, name, slug, description or '', now, now]
        )
    
    print(f"✅ Imported {len(categories)} taxonomy categories")
    
    # Import service types
    print("📂 Importing service types...")
    sqlite_cursor.execute("SELECT id, name, description FROM directory_servicetype")
    service_types = sqlite_cursor.fetchall()
    
    for st_id, name, description in service_types:
        slug = name.lower().replace(' ', '-').replace('&', 'and')
        now = datetime.now()
        pg_cursor.execute(
            "INSERT INTO directory_servicetype (id, name, slug, description, created_at) VALUES (%s, %s, %s, %s, %s)",
            [st_id, name, slug, description or '', now]
        )
    
    print(f"✅ Imported {len(service_types)} service types")
    
    # Import coverage areas
    print("📂 Importing coverage areas...")
    sqlite_cursor.execute("SELECT id, name, description FROM directory_coveragearea")
    coverage_areas = sqlite_cursor.fetchall()
    
    for ca_id, name, description in coverage_areas:
        now = datetime.now()
        pg_cursor.execute(
            "INSERT INTO directory_coveragearea (id, kind, name, radius_m, ext_ids, created_at, updated_at, created_by_id, updated_by_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [ca_id, 'county', name, None, '{}', now, now, admin_user_id, admin_user_id]
        )
    
    print(f"✅ Imported {len(coverage_areas)} coverage areas")
    
    # Import resources
    print("📂 Importing resources...")
    sqlite_cursor.execute("""
        SELECT id, name, category_id, description, phone, email, website, 
               address1, address2, city, state, county, postal_code, status, 
               source, notes, hours_of_operation, is_emergency_service, 
               is_24_hour_service, eligibility_requirements, populations_served, 
               insurance_accepted, cost_information, languages_available, capacity,
               last_verified_at, last_verified_by_id, verification_frequency_days,
               created_at, updated_at, created_by_id, updated_by_id, is_deleted,
               is_archived, archived_at, archived_by_id, archive_reason
        FROM directory_resource
    """)
    resources = sqlite_cursor.fetchall()
    
    imported_count = 0
    for resource in resources:
        try:
            # Replace user IDs with admin user ID
            resource = list(resource)
            if resource[25] is not None:  # last_verified_by_id
                resource[25] = admin_user_id
            if resource[29] is not None:  # created_by_id
                resource[29] = admin_user_id
            if resource[30] is not None:  # updated_by_id
                resource[30] = admin_user_id
            if resource[33] is not None:  # archived_by_id
                resource[33] = admin_user_id
            
            pg_cursor.execute("""
                INSERT INTO directory_resource (
                    id, name, category_id, description, phone, email, website,
                    address1, address2, city, state, county, postal_code, status,
                    source, notes, hours_of_operation, is_emergency_service,
                    is_24_hour_service, eligibility_requirements, populations_served,
                    insurance_accepted, cost_information, languages_available, capacity,
                    last_verified_at, last_verified_by_id, verification_frequency_days,
                    created_at, updated_at, created_by_id, updated_by_id, is_deleted,
                    is_archived, archived_at, archived_by_id, archive_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, resource)
            imported_count += 1
            
        except Exception as e:
            print(f"⚠️  Error importing resource {resource[1]}: {e}")
            continue
    
    print(f"✅ Imported {imported_count} resources")
    
    # Import resource-service type relationships
    print("📂 Importing resource-service type relationships...")
    sqlite_cursor.execute("SELECT resource_id, servicetype_id FROM directory_resource_service_types")
    relationships = sqlite_cursor.fetchall()
    
    for resource_id, service_type_id in relationships:
        try:
            pg_cursor.execute(
                "INSERT INTO directory_resource_service_types (resource_id, servicetype_id) VALUES (%s, %s)",
                [resource_id, service_type_id]
            )
        except Exception as e:
            print(f"⚠️  Error importing relationship {resource_id}-{service_type_id}: {e}")
            continue
    
    print(f"✅ Imported {len(relationships)} resource-service type relationships")
    
    # Import resource-coverage area relationships
    print("📂 Importing resource-coverage area relationships...")
    sqlite_cursor.execute("SELECT resource_id, coveragearea_id FROM directory_resource_coverage_areas")
    coverage_relationships = sqlite_cursor.fetchall()
    
    for resource_id, coverage_area_id in coverage_relationships:
        try:
            pg_cursor.execute(
                "INSERT INTO directory_resourcecoverage (resource_id, coveragearea_id) VALUES (%s, %s)",
                [resource_id, coverage_area_id]
            )
        except Exception as e:
            print(f"⚠️  Error importing coverage relationship {resource_id}-{coverage_area_id}: {e}")
            continue
    
    print(f"✅ Imported {len(coverage_relationships)} resource-coverage area relationships")
    
    # Commit all changes
    pg_conn.commit()
    
    # Verify the data
    print("\n🔍 Verifying data...")
    pg_cursor.execute("SELECT COUNT(*) FROM directory_resource")
    total_resources = pg_cursor.fetchone()[0]
    pg_cursor.execute("SELECT COUNT(*) FROM directory_resource WHERE status = 'published'")
    published_resources = pg_cursor.fetchone()[0]
    
    print(f"✅ Total resources in database: {total_resources}")
    print(f"✅ Published resources: {published_resources}")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print("🌐 You can now access your data at: http://localhost:8000")

if __name__ == '__main__':
    main()
