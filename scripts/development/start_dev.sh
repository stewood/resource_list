#!/bin/bash

# Comprehensive Development Environment Script
# This script stops any running servers, starts PostgreSQL, and runs Django
# with proper signal handling to stop Docker when Ctrl+C is pressed

set -e

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development environment..."
    
    # Stop Django server if running
    pkill -f "manage.py runserver" 2>/dev/null || true
    
    # Stop PostgreSQL container
    echo "📦 Stopping PostgreSQL container..."
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    echo "✅ Development environment stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Development Environment..."
echo "======================================"

# Change to project directory (scripts/development/.. = project root)
cd "$(dirname "$0")/../.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing Django servers
echo "🛑 Stopping any existing Django servers..."
pkill -f "manage.py runserver" 2>/dev/null || echo "No Django servers running"

# Stop any existing PostgreSQL containers
echo "📦 Stopping any existing PostgreSQL containers..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || echo "No PostgreSQL containers running"

# Start PostgreSQL container
echo "📦 Starting PostgreSQL container..."
docker compose -f docker-compose.dev.yml up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is running
if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "❌ PostgreSQL container failed to start"
    cleanup
fi

echo "✅ PostgreSQL container is running"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment 'venv' not found!"
    echo "Please create a virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    cleanup
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Error: Django not found in virtual environment!"
    echo "Please install requirements:"
    echo "  pip install -r requirements.txt"
    cleanup
fi

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found!"
    echo "Please run this script from the Django project root directory."
    cleanup
fi

# Check if migrations are up to date
echo "🔍 Checking database migrations..."
python manage.py migrate --settings=resource_directory.development_settings --check

# Start Django development server
echo ""
echo "🌐 Starting Django development server..."
echo "📱 Server will be available at: http://localhost:8000"
echo "🔧 Admin interface: http://localhost:8000/admin"
echo "📊 Debug toolbar: http://localhost:8000/__debug__/"
echo ""
echo "Press Ctrl+C to stop the server and shutdown PostgreSQL"
echo "======================================"

# Start Django server
python manage.py runserver 0.0.0.0:8000 --settings=resource_directory.development_settings
