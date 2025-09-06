# CLI Verification Tools Archive

This directory contains the archived CLI verification tools that were previously used for manual resource verification. The MCP Server approach has been chosen as the preferred verification method.

## Archived Components

### Management Commands
- `management/commands/verify_cli.py` - Main verification CLI command
- `management/commands/resource_cli.py` - Resource CLI with verification features
- `management/commands/cli_utils.py` - CLI utility functions

### Services
- `services/cursor_agent_service.py` - Cursor agent for CLI verification
- `services/field_verification_service.py` - Field verification service
- `services/resource_verification_service.py` - Resource verification service
- `services/website_discovery_service.py` - Website discovery for CLI
- `services/output_formatter.py` - Output formatting for CLI

### Models & Utils
- `models/verification_models.py` - Verification data models
- `utils/verification_utils.py` - Verification utility functions
- `utils/json_utils.py` - JSON utilities for CLI
- `config/verification_config.py` - Verification configuration

### Documentation
- `docs/CLI_Documentation.md` - CLI documentation
- `docs/SERVICE_TYPE_CLI_ADDITIONS.md` - Service type CLI additions
- `docs/VERIFICATION_PROCESS.md` - Verification process documentation

### Scripts
- `scripts/find_unverified_resources.py` - Find unverified resources script
- `scripts/get_resource.py` - Get resource script
- `scripts/check_resource.py` - Check resource script
- `scripts/check_name_change.py` - Check name change script
- `scripts/check_previous_version.py` - Check previous version script
- `scripts/find_next_verification.py` - Find next verification script

## Archive Date
January 15, 2025

## Reason for Archive
Replaced with MCP Server approach for resource verification. The MCP Server provides better integration with external tools and more reliable verification capabilities.

## Current Verification Method
MCP Server located at `mcp_server/` directory.
