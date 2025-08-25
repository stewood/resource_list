#!/bin/bash

# Deploy to Staging Script
# This script deploys the application from development to staging on Render

set -e  # Exit on any error

echo "🚀 Starting deployment to staging..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    print_error "Git is not installed or not in PATH"
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_error "You have uncommitted changes. Please commit all changes before deployment."
    print_status "Use 'git add .' and 'git commit -m \"your message\"' to commit changes"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current branch: $CURRENT_BRANCH"

# Check if we're on a good branch for deployment
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    print_success "Deploying from main/master branch"
elif [ "$CURRENT_BRANCH" = "feature/spatial-service-areas" ]; then
    print_warning "Deploying from feature branch: $CURRENT_BRANCH"
else
    print_warning "Deploying from branch: $CURRENT_BRANCH"
fi

# Run tests before deployment
print_status "Running tests before deployment..."
if python manage.py test --settings=resource_directory.test_settings_postgresql --verbosity=2; then
    print_success "All tests passed"
else
    print_error "Tests failed. Deployment cancelled."
    exit 1
fi

# Check if staging settings file exists
if [ ! -f "resource_directory/staging_settings.py" ]; then
    print_error "Staging settings file not found: resource_directory/staging_settings.py"
    exit 1
fi

# Test staging configuration
print_status "Testing staging configuration..."
if python manage.py check --settings=resource_directory.staging_settings; then
    print_success "Staging configuration is valid"
else
    print_error "Staging configuration has errors. Please fix them before deployment."
    exit 1
fi

# Check if we can connect to the database
print_status "Testing database connection..."
if python manage.py check --database default --settings=resource_directory.staging_settings; then
    print_success "Database connection successful"
else
    print_error "Cannot connect to staging database. Check your environment variables."
    exit 1
fi

# Run migrations on staging
print_status "Running migrations on staging..."
if python manage.py migrate --settings=resource_directory.staging_settings; then
    print_success "Migrations completed successfully"
else
    print_error "Migrations failed"
    exit 1
fi

# Collect static files
print_status "Collecting static files..."
if python manage.py collectstatic --noinput --settings=resource_directory.staging_settings; then
    print_success "Static files collected"
else
    print_error "Static file collection failed"
    exit 1
fi

# Push to git to trigger Render deployment
print_status "Pushing to git to trigger Render deployment..."
if git push origin "$CURRENT_BRANCH"; then
    print_success "Code pushed to git successfully"
else
    print_error "Failed to push to git"
    exit 1
fi

print_success "Deployment initiated successfully!"
print_status "Your application will be deployed to: https://isaiah58-resource-directory.onrender.com"
print_status "You can monitor the deployment at: https://dashboard.render.com/web/srv-d2ls9vn5r7bs73e2haeg"

echo
print_status "Next steps:"
echo "1. Monitor the deployment in the Render dashboard"
echo "2. Test the staging application once deployed"
echo "3. Check logs if there are any issues"

echo
print_success "Deployment script completed!"
