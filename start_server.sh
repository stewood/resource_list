#!/bin/bash

# Start Django Development Server Script
# This script activates the virtual environment and starts the Django server on port 8000

echo "🚀 Starting Django Development Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment 'venv' not found!"
    echo "Please create a virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Error: Django not found in virtual environment!"
    echo "Please install requirements:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found!"
    echo "Please run this script from the Django project root directory."
    exit 1
fi

# Start the server
echo "🌐 Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 8000
