# Data Quality Improvement Process

## Overview

This document outlines the systematic process for identifying and fixing data quality issues in the Community Resource Directory database. The process uses Django shell commands to browse, analyze, and manipulate data directly.

**⚠️ IMPORTANT: This process involves direct database manipulation. Always obtain explicit user permission before making any changes to the database.**

## Process Steps

### 1. Data Exploration and Issue Identification

#### 1.1 Basic Database Overview
```bash
# Get total resource count and status distribution
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
print(f'Total resources: {Resource.objects.count()}');
print(f'Published: {Resource.objects.filter(status=\"published\").count()}');
print(f'Draft: {Resource.objects.filter(status=\"draft\").count()}');
print(f'Needs Review: {Resource.objects.filter(status=\"needs_review\").count()}');
"
```

#### 1.2 Sample Data Examination
```bash
# Examine first few resources for obvious issues
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
resources = Resource.objects.all()[:5]; 
[print(f'ID: {r.id}, Name: {r.name}, Phone: {r.phone}, City: {r.city}, State: {r.state}') for r in resources];
"
```

#### 1.3 Targeted Issue Searches

**Empty or Missing Contact Information:**
```bash
# Find resources with empty phone numbers
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
empty_phone = Resource.objects.filter(phone=''); 
print(f'Resources with empty phone: {empty_phone.count()}'); 
[print(f'ID: {r.id}, Name: {r.name}, City: {r.city}') for r in empty_phone[:10]];
"
```

**Problematic Location Data:**
```bash
# Find resources with placeholder or invalid location data
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
weird_cities = Resource.objects.filter(city__in=['Not applicable', 'Not provided', 'Statewide']); 
print(f'Resources with problematic city names: {weird_cities.count()}'); 
[print(f'ID: {r.id}, Name: {r.name}, City: {r.city}, State: {r.state}') for r in weird_cities];
"
```

**Invalid State Codes:**
```bash
# Find resources with non-standard state codes
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
weird_states = Resource.objects.filter(state__in=['NA', 'Not provided']); 
print(f'Resources with problematic state codes: {weird_states.count()}'); 
[print(f'ID: {r.id}, Name: {r.name}, City: {r.city}, State: {r.state}') for r in weird_states];
"
```

**Validation Issues:**
```bash
# Find resources that fail validation
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
invalid_resources = [];
for r in Resource.objects.all():
    try:
        r.clean();
    except Exception as e:
        invalid_resources.append((r.id, r.name, str(e)));
print(f'Resources with validation errors: {len(invalid_resources)}');
[print(f'ID: {id}, Name: {name}, Error: {error}') for id, name, error in invalid_resources[:5]];
"
```

### 2. Detailed Record Analysis

#### 2.1 Examine Specific Resource
```bash
# Get complete details for a specific resource
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
r = Resource.objects.get(id=28); 
print(f'ID: {r.id}');
print(f'Name: {r.name}');
print(f'Description: {r.description}');
print(f'Phone: {r.phone}');
print(f'Website: {r.website}');
print(f'City: {r.city}');
print(f'State: {r.state}');
print(f'Category: {r.category}');
print(f'Status: {r.status}');
print(f'Created: {r.created_at}');
print(f'Updated: {r.updated_at}');
"
```

#### 2.2 Check Related Data
```bash
# Check service types and category
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
r = Resource.objects.get(id=28); 
print(f'Service Types: {[st.name for st in r.service_types.all()]}');
print(f'Category: {r.category.name if r.category else \"None\"}');
"
```

### 3. Research and Verification

#### 3.1 Online Research
- Use browser tools to verify organization information
- Check official websites for current contact details
- Verify service descriptions and hours
- Confirm geographic coverage areas

#### 3.2 Cross-Reference with Other Sources
- Check if information matches other directories
- Verify against official government databases
- Compare with social media presence

### 4. Issue Analysis and Recommendation

#### 4.1 Document the Issue
- Describe what's wrong with the data
- Explain why it's problematic
- Provide evidence from research

#### 4.2 Suggest Solutions
- Propose specific data corrections
- Consider multiple approaches
- Explain the rationale for recommendations

#### 4.3 Consider Impact
- Will the change affect other records?
- Does it require validation rule changes?
- Are there test implications?

### 5. Implementation

**⚠️ CRITICAL: Before proceeding with any database changes, you MUST:**
1. **Get explicit permission from the user**
2. **Confirm the specific changes to be made**
3. **Explain the potential impact of the changes**
4. **Provide a summary of what will be modified**

#### 5.1 Make the Change
```bash
# Update a specific resource
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
r = Resource.objects.get(id=28); 
r.city = 'New City Name';
r.state = 'KY';
r.save();
print(f'Updated {r.name}');
"
```

#### 5.2 Bulk Updates (if needed)
```bash
# Update multiple resources with same issue
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
problematic = Resource.objects.filter(city='Old Value'); 
print(f'Updating {problematic.count()} resources...'); 
problematic.update(city='New Value'); 
print('✅ Update completed');
"
```

### 6. Validation and Testing

#### 6.1 Verify the Fix
```bash
# Test that the updated resource passes validation
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
r = Resource.objects.get(id=28); 
r.clean(); 
print('✅ Resource passes validation');
"
```

#### 6.2 Run Tests
```bash
# Run relevant test suites
source venv/bin/activate && python run_tests.py models
source venv/bin/activate && python run_tests.py forms
```

#### 6.3 Check for Side Effects
```bash
# Verify no other resources were affected
source venv/bin/activate && python manage.py shell -c "
from directory.models import Resource; 
print(f'Total resources: {Resource.objects.count()}');
print(f'Published: {Resource.objects.filter(status=\"published\").count()}');
"
```

## Common Issues and Solutions

### Contact Information Issues
- **Empty phone numbers**: Research current contact info
- **Invalid phone formats**: Normalize to digits only
- **Broken websites**: Check for new URLs or remove if defunct

### Location Data Issues
- **Placeholder values**: Remove or replace with actual data
- **Invalid state codes**: Use standard 2-letter codes
- **Missing city/state**: Research actual location or leave blank
- **National services**: Should have empty city and state fields (correct)
- **Statewide services**: Should have state filled in but empty city field
- **Local services**: Should have both city and state filled in

### Service Information Issues
- **Outdated descriptions**: Update with current service details
- **Incorrect categories**: Reclassify based on actual services
- **Missing service types**: Add appropriate service type tags
- **New service categories**: Create appropriate categories for specialized services (e.g., Animal Care)
- **New service types**: Create appropriate service types for specialized services (e.g., Pet Care)

### Verification Issues
- **Expired verification**: Re-verify with current information
- **Missing verifier**: Assign appropriate user
- **Outdated source**: Update source information

## Tools and Commands Reference

### Django Shell Commands
```bash
# Activate environment and start shell
source venv/bin/activate && python manage.py shell -c "COMMAND"

# Import models
from directory.models import Resource, TaxonomyCategory, ServiceType

# Basic queries
Resource.objects.all()
Resource.objects.filter(status='published')
Resource.objects.get(id=123)

# Count queries
Resource.objects.count()
Resource.objects.filter(city='London').count()

# Update operations
Resource.objects.filter(id=123).update(city='New City')
r = Resource.objects.get(id=123); r.city = 'New City'; r.save()
```

### Validation Testing
```bash
# Test individual resource validation
r = Resource.objects.get(id=123); r.clean()

# Test form validation
from directory.forms import ResourceForm
form = ResourceForm(data=form_data); form.is_valid()
```

### Test Execution
```bash
# Run specific test categories
python run_tests.py models
python run_tests.py forms
python run_tests.py views

# Run all tests
python run_tests.py
```

## Documentation Requirements

For each data quality improvement:

1. **Issue Description**: What was wrong and why it mattered
2. **Research Process**: How the correct information was verified
3. **Solution Implemented**: What changes were made
4. **Testing Results**: How the fix was validated
5. **Impact Assessment**: What other systems or data were affected

## Best Practices

1. **ALWAYS get user permission before making any database changes**
2. **Always research before making changes**
3. **Document the rationale for changes**
4. **Test thoroughly before and after changes**
5. **Consider the impact on related data**
6. **Use bulk operations for similar issues**
7. **Maintain data integrity and consistency**
8. **Follow established naming conventions**
9. **Verify changes don't break validation rules**

## Emergency Procedures

If a change causes unexpected issues:

1. **Stop immediately** if tests fail
2. **Revert changes** using Django shell commands
3. **Analyze the problem** before retrying
4. **Update this document** with lessons learned
5. **Consider creating a backup** before major changes
6. **Notify the user immediately** of any issues or unexpected outcomes

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Author**: Data Quality Team
