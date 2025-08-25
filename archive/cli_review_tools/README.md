# CLI Review Tools

This directory contains command-line tools for reviewing and managing resources in the Homeless Resource Directory.

## 🎯 Overview

The CLI tools support a 3-step workflow for updating resources:
1. **Identify** a draft resource to update
2. **Research** the organization to find verified information  
3. **Update** the resource with verified data

## 🛠️ Available Tools

### `auto_update_random.py`

**Primary tool for the 3-step workflow**

Finds a random draft resource and optionally updates it with provided data.

**Features:**
- Finds random draft resource (step 1)
- Updates with provided data (step 3)
- Perfect for AI automation
- Can show resource without updating

**Usage:**
```bash
# Show random draft resource (step 1)
python auto_update_random.py --show-only

# Find random draft and update it (step 1 + 3)
python auto_update_random.py --data-file update_data.json --transition needs_review
```

**Options:**
- `--show-only`: Only display the resource, do not update
- `--data JSON_STRING`: JSON string with update data
- `--data-file PATH`: Path to JSON file with update data
- `--transition STATUS`: Transition to status after update (draft, needs_review, published)
- `--user USERNAME`: Username for the update (default: admin)

### `update_resource_noninteractive.py`

**Update specific resources by ID**

Updates a specific resource with provided data without user interaction.

**Features:**
- Update specific resources by ID
- Accept JSON data via command line or file
- No user interaction required
- Perfect for AI automation

**Usage:**
```bash
# Update with JSON data file
python update_resource_auto.py 123 --data-file update_data.json --transition needs_review

# Update with JSON string
python update_resource_auto.py 123 --data '{"name":"New Name","phone":"555-1234"}' --transition needs_review
```

**Options:**
- `resource_id`: ID of the resource to update
- `--data JSON_STRING`: JSON string with update data
- `--data-file PATH`: Path to JSON file with update data
- `--transition STATUS`: Transition to status after update
- `--user USERNAME`: Username for the update (default: admin)

## 📋 Quick Start

### Step 1: Find a Resource
```bash
python auto_update_random.py --show-only
```

### Step 2: Research the Organization
- Search online for current information
- Verify contact details, hours, services
- Create JSON data file with verified information

### Step 3: Update the Resource
```bash
python auto_update_random.py --data-file verified_data.json --transition needs_review
```

## 📝 JSON Data Format

```json
{
  "name": "Organization Name",
  "description": "Description of services provided...",
  "source": "Verified from official website",
  "phone": "(555) 123-4567",
  "website": "https://www.organization.org",
  "city": "City Name",
  "state": "KY",
  "hours_of_operation": "Monday-Friday 9:00 AM-5:00 PM",
  "notes": "VERIFIED: All information confirmed on 2024-01-15"
}
```

## ✅ Required Fields for "Needs Review"

A resource must have these fields to move to "needs review" status:
- ✅ **City**: Required
- ✅ **State**: Required (2-letter code)
- ✅ **Description**: Minimum 20 characters
- ✅ **Source**: Where the information came from

## 📖 Documentation

- **[PROCESS_GUIDE.md](PROCESS_GUIDE.md)** - Complete process documentation with search guidelines and update rules
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card with common commands

## Requirements

- Django project must be properly configured
- Virtual environment should be activated
- Database must contain draft resources

## Examples

### Find and Display a Resource
```bash
python auto_update_random.py --show-only
```

### Update with Data File
```bash
python auto_update_random.py --data-file update_data.json --transition needs_review
```

### Update Specific Resource
```bash
python update_resource_auto.py 123 --data-file update_data.json --transition needs_review
```
