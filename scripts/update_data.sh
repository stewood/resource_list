#!/bin/bash
# Geographic Data Update Script Wrapper
# 
# This script provides an easy way to update geographic data for the Resource Directory app.
# It handles virtual environment activation and proper environment setup.
#
# Usage:
#   ./scripts/update_data.sh [options]
#
# Options:
#   --all-states       Import data for all US states
#   --clear-existing   Clear existing data before importing
#   --update-existing  Update existing records with new data
#   --year YEAR        TIGER/Line year to use (default: 2023)
#   --status-only      Only show current data status
#   --help             Show this help message

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to show help
show_help() {
    echo "Geographic Data Update Script"
    echo ""
    echo "This script updates geographic data for the Resource Directory app."
    echo ""
    echo "Usage:"
    echo "  $0 [options]"
    echo ""
    echo "Options:"
    echo "  --all-states       Import data for all US states (default: KY and surrounding states)"
    echo "  --clear-existing   Clear existing data before importing"
    echo "  --update-existing  Update existing records with new data (default: skip existing)"
    echo "  --year YEAR        TIGER/Line year to use (default: 2023)"
    echo "  --status-only      Only show current data status, do not import"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --status-only                    # Check current data status"
    echo "  $0 --update-existing               # Update existing data with new boundaries"
    echo "  $0 --all-states --clear-existing   # Import all US data (clears existing)"
    echo "  $0 --year 2024                     # Use 2024 TIGER/Line data"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "This script must be run from the project root directory (where manage.py is located)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run 'python -m venv venv' first."
    exit 1
fi

# Parse command line arguments
PYTHON_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --all-states|--clear-existing|--update-existing|--status-only)
            PYTHON_ARGS="$PYTHON_ARGS $1"
            shift
            ;;
        --year)
            PYTHON_ARGS="$PYTHON_ARGS $1 $2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Set GIS environment
export GIS_ENABLED=1

# Run the Python script
print_info "Running geographic data update script..."
python scripts/update_geographic_data.py $PYTHON_ARGS

# Check exit status
if [ $? -eq 0 ]; then
    print_success "Geographic data update completed successfully!"
else
    print_error "Geographic data update failed!"
    exit 1
fi
