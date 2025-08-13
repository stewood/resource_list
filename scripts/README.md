# Scripts

This directory contains utility scripts for the Homeless Resource Directory project.

## Available Scripts

### update_existing_resources.py
A utility script for updating existing resource data in the database. This script can be used to:
- Update resource information in bulk
- Modify specific fields across multiple resources
- Perform data migrations

**Usage:**
```bash
python scripts/update_existing_resources.py
```

## Development Guidelines

- All scripts should include proper error handling
- Scripts should be idempotent when possible
- Include documentation for script parameters and usage
- Test scripts thoroughly before running on production data
