#!/usr/bin/env python3
"""
Test runner for the Homeless Resource Directory.

This script provides an optimized way to run Django tests with various options
for coverage, parallel execution, and verbosity.
"""

import os
import sys
import subprocess
import argparse
import re

def run_tests(test_type=None, parallel=True, keepdb=True, coverage=False, verbose=False):
    """Run Django tests with optimized settings."""
    
    # Set test settings environment variable
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'resource_directory.test_settings'
    
    if coverage:
        # Use coverage command for coverage reporting
        cmd = ["coverage", "run", "--source=directory,importer,audit", "manage.py", "test"]
    else:
        # Build the command
        cmd = ["python", "manage.py", "test"]
    
    # Add test type if specified
    if test_type:
        cmd.append(test_type)
    
    # Add options
    if parallel:
        cmd.extend(["--parallel"])
    if keepdb:
        cmd.extend(["--keepdb"])
    if verbose:
        cmd.extend(["--verbosity=2"])
    
    # Run the command
    try:
        # Run with stderr redirected to capture and filter output
        result = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
        
        # Filter and display output
        output_lines = result.stdout.split('\n')
        filtered_lines = []
        
        for line in output_lines:
            # Skip lines that contain large HTML content
            if len(line) > 1000 or '<html' in line.lower() or '<!doctype' in line.lower():
                continue
            # Skip lines that are just HTML tags
            if re.match(r'^<[^>]+>$', line.strip()):
                continue
            # Include important test output
            if any(keyword in line.lower() for keyword in ['test', 'fail', 'error', 'assertion', 'exception', 'traceback', 'ok', 'failed', 'passed']):
                filtered_lines.append(line)
            # Include lines that are not too long
            elif len(line) < 200:
                filtered_lines.append(line)
        
        # Print filtered output
        print('\n'.join(filtered_lines))
        
        # If there was stderr output, show it (usually contains the actual errors)
        if result.stderr:
            print("\n=== STDERR OUTPUT ===")
            stderr_lines = result.stderr.split('\n')
            for line in stderr_lines:
                if len(line) < 500:  # Filter out very long lines
                    print(line)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        
        # Show filtered stdout
        if e.stdout:
            output_lines = e.stdout.split('\n')
            filtered_lines = []
            for line in output_lines:
                if len(line) < 1000 and not '<html' in line.lower():
                    filtered_lines.append(line)
            print('\n'.join(filtered_lines))
        
        # Show stderr (usually contains the actual error)
        if e.stderr:
            print("\n=== ERROR OUTPUT ===")
            stderr_lines = e.stderr.split('\n')
            for line in stderr_lines:
                if len(line) < 500:
                    print(line)
        
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Django tests with optimized settings")
    parser.add_argument("--test-type", help="Specific test type to run (e.g., directory.tests.test_models)")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel test execution")
    parser.add_argument("--no-keepdb", action="store_true", help="Don't keep test database between runs")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    success = run_tests(
        test_type=args.test_type,
        parallel=not args.no_parallel,
        keepdb=not args.no_keepdb,
        coverage=args.coverage,
        verbose=args.verbose
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
