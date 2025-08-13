#!/usr/bin/env python3
"""
Test runner script for the Homeless Resource Directory.

This script provides convenient ways to run tests with optimized settings.
By default, it runs tests in parallel with database reuse for maximum speed.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type=None, parallel=True, keepdb=True, coverage=False, verbose=False):
    """Run Django tests with optimized settings."""
    
    if coverage:
        # Use coverage command for coverage reporting
        cmd = ["coverage", "run", "--source=directory,importer,audit", "manage.py", "test"]
    else:
        # Build the command
        cmd = ["python", "manage.py", "test"]
    
    # Add optimization flags
    if parallel:
        cmd.append("--parallel")
    if keepdb:
        cmd.append("--keepdb")
    if verbose:
        cmd.append("-v")
        cmd.append("2")
    
    # Add specific test types
    if test_type:
        if test_type == "all":
            cmd.extend(["directory", "importer", "audit"])
        elif test_type == "models":
            cmd.append("directory.tests.test_models")
        elif test_type == "views":
            cmd.append("directory.tests.test_views")
        elif test_type == "search":
            cmd.append("directory.tests.test_search")
        elif test_type == "integration":
            cmd.append("directory.tests.test_integration")
        elif test_type == "permissions":
            cmd.append("directory.tests.test_permissions")
        elif test_type == "versions":
            cmd.append("directory.tests.test_versions")
        elif test_type == "forms":
            cmd.append("directory.tests.test_forms")
        else:
            cmd.append(f"directory.tests.test_{test_type}")
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Optimizations: Parallel={parallel}, KeepDB={keepdb}")
    print("-" * 60)
    
    # Run the command
    try:
        result = subprocess.run(cmd, check=True)
        
        # Generate coverage report if requested
        if coverage and result.returncode == 0:
            print("\n" + "="*60)
            print("COVERAGE REPORT")
            print("="*60)
            subprocess.run(["coverage", "report"], check=True)
            print("\n" + "="*60)
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Django tests with optimized settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./run_tests.py                    # Run all tests with optimizations
  ./run_tests.py models             # Run only model tests
  ./run_tests.py --no-parallel      # Run tests sequentially
  ./run_tests.py --coverage         # Run with coverage report
  ./run_tests.py --verbose          # Verbose output
        """
    )
    
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["all", "models", "views", "search", "integration", "permissions", "versions", "forms"],
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )
    
    parser.add_argument(
        "--no-keepdb",
        action="store_true",
        help="Don't reuse test database"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Run tests
    success = run_tests(
        test_type=args.test_type,
        parallel=not args.no_parallel,
        keepdb=not args.no_keepdb,
        coverage=args.coverage,
        verbose=args.verbose
    )
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
