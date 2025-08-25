#!/usr/bin/env python3
"""
Simple SQLite to PostgreSQL Migration Script

This script directly copies data from SQLite to PostgreSQL for development testing.
It bypasses foreign key constraints and user relationships since this is just for testing.

Usage:
    python cloud/simple_sqlite_to_postgres.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
django.setup()

from django.db import connections
from django.core.management import execute_from_command_line

def main():
    print("🚀 Simple SQLite to PostgreSQL Migration")
    print("========================================")
    
    # Get the admin user ID (should be 1)
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT id FROM auth_user WHERE username = 'admin' LIMIT 1")
        result = cursor.fetchone()
        if result:
            admin_user_id = result[0]
            print(f"✅ Found admin user with ID: {admin_user_id}")
        else:
            print("❌ No admin user found")
            return
    
    # Clear existing data (except users)
    print("\n🧹 Clearing existing data...")
    with connections['default'].cursor() as cursor:
        cursor.execute("DELETE FROM directory_resource_service_types")
        cursor.execute("DELETE FROM directory_resourcecoverage")
        cursor.execute("DELETE FROM directory_resource")
        cursor.execute("DELETE FROM directory_servicetype")
        cursor.execute("DELETE FROM directory_coveragearea")
        cursor.execute("DELETE FROM directory_taxonomycategory")
        print("✅ Cleared existing data")
    
    # Copy data from SQLite to PostgreSQL
    print("\n📋 Copying data from SQLite...")
    
    # Connect to SQLite
    sqlite_db = project_root / 'data' / 'db.sqlite3'
    if not sqlite_db.exists():
        print(f"❌ SQLite database not found at {sqlite_db}")
        return
    
    # Import taxonomy categories first
    print("📂 Importing taxonomy categories...")
    with connections['default'].cursor() as pg_cursor:
        import sqlite3
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get taxonomy categories
        sqlite_cursor.execute("SELECT id, name, description FROM directory_taxonomycategory")
        categories = sqlite_cursor.fetchall()
        
        for cat_id, name, description in categories:
            pg_cursor.execute(
                "INSERT INTO directory_taxonomycategory (id, name, description) VALUES (%s, %s, %s)",
                [cat_id, name, description or '']
            )
        
        print(f"✅ Imported {len(categories)} taxonomy categories")
        
        # Get service types
        print("📂 Importing service types...")
        sqlite_cursor.execute("SELECT id, name, description FROM directory_servicetype")
        service_types = sqlite_cursor.fetchall()
        
        for st_id, name, description in service_types:
            pg_cursor.execute(
                "INSERT INTO directory_servicetype (id, name, description) VALUES (%s, %s, %s)",
                [st_id, name, description or '']
            )
        
        print(f"✅ Imported {len(service_types)} service types")
        
        # Get coverage areas
        print("📂 Importing coverage areas...")
        sqlite_cursor.execute("SELECT id, name, description FROM directory_coveragearea")
        coverage_areas = sqlite_cursor.fetchall()
        
        for ca_id, name, description in coverage_areas:
            pg_cursor.execute(
                "INSERT INTO directory_coveragearea (id, name, description) VALUES (%s, %s, %s)",
                [ca_id, name, description or '']
            )
        
        print(f"✅ Imported {len(coverage_areas)} coverage areas")
        
        # Get resources (with all fields)
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
        
        for resource in resources:
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
        
        print(f"✅ Imported {len(resources)} resources")
        
        # Get resource-service type relationships
        print("📂 Importing resource-service type relationships...")
        sqlite_cursor.execute("SELECT resource_id, servicetype_id FROM directory_resource_service_types")
        relationships = sqlite_cursor.fetchall()
        
        for resource_id, service_type_id in relationships:
            pg_cursor.execute(
                "INSERT INTO directory_resource_service_types (resource_id, servicetype_id) VALUES (%s, %s)",
                [resource_id, service_type_id]
            )
        
        print(f"✅ Imported {len(relationships)} resource-service type relationships")
        
        # Get resource-coverage area relationships
        print("📂 Importing resource-coverage area relationships...")
        sqlite_cursor.execute("SELECT resource_id, coveragearea_id FROM directory_resource_coverage_areas")
        coverage_relationships = sqlite_cursor.fetchall()
        
        for resource_id, coverage_area_id in coverage_relationships:
            pg_cursor.execute(
                "INSERT INTO directory_resourcecoverage (resource_id, coveragearea_id) VALUES (%s, %s)",
                [resource_id, coverage_area_id]
            )
        
        print(f"✅ Imported {len(coverage_relationships)} resource-coverage area relationships")
        
        sqlite_conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print(f"📊 Summary:")
    print(f"   - Taxonomy Categories: {len(categories)}")
    print(f"   - Service Types: {len(service_types)}")
    print(f"   - Coverage Areas: {len(coverage_areas)}")
    print(f"   - Resources: {len(resources)}")
    print(f"   - Service Type Relationships: {len(relationships)}")
    print(f"   - Coverage Area Relationships: {len(coverage_relationships)}")
    
    # Verify the data
    print("\n🔍 Verifying data...")
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM directory_resource")
        resource_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM directory_resource WHERE status = 'published'")
        published_count = cursor.fetchone()[0]
        
        print(f"✅ Total resources in database: {resource_count}")
        print(f"✅ Published resources: {published_count}")
    
    print("\n🌐 You can now access your data at: http://localhost:8000")

if __name__ == '__main__':
    main()
