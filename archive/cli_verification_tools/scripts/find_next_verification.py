#!/usr/bin/env python3
"""
Resource Verification Finder - Project Root Wrapper

This is a simple wrapper script that runs the verification finder tool
from the project root directory.

Usage:
    python find_next_verification.py
"""

import subprocess
import sys
import os

def main():
    """Run the verification finder tool."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the actual verification finder script
    verification_script = os.path.join(script_dir, 'docs', 'verification', 'find_next_verification.py')
    
    # Check if the script exists
    if not os.path.exists(verification_script):
        print("❌ Error: Verification script not found!")
        print(f"Expected location: {verification_script}")
        sys.exit(1)
    
    # Run the verification script
    try:
        result = subprocess.run([sys.executable, verification_script], 
                              cwd=script_dir, 
                              check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running verification script: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Python interpreter not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()
