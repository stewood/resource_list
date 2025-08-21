# Service Area Assignment Workflow

## Overview
This document outlines the complete workflow for identifying resources without service areas, researching their actual service coverage, and updating the database records with accurate geographic service areas.

## Prerequisites
- Virtual environment activated: `source venv/bin/activate`
- Access to the Django project database
- Internet access for researching organization websites

## Workflow Steps

### Phase 1: Automated Discovery and Research (Steps 1-4)

**⚠️ IMPORTANT: This phase can be fully automated. Complete all research before proceeding to Phase 2.**

#### Step 1: Find Resources Without Service Areas

**Command:**
```bash
python scripts/manage_service_areas.py find-without-areas
```

**What this does:**
- Searches the database for resources that have no coverage areas assigned
- Displays detailed information about the first resource found without service areas
- Shows all resource details including contact information, description, and notes

**Example Output:**
```
=== RESOURCE WITHOUT SERVICE AREAS ===
ID: 328
Name: Cumberland Valley Regional Housing Authority
Status: published
Category: Housing
Phone: 8009285971
Email: receptionist@cvrhaky.com
Website: https://www.cvrhaky.com
...
```

#### Step 2: Get Detailed Resource Information

**Command:**
```bash
python scripts/manage_service_areas.py details <resource_id>
```

**What this does:**
- Provides comprehensive information about a specific resource
- Shows current service areas (if any)
- Displays all resource fields including description, notes, and contact info

**Example:**
```bash
python scripts/manage_service_areas.py details 328
```

#### Step 3: Research Service Area Information

##### 3.1 Check Resource Description and Notes
- Review the resource description for mentions of service areas
- Look for geographic references in the notes field
- Identify any office locations mentioned

##### 3.2 Visit Official Website
- Navigate to the organization's official website
- Look for "Service Area," "Coverage Area," "Counties Served," or similar sections
- Check "About Us" pages for geographic information
- Review contact pages for multiple office locations

##### 3.3 Search for Additional Information
- Look for mentions of specific counties, cities, or regions
- Check for state-level service areas
- Identify any regional or multi-county service areas

#### Step 4: Find Coverage Areas in Database

##### 4.1 List Available Coverage Areas
**Command:**
```bash
python scripts/manage_service_areas.py list-coverage-areas --kind COUNTY --limit 1000
```

**What this does:**
- Shows all county-level coverage areas in the database
- Helps identify which counties exist in the system

##### 4.2 Search for Specific Counties
**Command:**
```bash
python manage.py shell -c "from directory.models import CoverageArea; counties = CoverageArea.objects.filter(kind='COUNTY'); target = counties.filter(name__icontains='COUNTY_NAME'); [print(f'ID: {c.id}, Name: {c.name}, State: {c.ext_ids.get(\"state_name\", \"Unknown\")}') for c in target]"
```

**Example for Kentucky counties:**
```bash
python manage.py shell -c "from directory.models import CoverageArea; counties = CoverageArea.objects.filter(kind='COUNTY'); harlan = counties.filter(name__icontains='harlan'); knox = counties.filter(name__icontains='knox'); whitley = counties.filter(name__icontains='whitley'); print('Harlan counties:'); [print(f'ID: {c.id}, Name: {c.name}') for c in harlan]; print('Knox counties:'); [print(f'ID: {c.id}, Name: {c.name}') for c in knox]; print('Whitley counties:'); [print(f'ID: {c.id}, Name: {c.name}') for c in whitley]"
```

##### 4.3 Verify State Information
**Command:**
```bash
python manage.py shell -c "from directory.models import CoverageArea; county = CoverageArea.objects.get(id=COUNTY_ID); print(f'County: {county.name}'); print(f'State Info: {county.ext_ids}')"
```

**What this does:**
- Shows the external IDs for a specific county
- Confirms which state the county belongs to
- Helps avoid assigning counties from the wrong state

### ⚠️ STOP HERE - APPROVAL REQUIRED ⚠️

**Before proceeding to Phase 2, you MUST present your findings and logic for approval:**

#### Required Approval Presentation Format:

**1. Initial Problem Identified:**
- Resource ID and name
- Current state (no service areas)
- Issues with current description

**2. Research Process & Logic:**
- Information gathered from database
- Official source verification (website, etc.)
- Database analysis results
- Coverage area IDs found

**3. Proposed Update Logic:**
- Specific counties to assign
- Reasoning for each assignment
- Quality improvements expected
- Source verification method

**4. Approval Request:**
- Clear statement of what will be updated
- Request for approval to proceed

**Example Approval Request:**
```
## Findings and Logic Summary

### Initial Problem Identified:
- Resource ID 328: Cumberland Valley Regional Housing Authority
- Issue: No service areas assigned despite serving multiple counties
- Description: Vague "serving multiple counties in southeastern Kentucky"

### Research Process & Logic:
1. Website Research: Official CVRHA website confirmed exact service area
2. Database Analysis: Found 3 Kentucky counties (Harlan ID 105, Knox ID 142, Whitley ID 127)
3. State Verification: All confirmed as Kentucky counties (FIPS 21)

### Proposed Update Logic:
- Replace "multiple counties" with exact 3 counties
- Use official website information over database description
- Assign: Harlan County (ID 105), Knox County (ID 142), Whitley County (ID 127)

## Approval Request
Do you approve this approach and want me to proceed with the database updates?
```

### Phase 2: Database Updates (Steps 5-6) - AFTER APPROVAL

**⚠️ ONLY PROCEED AFTER RECEIVING EXPLICIT APPROVAL**

#### Step 5: Add Service Areas to Resource

##### 5.1 Add Individual Coverage Areas
**Command:**
```bash
python scripts/manage_service_areas.py add <resource_id> <coverage_area_id>
```

**Example:**
```bash
python scripts/manage_service_areas.py add 328 105  # Add Harlan County
python scripts/manage_service_areas.py add 328 142  # Add Knox County
python scripts/manage_service_areas.py add 328 127  # Add Whitley County
```

**What this does:**
- Creates a ResourceCoverage association between the resource and coverage area
- Adds audit trail information (created_by, created_at, notes)
- Prevents duplicate associations

##### 5.2 Verify Service Areas Were Added
**Command:**
```bash
python scripts/manage_service_areas.py list <resource_id>
```

**What this does:**
- Shows all service areas currently assigned to the resource
- Displays coverage area details including external IDs
- Confirms the associations were created successfully

#### Step 6: Final Verification

##### 6.1 Confirm Resource No Longer Appears in "Without Areas" Search
**Command:**
```bash
python scripts/manage_service_areas.py find-without-areas
```

**What this does:**
- Verifies the resource no longer appears in the list of resources without service areas
- Shows the next resource that needs service area assignment

##### 6.2 Review Final Resource Details
**Command:**
```bash
python scripts/manage_service_areas.py details <resource_id>
```

**What this does:**
- Shows the complete updated resource information
- Displays all assigned service areas
- Confirms the update was successful

## Case Study: Cumberland Valley Regional Housing Authority

### Initial State
- **Resource ID:** 328
- **Name:** Cumberland Valley Regional Housing Authority
- **Service Areas:** None assigned
- **Description:** "serving multiple counties in southeastern Kentucky"

### Research Process
1. **Website Visit:** https://www.cvrhaky.com
2. **About Us Page:** Found specific statement: "residents of Harlan, Knox, and Whitley Counties"
3. **Office Locations:** Confirmed offices in Barbourville (Knox), Williamsburg (Whitley), and Harlan (Harlan)

### Database Search Results
- **Harlan County, KY:** ID 105 (FIPS: 21-095)
- **Knox County, KY:** ID 142 (FIPS: 21-121)
- **Whitley County, KY:** ID 127 (FIPS: 21-235)

### Final State
- **Service Areas:** 3 counties assigned
- **Accuracy:** Matches official website information
- **Audit Trail:** Complete with timestamps and user tracking

## Best Practices

### ⚠️ CRITICAL: Approval Workflow
1. **NEVER skip the approval step** - Always present findings before making changes
2. **Complete all research first** - Gather all information before requesting approval
3. **Document your sources** - Include website URLs, page references, and verification methods
4. **Present clear logic** - Explain why each coverage area should be assigned
5. **Wait for explicit approval** - Only proceed after receiving confirmation

### Research Guidelines
1. **Always check official websites** - Don't rely solely on database descriptions
2. **Look for specific geographic mentions** - Counties, cities, regions
3. **Verify state information** - Ensure counties are from the correct state
4. **Document your sources** - Note where information was found
5. **Cross-reference information** - Use multiple sources when possible
6. **For federal/national services** - Use the United States coverage area (ID: 7855) instead of assigning all individual states

### Database Guidelines
1. **Use specific coverage areas** - Prefer counties over vague regional descriptions
2. **For federal/national services** - Use United States coverage area (ID: 7855) rather than individual states
3. **Verify coverage area IDs** - Double-check before assigning
4. **Test associations** - Verify they were created successfully
5. **Update audit trail** - Ensure proper tracking of changes

### Quality Control
1. **Cross-reference information** - Use multiple sources when possible
2. **Verify against official sources** - Prefer organization websites over third-party listings
3. **Check for duplicates** - Ensure counties aren't assigned multiple times
4. **Test the workflow** - Verify the resource no longer appears in "without areas" search
5. **Present findings for review** - Always get approval before making changes

## Troubleshooting

### Common Issues
1. **County not found in database**
   - Check spelling variations
   - Search by partial name
   - Verify the county exists in the coverage areas table

2. **Wrong state county assigned**
   - Always check ext_ids for state information
   - Verify state_fips and state_name fields
   - Use the correct county ID for the target state

3. **Resource still appears in "without areas"**
   - Verify the add command was successful
   - Check for any error messages
   - Confirm the resource ID is correct

### Useful Commands for Debugging
```bash
# Check if a specific coverage area exists
python manage.py shell -c "from directory.models import CoverageArea; print(CoverageArea.objects.filter(name__icontains='COUNTY_NAME').count())"

# Verify resource-coverage associations
python manage.py shell -c "from directory.models import Resource, ResourceCoverage; resource = Resource.objects.get(id=RESOURCE_ID); print(f'Associations: {resource.resource_coverage_associations.count()}')"

# List all coverage areas for a resource
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); [print(f'{ca.name} ({ca.kind})') for ca in resource.coverage_areas.all()]"
```

## Handling Conflicting Information and Record Updates

### ⚠️ IMPORTANT: When Research Reveals Incorrect Database Information

During the research process, you may discover that the database record contains incorrect information beyond just missing service areas. Common issues include:

- **Incorrect location information** (wrong city, state, county)
- **Outdated contact information** (wrong phone, email, website)
- **Incorrect address information**
- **Outdated program descriptions**

### When to Update Records

**Update the record if:**
1. **Location information is wrong** - Organization is in a different city/county than listed
2. **Contact information is outdated** - Website, phone, or email has changed
3. **Address information is incorrect** - Street address, city, state, or postal code is wrong
4. **Service area information conflicts** - Database shows different service areas than research reveals

**Do NOT update if:**
1. **Minor formatting differences** - Same information in different format
2. **Additional information found** - Research reveals extra details not in database
3. **Uncertain information** - Cannot verify the accuracy of conflicting information

### How to Update Records Using Django ORM

#### Step 1: Check Current Record Information
```bash
# View current record details
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print('Current values:'); print(f'Address1: {resource.address1}'); print(f'City: {resource.city}'); print(f'State: {resource.state}'); print(f'County: {resource.county}'); print(f'Postal Code: {resource.postal_code}'); print(f'Website: {resource.website}')"
```

#### Step 2: Update the Record
```bash
# Update record with correct information
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); resource.address1 = 'NEW_ADDRESS'; resource.city = 'NEW_CITY'; resource.state = 'NEW_STATE'; resource.county = 'NEW_COUNTY'; resource.postal_code = 'NEW_POSTAL_CODE'; resource.website = 'NEW_WEBSITE'; resource.save(); print('Record updated successfully')"
```

**⚠️ IMPORTANT:** Avoid using exclamation marks (!) in the print statement as they can cause shell interpretation issues. Use periods or other punctuation instead.

#### Step 3: Verify the Update
```bash
# Verify the changes were applied
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print('After update:'); print(f'Address1: {resource.address1}'); print(f'City: {resource.city}'); print(f'State: {resource.state}'); print(f'County: {resource.county}'); print(f'Postal Code: {resource.postal_code}'); print(f'Website: {resource.website}')"
```

### Available Resource Fields for Updates

Common fields that can be updated:
- `address1` - Primary address line
- `address2` - Secondary address line  
- `city` - City name
- `state` - State abbreviation
- `county` - County name
- `postal_code` - ZIP/postal code
- `website` - Organization website URL
- `phone` - Phone number
- `email` - Email address
- `description` - Program description
- `notes` - Additional notes
- `hours_of_operation` - Operating hours
- `eligibility_requirements` - Who can access services

### Workflow Integration

**When updating records:**
1. **Include record updates in your approval request** - Mention any incorrect information found
2. **Document the changes** - Note what was wrong and what was corrected
3. **Update before adding service areas** - Fix location/contact info first, then add service areas
4. **Verify both updates** - Confirm both the record update and service area assignment worked

**Example approval request with record updates:**
```
## Findings and Logic Summary

### Initial Problem Identified:
- Resource ID 314: Bethany House Domestic Violence Shelter
- Issue: No service areas assigned AND incorrect location information
- Database shows: Lexington, KY (Fayette County)
- Research shows: Somerset, KY (Pulaski County) serving 10 counties

### Record Updates Needed:
- Location: Lexington, KY → Somerset, KY
- County: Fayette → Pulaski  
- Address: 123 Safety Street → P.O. Box 864
- Website: https://www.bethanyhouse.org → https://bethanyhouseinc.org

### Service Areas to Assign:
10 counties in Lake Cumberland ADD: Adair, Casey, Clinton, Cumberland, Green, McCreary, Pulaski, Russell, Taylor, Wayne

## Approval Request
Do you approve updating the record information AND assigning the service areas?
```

### Best Practices for Record Updates

1. **Always verify with official sources** - Use organization websites, government databases, or direct contact
2. **Document your sources** - Note where you found the correct information
3. **Update systematically** - Fix location/contact info first, then add service areas
4. **Test your changes** - Verify both the record update and service area assignment
5. **Include in approval process** - Mention record updates in your approval request

## Conclusion

This workflow ensures accurate and verifiable service area assignments for resources in the database. By following these steps systematically, you can:

1. **Identify** resources needing service areas
2. **Research** their actual service coverage
3. **Find** the correct coverage areas in the database
4. **Assign** the appropriate service areas
5. **Verify** the changes were successful

The process maintains data quality, provides audit trails, and ensures resources accurately reflect their real-world service areas.
