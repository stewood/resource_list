#!/bin/bash
# Simple backup script wrapper for the Community Resource Directory.
#
# This script provides convenient shortcuts for common backup operations.
# It's a wrapper around the main backup_manager.py script.
#
# Usage:
#     ./scripts/backup/backup.sh local
#     ./scripts/backup/backup.sh staging
#     ./scripts/backup/backup.sh files
#     ./scripts/backup/backup.sh all
#     ./scripts/backup/backup.sh cleanup
#     ./scripts/backup/backup.sh list
#     ./scripts/backup/backup.sh help
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
    echo "Backup Script for Community Resource Directory"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  local     - Backup local development database"
    echo "  staging   - Backup staging database on Render"
    echo "  files     - Backup project files and directories"
    echo "  all       - Backup everything (local DB, staging DB, and files)"
    echo "  cleanup   - Clean up old backups (keep last 30 days)"
    echo "  list      - List all available backups"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local                    # Backup local database"
    echo "  $0 staging                  # Backup staging database"
    echo "  $0 all                      # Full backup"
    echo "  $0 cleanup                  # Cleanup old backups"
    echo "  $0 cleanup --keep-days 7    # Cleanup keeping last 7 days"
    echo ""
    echo "For more options, run: python scripts/backup/backup_manager.py --help"
}

# Check if Python script exists
if [ ! -f "$SCRIPT_DIR/backup_manager.py" ]; then
    echo "Error: backup_manager.py not found in $SCRIPT_DIR"
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
    "local")
        echo "🔄 Backing up local development database..."
        python "$SCRIPT_DIR/backup_manager.py" --local-db "${@:2}"
        ;;
    "staging")
        echo "🔄 Backing up staging database on Render..."
        python "$SCRIPT_DIR/backup_manager.py" --staging-db "${@:2}"
        ;;
    "files")
        echo "🔄 Backing up project files and directories..."
        python "$SCRIPT_DIR/backup_manager.py" --files "${@:2}"
        ;;
    "all")
        echo "🔄 Performing full backup (local DB, staging DB, and files)..."
        python "$SCRIPT_DIR/backup_manager.py" --all "${@:2}"
        ;;
    "cleanup")
        echo "🧹 Cleaning up old backups..."
        python "$SCRIPT_DIR/backup_manager.py" --cleanup "${@:2}"
        ;;
    "list")
        echo "📋 Listing available backups..."
        python "$SCRIPT_DIR/backup_manager.py" --list "${@:2}"
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
