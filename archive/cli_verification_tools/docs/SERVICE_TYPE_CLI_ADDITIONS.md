# Service Type CLI Commands - New Additions

## Overview

You were absolutely correct! The CLI was missing dedicated commands for managing **services offered** (ServiceType model). I've now added comprehensive service type management capabilities to your resource CLI tool.

## 🆕 New Commands Added

### 1. **List Services** (`list-services`)
List all available service types with filtering, pagination, and sorting.

```bash
# List all service types (default: 50 per page)
python manage.py resource_cli list-services

# List with pagination
python manage.py resource_cli list-services --limit=25 --offset=0

# Search for specific service types
python manage.py resource_cli list-services --search="Crisis"

# Sort by creation date (newest first)
python manage.py resource_cli list-services --sort=created_at --order=desc
```

### 2. **Show Service** (`show-service`)
Display detailed information about a specific service type.

```bash
# Show service type details
python manage.py resource_cli show-service 15

# Show service type with ID 23
python manage.py resource_cli show-service 23
```

### 3. **Create Service** (`create-service`)
Create new service types interactively or from JSON input.

```bash
# Interactive creation
python manage.py resource_cli create-service

# Create from JSON
python manage.py resource_cli create-service --json='{"name":"Crisis Intervention","description":"Immediate assistance for crisis situations"}'
```

### 4. **Update Service** (`update-service`)
Update existing service types with field-level changes.

```bash
# Update individual fields
python manage.py resource_cli update-service 15 --description="Updated description"
python manage.py resource_cli update-service 15 --name="New Service Name"

# Bulk update with JSON
python manage.py resource_cli update-service 15 --json='{"name":"Updated Name","description":"Updated description"}'
```

## 🔧 Enhanced Resource Update Commands

The existing `update` command now supports managing which services a resource offers:

### **Add Service Types to Resources**
```bash
# Add specific service types to a resource
python manage.py resource_cli update 123 --add-service-types="Crisis Intervention,Case Management"

# Add by ID
python manage.py resource_cli update 123 --add-service-types="15,23"
```

### **Remove Service Types from Resources**
```bash
# Remove specific service types from a resource
python manage.py resource_cli update 123 --remove-service-types="Crisis Intervention"

# Remove by ID
python manage.py resource_cli update 123 --remove-service-types="15"
```

### **Replace All Service Types**
```bash
# Replace all service types with new ones
python manage.py resource_cli update 123 --set-service-types="Emergency Shelter,Food Assistance"
```

### **Clear All Service Types**
```bash
# Remove all service types from a resource
python manage.py resource_cli update 123 --clear-service-types
```

## 📊 Complete Service Type Management Workflow

### **1. Discover Available Services**
```bash
# See what service types exist
python manage.py resource_cli list-services

# Search for specific services
python manage.py resource_cli list-services --search="Mental Health"
```

### **2. Create New Service Types**
```bash
# Create a new service type for your organization
python manage.py resource_cli create-service --json='{
  "name": "Peer Support Groups",
  "description": "Support groups led by individuals with lived experience"
}'
```

### **3. Assign Services to Resources**
```bash
# Add multiple services to a resource
python manage.py resource_cli update 123 --add-service-types="Peer Support Groups,Crisis Intervention"

# Replace all services with new ones
python manage.py resource_cli update 123 --set-service-types="Emergency Shelter,Case Management"
```

### **4. Manage Service Type Details**
```bash
# Update service type descriptions
python manage.py resource_cli update-service 15 --description="Enhanced description with more details"

# Show which resources use a service
python manage.py resource_cli show-service 15
```

## 🎯 Key Features

### **Flexible Input Methods**
- **Names**: Use human-readable names like "Crisis Intervention"
- **IDs**: Use numeric IDs like "15" for precise targeting
- **Mixed**: Combine both in the same command

### **Smart Matching**
- **Case-insensitive**: "crisis intervention" matches "Crisis Intervention"
- **Partial matches**: "Crisis" finds "Crisis Intervention", "Crisis Counseling"
- **Duplicate handling**: Warns when multiple matches found

### **Comprehensive Management**
- **Add**: Add new services without affecting existing ones
- **Remove**: Remove specific services selectively
- **Replace**: Completely replace all services with new set
- **Clear**: Remove all services from a resource

### **Audit Trail**
- All changes are logged with timestamps
- Maintains data integrity and history

## 🔍 Example Use Cases

### **Scenario 1: Setting Up a New Crisis Center**
```bash
# 1. Create the crisis intervention service type
python manage.py resource_cli create-service --json='{
  "name": "Crisis Intervention",
  "description": "Immediate assistance for individuals in crisis situations"
}'

# 2. Create the resource
python manage.py resource_cli create --json='{
  "name": "London Crisis Center",
  "category": "Mental Health"
}'

# 3. Assign the service type
python manage.py resource_cli update 123 --add-service-types="Crisis Intervention"
```

### **Scenario 2: Updating an Existing Resource**
```bash
# 1. See current services
python manage.py resource_cli show 123

# 2. Add new services
python manage.py resource_cli update 123 --add-service-types="Case Management,Peer Support"

# 3. Remove outdated services
python manage.py resource_cli update 123 --remove-service-types="Old Service Name"
```

### **Scenario 3: Bulk Service Type Management**
```bash
# 1. List all available services
python manage.py resource_cli list-services

# 2. Update multiple resources with same services
python manage.py resource_cli update 123 --set-service-types="Emergency Shelter,Food Assistance"
python manage.py resource_cli update 124 --set-service-types="Emergency Shelter,Food Assistance"
python manage.py resource_cli update 125 --set-service-types="Emergency Shelter,Food Assistance"
```

## 🧪 Testing

I've created a test script to verify the new functionality:

```bash
# Run the test script
python test_service_type_commands.py
```

This will test:
- Listing service types
- Creating new service types
- Updating service types
- Assigning services to resources
- Removing services from resources

## 📚 Integration with Existing Commands

The new service type commands integrate seamlessly with your existing CLI:

- **Consistent JSON output** format
- **Same authentication** requirements
- **Unified error handling** and validation
- **Compatible with** existing resource management workflows

## 🎉 What This Solves

Before these additions, you could:
- ✅ View service types when showing resources
- ❌ List all available service types
- ❌ Create new service types
- ❌ Update service type details
- ❌ Manage which services a resource offers
- ❌ Bulk assign/remove services from resources

Now you have **complete service type management** capabilities that mirror your existing service area management!

## 🚀 Next Steps

1. **Test the new commands** with the test script
2. **Explore your existing service types** with `list-services`
3. **Create new service types** as needed for your organization
4. **Assign services to resources** using the enhanced update commands
5. **Integrate into your workflows** for comprehensive resource management

Your CLI now provides **full CRUD operations** for both resources AND the services they offer! 🎯
