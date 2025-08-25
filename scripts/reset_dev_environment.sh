#!/bin/bash

# Development Environment Reset Script for Resource Directory
# This script resets the PostgreSQL development environment

set -e  # Exit on any error

echo "🔄 Resetting Resource Directory Development Environment"
echo "====================================================="

# Check if we're in the project root
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
fi

# Stop and remove PostgreSQL container
echo "🛑 Stopping PostgreSQL container..."
docker compose -f docker-compose.dev.yml down

# Remove PostgreSQL volume to clear all data
echo "🗑️  Clearing PostgreSQL data..."
docker volume rm rl_postgres_data 2>/dev/null || echo "   Volume already removed or doesn't exist"

# Start PostgreSQL container fresh
echo "📦 Starting fresh PostgreSQL container..."
docker compose -f docker-compose.dev.yml up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker exec resource_directory_postgres_dev pg_isready -U postgres -d resource_directory_dev > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    
    echo "   Attempt $attempt/$max_attempts - PostgreSQL not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ PostgreSQL failed to start within the expected time."
    echo "   Check container logs with: docker logs resource_directory_postgres_dev"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and run migrations
echo "🔄 Running Django migrations..."
source venv/bin/activate
python manage.py migrate --settings=resource_directory.development_settings

# Create superuser
echo "👤 Creating superuser..."
python manage.py shell --settings=resource_directory.development_settings -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
"

echo ""
echo "✅ Development environment reset complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Start the development server:"
echo "      python manage.py runserver --settings=resource_directory.development_settings"
echo ""
echo "   2. Access the admin interface:"
echo "      http://localhost:8000/admin/"
echo "      Username: admin, Password: admin"
echo ""
echo "   3. Stop PostgreSQL when done:"
echo "      docker compose -f docker-compose.dev.yml down"
echo ""
