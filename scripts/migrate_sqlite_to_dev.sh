#!/bin/bash

# SQLite to PostgreSQL Development Migration Script
# This script migrates all data from SQLite to the PostgreSQL development environment

set -e

echo "🚀 SQLite to PostgreSQL Development Migration"
echo "=============================================="

# Change to project directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if PostgreSQL development environment is running
echo "🔍 Checking PostgreSQL development environment..."
if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "❌ PostgreSQL development environment is not running!"
    echo "Starting it now..."
    ./scripts/start_dev.sh &
    sleep 10
fi

# Run the migration
echo "🔄 Running migration..."
python cloud/migrate_sqlite_to_dev.py

echo ""
echo "✅ Migration completed!"
echo ""
echo "🌐 Your development environment is ready with all your SQLite data!"
echo "📱 Access the application at: http://localhost:8000"
echo "🔧 Admin interface at: http://localhost:8000/admin"
echo ""
echo "📋 Migration report saved to: cloud/exports/migration_report.json"
