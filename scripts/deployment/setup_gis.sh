#!/bin/bash

# GIS Setup Script for Resource Directory
# This script helps set up the GIS environment for local development

set -e

echo "🔧 Setting up GIS environment for Resource Directory..."

# Check if we're on Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    echo "📦 Installing GIS dependencies via apt..."
    sudo apt-get update
    sudo apt-get install -y \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libspatialite7 \
        spatialite-bin \
        gdal-bin \
        python3-dev \
        build-essential
elif command -v brew &> /dev/null; then
    echo "🍺 Installing GIS dependencies via Homebrew..."
    brew install gdal geos proj spatialite-tools
else
    echo "❌ Unsupported package manager. Please install GDAL, GEOS, and PROJ manually."
    exit 1
fi

# Set environment variables
echo "🔧 Setting up environment variables..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Django Settings
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_PATH=./data/db.sqlite3

# GIS Configuration
GIS_ENABLED=1
SPATIALITE_LIBRARY_PATH=$(find /usr -name "mod_spatialite.so" 2>/dev/null | head -1 || echo "")
GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" 2>/dev/null | head -1 || echo "")

# Optional: TIGER/Line data directory
TIGER_DATA_DIR=./tiger_data
EOF
    echo "✅ Created .env file with GIS configuration"
else
    echo "📝 Updating existing .env file with GIS configuration..."
    # Add GIS variables if they don't exist
    if ! grep -q "GIS_ENABLED" .env; then
        echo "" >> .env
        echo "# GIS Configuration" >> .env
        echo "GIS_ENABLED=1" >> .env
        echo "SPATIALITE_LIBRARY_PATH=$(find /usr -name "mod_spatialite.so" 2>/dev/null | head -1 || echo "")" >> .env
        echo "GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" 2>/dev/null | head -1 || echo "")" >> .env
        echo "TIGER_DATA_DIR=./tiger_data" >> .env
        echo "✅ Added GIS configuration to .env file"
    else
        echo "✅ GIS configuration already exists in .env file"
    fi
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data
mkdir -p tiger_data

# Install Python dependencies
echo "🐍 Installing Python GIS dependencies..."
pip install -r requirements.txt

# Test GIS installation
echo "🧪 Testing GIS installation..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')

try:
    import django
    django.setup()
    
    from django.conf import settings
    print(f'✅ Django GIS enabled: {getattr(settings, \"GIS_ENABLED\", False)}')
    
    if getattr(settings, 'GIS_ENABLED', False):
        from django.contrib.gis.db.backends.spatialite.base import DatabaseWrapper
        print('✅ SpatiaLite backend available')
        
        from django.contrib.gis.geos import Point
        point = Point(0, 0, srid=4326)
        print('✅ GEOS geometry creation works')
        
        import fiona
        print('✅ Fiona library available')
        
        import shapely
        print('✅ Shapely library available')
        
        print('🎉 GIS environment is ready!')
    else:
        print('⚠️  GIS is not enabled in Django settings')
        
except Exception as e:
    print(f'❌ Error testing GIS: {e}')
    exit(1)
"

# Initialize database with spatial support
echo "🗄️  Initializing database with spatial support..."
python manage.py migrate

# Test spatial functionality
echo "🧪 Testing spatial functionality..."
python manage.py shell -c "
from django.conf import settings
from directory.models import CoverageArea

print(f'GIS Enabled: {getattr(settings, \"GIS_ENABLED\", False)}')

if getattr(settings, 'GIS_ENABLED', False):
    try:
        # Test creating a coverage area with geometry
        from django.contrib.gis.geos import Point, Polygon
        from django.contrib.auth.models import User
        
        user, _ = User.objects.get_or_create(username='test_user')
        
        # Create a test point
        point = Point(-84.5, 37.0, srid=4326)
        
        # Create a test polygon (simple square)
        coords = [(-84.6, 36.9), (-84.4, 36.9), (-84.4, 37.1), (-84.6, 37.1), (-84.6, 36.9)]
        polygon = Polygon(coords, srid=4326)
        
        # Create coverage area
        coverage_area = CoverageArea.objects.create(
            kind='RADIUS',
            name='Test Coverage Area',
            geom=polygon,
            center=point,
            radius_m=5000,
            ext_ids={'test': 'data'},
            created_by=user,
            updated_by=user
        )
        
        print(f'✅ Created test coverage area: {coverage_area}')
        
        # Clean up
        coverage_area.delete()
        print('✅ Spatial functionality test passed!')
        
    except Exception as e:
        print(f'❌ Spatial functionality test failed: {e}')
        exit(1)
else:
    print('⚠️  Skipping spatial test - GIS not enabled')
"

echo ""
echo "🎉 GIS setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the development server: python manage.py runserver"
echo "2. Test GIS functionality: python manage.py import_counties --validate-only"
echo "3. Import county data: python manage.py import_counties --states 21,47,51"
echo ""
echo "For Docker deployment:"
echo "1. Build with GIS: docker-compose build"
echo "2. Run with GIS: docker-compose up"
echo ""
