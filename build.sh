#!/usr/bin/env bash
# Build script for Render deployment

# Exit on any error
set -e

echo "🚀 Starting build process..."

# Set Django settings module for the build process
export DJANGO_SETTINGS_MODULE=resource_directory.production_settings

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"
