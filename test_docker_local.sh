#!/bin/bash

# Test Docker build and run locally
set -e

echo "🐳 Testing Docker build locally..."

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t resource-directory-test .

echo "✅ Docker build successful!"

# Test running the container
echo "🚀 Testing container startup..."
docker run --rm -it \
  -e DJANGO_SETTINGS_MODULE=resource_directory.production_settings \
  -e SECRET_KEY=test-secret-key \
  -e DEBUG=True \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e GIS_ENABLED=False \
  -e DATABASE_URL=sqlite:///test.db \
  resource-directory-test \
  python manage.py check

echo "✅ Container startup test successful!"

echo "🎉 All tests passed! You can now run:"
echo "   docker-compose -f docker-compose.test.yml up --build"
