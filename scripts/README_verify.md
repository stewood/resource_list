# Resource Verification Script

The `verify.py` script provides automated resource verification for the Community Resource Directory using cursor-agent integration.

## Overview

This script identifies resources that need verification and runs cursor-agent to verify them following the established verification workflow. It supports configuration files, command-line options, and comprehensive logging.

## Features

- **Automated Verification**: Uses cursor-agent to verify resources following the verification workflow
- **Configuration Support**: Command-line arguments and configuration file support
- **Comprehensive Logging**: File and console logging with configurable verbosity
- **Graceful Shutdown**: Proper signal handling and cleanup
- **Progress Tracking**: Monitors verification progress and stops when no progress is made
- **Dry Run Mode**: Test configuration without executing cursor-agent
- **Error Handling**: Robust error handling and recovery

## Installation

1. Ensure cursor-agent is installed and available in your PATH
2. Ensure Django environment is properly configured
3. The script will automatically set up the Django environment

## Usage

### Basic Usage

```bash
# Run with default settings
python scripts/verify.py

# Run with custom settings
python scripts/verify.py --max-iterations 5 --timeout 600 --verbose
```

### Command Line Options

```bash
python scripts/verify.py [options]

Options:
  --max-iterations N    Maximum number of verification iterations (default: 10)
  --timeout N          Timeout in seconds for cursor-agent process (default: 300)
  --cursor-agent-path PATH  Path to cursor-agent executable (default: cursor-agent)
  --limit N            Maximum resources to process per iteration (default: 100)
  --config FILE        Configuration file path (optional)
  --verbose            Enable verbose logging
  --dry-run            Show what would be done without executing cursor-agent
  --help               Show help message
```

### Configuration File

Create a configuration file (e.g., `verification.conf`) based on the example:

```ini
[verification]
max_iterations = 10
timeout = 300
cursor_agent_path = cursor-agent
limit = 100
verbose = false
dry_run = false
```

Then run:

```bash
python scripts/verify.py --config verification.conf
```

### Examples

```bash
# Basic verification
python scripts/verify.py

# Verbose output with custom timeout
python scripts/verify.py --verbose --timeout 600

# Dry run to test configuration
python scripts/verify.py --dry-run --verbose

# Custom configuration file
python scripts/verify.py --config my_config.conf

# Limit iterations and resources per iteration
python scripts/verify.py --max-iterations 3 --limit 50
```

## How It Works

1. **Initialization**: Sets up logging, loads configuration, and registers signal handlers
2. **Resource Discovery**: Uses the MCP server function to find resources needing verification
3. **Progress Tracking**: Monitors verification progress and stops if no progress is made
4. **Cursor-Agent Integration**: Runs cursor-agent with the verification workflow
5. **Cleanup**: Properly terminates processes and logs results

## Verification Process

The script identifies resources that need verification based on:

- **Never Verified**: Resources that have never been verified
- **Overdue**: Resources past their verification due date
- **No Frequency Set**: Resources without verification frequency configured

It excludes resources with status "needs_review" as they're already in the review queue.

## Logging

Logs are written to both console and file (`logs/verification.log`). Log levels:

- **INFO**: General progress and status information
- **DEBUG**: Detailed debugging information (use --verbose)
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors that may cause failure

## Signal Handling

The script handles SIGINT (Ctrl+C) and SIGTERM gracefully:

- Terminates cursor-agent process if running
- Logs cleanup actions
- Exits cleanly

## Error Handling

The script includes comprehensive error handling for:

- **File Not Found**: cursor-agent executable not found
- **Permission Errors**: Insufficient permissions to execute cursor-agent
- **Timeout**: cursor-agent process exceeds timeout
- **Database Errors**: Issues with resource queries
- **Configuration Errors**: Invalid configuration files

## Performance Considerations

- Uses the MCP server's optimized database queries
- Implements pagination to handle large datasets
- Includes progress monitoring to prevent infinite loops
- Configurable limits to control resource usage

## Troubleshooting

### Common Issues

1. **cursor-agent not found**
   - Ensure cursor-agent is installed and in PATH
   - Use --cursor-agent-path to specify full path

2. **Permission denied**
   - Check cursor-agent executable permissions
   - Ensure script has necessary permissions

3. **Timeout issues**
   - Increase timeout with --timeout option
   - Check cursor-agent performance

4. **Database connection issues**
   - Verify Django settings
   - Check database connectivity

### Debug Mode

Use --verbose for detailed debugging information:

```bash
python scripts/verify.py --verbose
```

### Dry Run Mode

Test configuration without executing cursor-agent:

```bash
python scripts/verify.py --dry-run --verbose
```

## Configuration Reference

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| --max-iterations | int | 10 | Maximum verification iterations |
| Built-in timeout | int | 300 | Hardcoded 5-minute timeout |
| --cursor-agent-path | str | cursor-agent | Path to cursor-agent |
| --limit | int | 100 | Resources per iteration |
| --config | str | None | Configuration file path |
| --verbose | bool | False | Enable verbose logging |
| --dry-run | bool | False | Test mode without execution |

### Configuration File Format

```ini
[verification]
max_iterations = 10
cursor_agent_path = cursor-agent
limit = 100
verbose = false
dry_run = false
# Note: Timeout is hardcoded to 5 minutes (300 seconds) for safety
```

## Integration

The script integrates with:

- **MCP Server**: Uses `list_resources_needing_verification` function
- **Django**: Automatically sets up Django environment
- **Cursor-Agent**: Executes verification workflow
- **Logging System**: Uses Python logging module

## Security Considerations

- Validates cursor-agent path before execution
- Uses subprocess with proper security settings
- Handles input/output safely
- Implements proper cleanup on interruption

## Future Enhancements

Potential improvements:

- Parallel processing for multiple resources
- Webhook integration for notifications
- Metrics and analytics collection
- Integration with CI/CD pipelines
- Custom verification workflows

## Support

For issues or questions:

1. Check the logs in `logs/verification.log`
2. Use --verbose for detailed debugging
3. Use --dry-run to test configuration
4. Review the verification workflow documentation
