#!/bin/bash
# Database Synchronization Script for Community Resource Directory
#
# This script provides convenient shortcuts for database synchronization operations.
# It's a wrapper around the main db_sync.py script.
#
# Usage:
#     ./scripts/backup/sync.sh dev-to-staging
#     ./scripts/backup/sync.sh staging-to-dev
#     ./scripts/backup/sync.sh dev-to-staging --dry-run
#     ./scripts/backup/sync.sh staging-to-dev --force
#     ./scripts/backup/sync.sh list
#     ./scripts/backup/sync.sh cleanup
#     ./scripts/backup/sync.sh help
#
# Author: Resource Directory Team
# Created: 2025-01-15
# Version: 1.0.0

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root directory
cd "$PROJECT_ROOT"

# Function to show help
show_help() {
    echo "Database Synchronization Script for Community Resource Directory"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev-to-staging    - Sync data from development to staging database"
    echo "  staging-to-dev    - Sync data from staging to development database"
    echo "  list              - List all sync backup files"
    echo "  cleanup           - Clean up old sync backup files"
    echo "  help              - Show this help message"
    echo ""
    echo "Options:"
    echo "  --dry-run         - Show what would be done without actually doing it"
    echo "  --force           - Skip confirmation prompts (use with caution)"
    echo "  --keep-days N     - Keep sync backups for N days (default: 7)"
    echo ""
    echo "Examples:"
    echo "  $0 dev-to-staging                    # Sync dev to staging (with confirmation)"
    echo "  $0 staging-to-dev                    # Sync staging to dev (with confirmation)"
    echo "  $0 dev-to-staging --dry-run          # See what would be synced"
    echo "  $0 staging-to-dev --force            # Force sync without confirmation"
    echo "  $0 cleanup --keep-days 3             # Cleanup keeping last 3 days"
    echo ""
    echo "For more options, run: python scripts/backup/db_sync.py --help"
}

# Check if Python script exists
if [ ! -f "$SCRIPT_DIR/db_sync.py" ]; then
    echo "Error: db_sync.py not found in $SCRIPT_DIR"
    exit 1
fi

# Check if virtual environment is activated and activate if needed
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        echo "Warning: Virtual environment not found. Make sure dependencies are installed."
    fi
fi

# Parse command
case "${1:-help}" in
    "dev-to-staging")
        echo "🔄 Syncing development data to staging database..."
        python "$SCRIPT_DIR/db_sync.py" --dev-to-staging "${@:2}"
        ;;
    "staging-to-dev")
        echo "🔄 Syncing staging data to development database..."
        python "$SCRIPT_DIR/db_sync.py" --staging-to-dev "${@:2}"
        ;;
    "list")
        echo "📋 Listing sync backup files..."
        python "$SCRIPT_DIR/db_sync.py" --list "${@:2}"
        ;;
    "cleanup")
        echo "🧹 Cleaning up old sync backup files..."
        python "$SCRIPT_DIR/db_sync.py" --cleanup "${@:2}"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
