#!/usr/bin/env python3
"""
Test runner script for the Homeless Resource Directory application.

This script provides convenient ways to run different types of tests.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and display the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS")
        print(result.stdout)
    else:
        print("❌ FAILED")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Main test runner function."""
    print("🧪 Homeless Resource Directory - Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Get command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        print("\nAvailable test options:")
        print("1. all          - Run all tests")
        print("2. models       - Run model tests only")
        print("3. views        - Run view tests only")
        print("4. forms        - Run form tests only")
        print("5. search       - Run search tests only")
        print("6. permissions  - Run permission tests only")
        print("7. versions     - Run version control tests only")
        print("8. integration  - Run integration tests only")
        print("9. directory    - Run all directory app tests")
        print("10. importer    - Run importer app tests")
        print("11. audit       - Run audit app tests")
        print("12. coverage    - Run tests with coverage report")
        
        test_type = input("\nEnter test type (or 'all'): ").strip().lower()
    
    # Define test commands
    test_commands = {
        "all": "python manage.py test",
        "models": "python manage.py test directory.tests.test_models",
        "views": "python manage.py test directory.tests.test_views",
        "forms": "python manage.py test directory.tests.test_forms",
        "search": "python manage.py test directory.tests.test_search",
        "permissions": "python manage.py test directory.tests.test_permissions",
        "versions": "python manage.py test directory.tests.test_versions",
        "integration": "python manage.py test directory.tests.test_integration",
        "directory": "python manage.py test directory",
        "importer": "python manage.py test importer",
        "audit": "python manage.py test audit",
        "coverage": "python manage.py test --with-coverage --cover-package=directory,importer,audit",
    }
    
    if test_type in test_commands:
        success = run_command(test_commands[test_type], f"{test_type.title()} Tests")
        if success:
            print(f"\n🎉 {test_type.title()} tests completed successfully!")
        else:
            print(f"\n💥 {test_type.title()} tests failed!")
            sys.exit(1)
    else:
        print(f"❌ Unknown test type: {test_type}")
        print("Available options:", ", ".join(test_commands.keys()))
        sys.exit(1)


if __name__ == "__main__":
    main()
