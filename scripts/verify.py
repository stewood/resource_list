#!/usr/bin/env python3
"""
Verification Check Script

This script checks for resources that need verification using the same logic
as the MCP server. It identifies resources that:
- Have never been verified
- Are overdue for verification based on their frequency settings
- Don't have a verification frequency set

Usage:
    python scripts/verify.py [options]

Options:
    --max-iterations N    Maximum number of verification iterations (default: 10)
    --cursor-agent-path PATH  Path to cursor-agent executable (default: cursor-agent)
    --limit N            Maximum resources to process per iteration (default: 100)
    --config FILE        Configuration file path (optional)
    --verbose            Enable verbose logging
    --dry-run            Show what would be done without executing cursor-agent
"""

import argparse
import configparser
import logging
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the Django project root to the Python path
django_root = Path(__file__).parent.parent
sys.path.insert(0, str(django_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resource_directory.settings")

import django
django.setup()

# Import the MCP server function to avoid code duplication
from mcp_server.tools.resource_tools import list_resources_needing_verification


# Configuration constants
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_CURSOR_AGENT_PATH = "cursor-agent"
DEFAULT_LIMIT = 100
DEFAULT_LOG_LEVEL = logging.INFO

# Global variables for cleanup
current_process: Optional[subprocess.Popen] = None


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else DEFAULT_LOG_LEVEL
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "verification.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce Django logging noise
    logging.getLogger('django').setLevel(logging.WARNING)


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file and command line arguments."""
    config = {
        'max_iterations': DEFAULT_MAX_ITERATIONS,
        'cursor_agent_path': DEFAULT_CURSOR_AGENT_PATH,
        'limit': DEFAULT_LIMIT,
        'verbose': False,
        'dry_run': False
    }
    
    # Load from config file if provided
    if config_file and Path(config_file).exists():
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        if 'verification' in parser:
            section = parser['verification']
            config.update({
                'max_iterations': section.getint('max_iterations', DEFAULT_MAX_ITERATIONS),
                'cursor_agent_path': section.get('cursor_agent_path', DEFAULT_CURSOR_AGENT_PATH),
                'limit': section.getint('limit', DEFAULT_LIMIT),
                'verbose': section.getboolean('verbose', False),
                'dry_run': section.getboolean('dry_run', False)
            })
    
    return config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Automated resource verification using cursor-agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify.py
  python scripts/verify.py --max-iterations 5 --verbose
  python scripts/verify.py --config verification.conf --dry-run
  python scripts/verify.py --limit 50
        """
    )
    
    parser.add_argument(
        '--max-iterations', type=int, default=DEFAULT_MAX_ITERATIONS,
        help=f'Maximum number of verification iterations (default: {DEFAULT_MAX_ITERATIONS})'
    )
    parser.add_argument(
        '--cursor-agent-path', default=DEFAULT_CURSOR_AGENT_PATH,
        help=f'Path to cursor-agent executable (default: {DEFAULT_CURSOR_AGENT_PATH})'
    )
    parser.add_argument(
        '--limit', type=int, default=DEFAULT_LIMIT,
        help=f'Maximum resources to process per iteration (default: {DEFAULT_LIMIT})'
    )
    parser.add_argument(
        '--config', type=str,
        help='Configuration file path (optional)'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would be done without executing cursor-agent'
    )
    
    return parser.parse_args()


def signal_handler(signum, _):
    """Handle interrupt signals gracefully."""
    global current_process
    logging.info(f"Received signal {signum}, cleaning up...")
    
    if current_process and current_process.poll() is None:
        logging.info("Terminating cursor-agent process...")
        current_process.terminate()
        try:
            current_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logging.warning("Force killing cursor-agent process...")
            current_process.kill()
    
    logging.info("Cleanup complete, exiting...")
    sys.exit(1)


def run_cursor_agent_verification(
    cursor_agent_path: str = DEFAULT_CURSOR_AGENT_PATH,
    dry_run: bool = False
) -> bool:
    """Run cursor-agent to verify resources following the verification workflow.
    
    Args:
        cursor_agent_path: Path to cursor-agent executable
        dry_run: If True, show what would be done without executing
        
    Returns:
        bool: True if verification completed successfully, False otherwise
    """
    global current_process
    
    logger = logging.getLogger(__name__)
    
    if dry_run:
        logger.info("🔍 DRY RUN: Would execute cursor-agent verification process")
        logger.info(f"Command: {cursor_agent_path} --model auto -f [verification prompt] -p --output-format text")
        logger.info("Built-in timeout: 5 minutes (300 seconds)")
        return True
    
    logger.info("🤖 Starting cursor-agent verification process...")
    logger.info("=" * 60)
    
    # Build the verification prompt with hardcoded 5-minute timeout
    verification_prompt = (
        "I want you to follow the process in the @mcp_server/VERIFICATION_WORKFLOW.md document "
        "and verify a resource. It is very important that you follow the document and that you "
        "verify all of the information. I do not have access to your tools so before any tool use "
        "say what tool you are going to use and what info you are sending. Also say what you got back.\n\n"
        "⏰ TIMEOUT WARNING: You have a maximum of 5 minutes (300 seconds) to complete the verification. "
        "If you don't finish within this time, the process will be terminated. Work efficiently and "
        "focus on the most critical verification steps.\n\n"
        "🚨 CRITICAL FINAL STEP - DO NOT FORGET: When you are completely finished with the "
        "verification process, you MUST print exactly this: <||END||> - this is how the script "
        "knows you are done. This is the most important part - the script will hang forever if "
        "you don't print this!\n\n"
        "REMINDER: Your very last line must be: <||END||>. Make sure to add a reminder to print <||END||>"
    )
    
    # Command to run cursor-agent with the verification workflow
    cmd = [
        cursor_agent_path,
        "--model", "auto",
        "-f", verification_prompt,
        "-p",
        "--output-format", "text"
    ]
    
    try:
        logger.debug("Executing command: %s", " ".join(cmd))
        
        # Run the command and capture output in real-time
        current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            stdin=subprocess.DEVNULL,  # Prevent waiting for input
            cwd=str(django_root)  # Set working directory
        )
        
        # Read output line by line and check for termination marker
        end_found = False
        line_count = 0
        start_time = time.time()
        timeout_seconds = 300  # 5 minutes
        read_timeout = 1.0  # 1 second timeout for select
        
        while True:
            # Check if we've exceeded the total timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning("⏰ Process timed out after %.1f seconds, terminating...", elapsed)
                current_process.terminate()
                try:
                    current_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("Force killing cursor-agent process...")
                    current_process.kill()
                return False
            
            # Use select to check if data is available (non-blocking)
            ready, _, _ = select.select([current_process.stdout], [], [], read_timeout)
            
            if ready:
                # Data is available, read a line
                try:
                    line = current_process.stdout.readline()
                    if not line:  # EOF reached
                        break
                        
                    line_count += 1
                    print(line.rstrip())
                    
                    # Check if we've reached the end marker
                    if '<||END||>' in line:
                        logger.info("🏁 Verification process completed successfully!")
                        end_found = True
                        break
                    
                    # Log progress every 100 lines
                    if line_count % 100 == 0:
                        logger.debug("Processed %d lines in %.1f seconds", line_count, elapsed)
                        
                except Exception as e:
                    logger.error("Error reading from subprocess: %s", e)
                    break
            else:
                # No data available, check if process is still running
                if current_process.poll() is not None:
                    # Process has terminated
                    break
                # Continue waiting for data
        
        # If we didn't find the end marker, wait for the process to complete
        if not end_found:
            logger.info("⏳ Waiting for verification process to complete...")
            try:
                current_process.wait(timeout=10)  # Short timeout since we already waited 5 minutes
            except subprocess.TimeoutExpired:
                logger.warning("Process still running after timeout, terminating...")
                current_process.terminate()
                try:
                    current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Force killing cursor-agent process...")
                    current_process.kill()
                return False
        
        if current_process.returncode != 0:
            logger.error("❌ cursor-agent process exited with code %d", current_process.returncode)
            return False
        
        elapsed = time.time() - start_time
        logger.info("✅ Verification completed in %.1f seconds", elapsed)
        return True
        
    except FileNotFoundError:
        logger.error("❌ Error: cursor-agent command not found at '%s'. Please ensure cursor-agent is installed and in your PATH.", cursor_agent_path)
        return False
    except PermissionError:
        logger.error("❌ Error: Permission denied when trying to execute '%s'", cursor_agent_path)
        return False
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        if current_process and current_process.poll() is None:
            current_process.terminate()
        return False
    except Exception as e:
        logger.error("❌ Error running cursor-agent: %s", str(e))
        return False
    finally:
        current_process = None


def display_verification_summary(summary: Dict[str, int], current_count: int) -> None:
    """Display verification summary information."""
    logger = logging.getLogger(__name__)
    
    logger.info("📊 Verification Summary:")
    logger.info("   • Never verified: %d", summary['never_verified'])
    logger.info("   • Overdue: %d", summary['overdue'])
    logger.info("   • No frequency set: %d", summary['no_frequency_set'])
    logger.info("   • Total needing verification: %d", current_count)
    logger.info("")


def display_resources_preview(resources: list, current_count: int) -> None:
    """Display a preview of resources needing verification."""
    logger = logging.getLogger(__name__)
    
    preview_count = min(5, len(resources))
    logger.info("📋 Resources needing verification (showing first %d of %d):", preview_count, current_count)
    logger.info("-" * 60)
    
    for i, resource in enumerate(resources[:5], 1):
        verification = resource["verification"]
        status_emoji = {
            "never_verified": "🆕",
            "overdue": "⚠️",
            "no_frequency_set": "❓"
        }.get(verification["status"], "❓")
        
        logger.info("%2d. %s %s (ID: %d)", i, status_emoji, resource['name'], resource['id'])
        logger.info("    Status: %s", verification['status'])
        
        if resource["location"]["city"]:
            location = f"{resource['location']['city']}, {resource['location']['state']}"
            logger.info("    Location: %s", location)
        
        if resource["category"]:
            logger.info("    Category: %s", resource['category'])
        
        logger.info("")
    
    if current_count > 5:
        logger.info("... and %d more resources need verification", current_count - 5)


def main():
    """Main function to check for resources needing verification."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    config.update({
        'max_iterations': args.max_iterations,
        'cursor_agent_path': args.cursor_agent_path,
        'limit': args.limit,
        'verbose': args.verbose or config['verbose'],
        'dry_run': args.dry_run or config['dry_run']
    })
    
    # Set up logging
    setup_logging(config['verbose'])
    logger = logging.getLogger(__name__)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🔍 Starting automated verification process...")
    logger.info("=" * 60)
    logger.info("Configuration:")
    logger.info("  Max iterations: %d", config['max_iterations'])
    logger.info("  Built-in timeout: 5 minutes (300 seconds)")
    logger.info("  Cursor-agent path: %s", config['cursor_agent_path'])
    logger.info("  Limit per iteration: %d", config['limit'])
    logger.info("  Dry run: %s", config['dry_run'])
    logger.info("  Verbose: %s", config['verbose'])
    logger.info("")
    
    iteration = 1
    previous_count = None
    
    try:
        while iteration <= config['max_iterations']:
            logger.info("🔄 Iteration %d", iteration)
            logger.info("-" * 40)
            
            # Get resources needing verification using the MCP server function
            result = list_resources_needing_verification(limit=config['limit'])
            
            if result["status"] == "error":
                logger.error("❌ Error: %s", result['message'])
                sys.exit(1)
            
            data = result["data"]
            summary = data["verification_summary"]
            resources = data["resources"]
            current_count = data['pagination']['total_count']
            
            # Check if there are no resources to verify at all
            if current_count == 0 and iteration == 1:
                logger.info("✅ No resources need verification. All resources are up to date!")
                break
            
            # Display summary
            display_verification_summary(summary, current_count)
            
            # Check if we're done - no records need verification
            if current_count == 0:
                logger.info("✅ All resources have been verified! Process complete.")
                break
            
            # If this is not the first iteration, check if count dropped
            if iteration > 1 and previous_count is not None:
                if current_count >= previous_count:
                    logger.warning("📊 Count did not decrease (was %d, now %d)", previous_count, current_count)
                    logger.warning("🛑 Stopping verification process - no progress made.")
                    break
                else:
                    logger.info("📈 Progress made! Count decreased from %d to %d", previous_count, current_count)
            
            # Store current count for next iteration
            previous_count = current_count
            
            # Display preview of resources needing verification
            display_resources_preview(resources, current_count)
            
            logger.info("=" * 60)
            
            # Run cursor-agent verification
            logger.info("🚀 Starting automated verification process...")
            logger.info("")
            
            success = run_cursor_agent_verification(
                cursor_agent_path=config['cursor_agent_path'],
                dry_run=config['dry_run']
            )
            
            if success:
                logger.info("✅ Verification process completed successfully!")
                
                # Check if verification made progress (unless it's a dry run)
                if not config['dry_run']:
                    # Get updated count after verification
                    updated_result = list_resources_needing_verification(limit=config['limit'])
                    if updated_result["status"] == "success":
                        updated_count = updated_result["data"]['pagination']['total_count']
                        if updated_count == 0:
                            logger.info("🎉 All resources have been verified during this iteration!")
                            break
                        elif updated_count < current_count:
                            logger.info("📈 Verification progress: %d resources verified (was %d, now %d)", 
                                       current_count - updated_count, current_count, updated_count)
                        elif updated_count == current_count:
                            logger.warning("⚠️ No resources were verified in this iteration")
                        else:
                            logger.warning("⚠️ Unexpected: verification count increased (was %d, now %d)", 
                                         current_count, updated_count)
            else:
                logger.error("❌ Verification process failed!")
                sys.exit(1)
            
            iteration += 1
        
        if iteration > config['max_iterations']:
            logger.warning("⚠️ Reached maximum iterations (%d). Stopping for safety.", config['max_iterations'])
        
        logger.info("🏁 Automated verification process finished.")
        logger.info("📊 Final count: %d resources still need verification", current_count)
        
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("❌ Unexpected error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
