# Duplicate Resolution Guide

## Overview

This guide documents the comprehensive process for identifying, investigating, and resolving duplicate resources in the Homeless Resource Directory system. The process uses custom Django management commands to detect duplicates and safely merge them while preserving data integrity and audit trails.

## Table of Contents

1. [Duplicate Detection](#duplicate-detection)
2. [Investigation Process](#investigation-process)
3. [Complex Duplicate Scenarios](#complex-duplicate-scenarios)
4. [Primary Resource Selection](#primary-resource-selection)
5. [Merge Strategy](#merge-strategy)
6. [Multi-Step Merges](#multi-step-merges)
7. [Resource Renaming for Multiple Locations](#resource-renaming-for-multiple-locations)
8. [Execution Process](#execution-process)
9. [Post-Merge Validation](#post-merge-validation)
10. [Verification](#verification)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [Real-World Examples](#real-world-examples)
14. [Command Reference](#command-reference)
15. [Investigated Duplicates - Keep Separate](#investigated-duplicates---keep-separate)

## Duplicate Detection

### Running Duplicate Detection

The system uses a comprehensive duplicate detection command that identifies duplicates using multiple criteria:

```bash
# Run full duplicate detection
python manage.py find_duplicates

# Run with detailed information
python manage.py find_duplicates --show-details

# Run with specific confidence levels
python manage.py find_duplicates --confidence=high
python manage.py find_duplicates --confidence=medium
python manage.py find_duplicates --confidence=low

# Export results to CSV for analysis
python manage.py find_duplicates --export-csv
```

### Confidence Levels

- **High Confidence**: Exact name matches and contact information duplicates
- **Medium Confidence**: Phone, website, and email duplicates
- **Low Confidence**: Fuzzy name matches and address duplicates

### Detection Criteria

The system identifies duplicates using:

1. **Exact Name Matches**: Normalized resource names that are identical
2. **Contact Information**: Same phone numbers, email addresses, or websites
3. **Address Matches**: Same physical addresses
4. **Fuzzy Name Matching**: Similar names with configurable similarity threshold
5. **Combined Criteria**: Resources sharing multiple identifying characteristics

## Investigation Process

### Step 1: Identify Duplicate Groups

Run the duplicate detection to identify potential duplicates:

```bash
python manage.py find_duplicates --show-details
```

### Step 2: Investigate Specific Duplicates

For each duplicate group, investigate the details:

```bash
# Get detailed information about specific resources
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.filter(id__in=[ID1, ID2, ID3])
for r in resources:
    print(f'ID: {r.id}')
    print(f'Name: {r.name}')
    print(f'Phone: {r.phone}')
    print(f'Email: {r.email}')
    print(f'Website: {r.website}')
    print(f'Address: {r.address1}, {r.city}, {r.state}')
    print(f'Status: {r.status}')
    print(f'Service Types: {[st.name for st in r.service_types.all()]}')
    print(f'Notes: {r.notes[:200] if r.notes else \"N/A\"}')
    print('-' * 50)
"
```

### Step 3: Determine Merge Strategy

For each duplicate group, determine:

1. **Primary Resource**: Which resource should be kept (usually the most complete/verified)
2. **Complementary Information**: What unique information each duplicate provides
3. **Merge Notes**: Documentation of the merge decision

## Complex Duplicate Scenarios

### Same Contact Info, Different Names

When resources share phone numbers and addresses but have different names:

#### Investigation Steps

1. **Check for Business Name Variations**:
   ```bash
   # Check for additional identifying information
   python manage.py shell -c "
   from directory.models import Resource
   resources = Resource.objects.filter(phone='PHONE_NUMBER')
   for r in resources:
       print(f'ID {r.id}: {r.name}')
       print(f'  Notes: {r.notes[:200]}')
       print(f'  Website: {r.website}')
       print(f'  Service Types: {[st.name for st in r.service_types.all()]}')
       print(f'  Status: {r.status}')
   "
   ```

2. **Look for Evidence of**:
   - Legal name vs. operating name (e.g., "Miss Barbara's Child Care Center Inc" vs "A Time to Shine Child Care")
   - Business rebranding or name changes
   - Different programs under the same organization
   - Data entry errors

#### Decision Criteria

- **Prefer verified information**: Resources with citations, official websites, or social media presence
- **Choose current names**: If evidence suggests rebranding, use the more current name
- **Match official listings**: Use the name that appears in official business directories
- **Consider service types**: Ensure the name aligns with the services provided

### Inappropriate Service Type Combinations

Some service type combinations may indicate data quality issues:

#### Common Inappropriate Combinations

- **Child care centers** with "Domestic Violence" or "Substance Abuse Treatment"
- **Food pantries** with "Medical Care" or "Mental Health Counseling"
- **Churches** with "Transportation" (unless they specifically provide this service)
- **Schools** with "Medical Care" or "Substance Abuse Treatment"

#### Investigation Command

```bash
# Check for potentially inappropriate service types
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.filter(id__in=[ID1, ID2, ID3])
for r in resources:
    print(f'ID {r.id}: {r.name}')
    service_types = [st.name for st in r.service_types.all()]
    print(f'  Service Types: {service_types}')
    
    # Flag potentially inappropriate combinations
    if 'Child Care' in service_types and any(st in service_types for st in ['Domestic Violence', 'Substance Abuse Treatment']):
        print('  ⚠️  WARNING: Child care with inappropriate service types')
    if 'Food Pantry' in service_types and any(st in service_types for st in ['Medical Care', 'Mental Health Counseling']):
        print('  ⚠️  WARNING: Food pantry with medical services')
"
```

## Internet Research for Complex Duplicates

When database investigation alone cannot resolve complex duplicate cases, use internet research to verify current status, contact information, and organizational details.

### When to Use Internet Research

Use internet research when you encounter:
- **Conflicting information** between duplicate entries
- **Different addresses** for the same organization name
- **Different service types** that seem incompatible
- **Missing or unclear contact information**
- **Suspected organization closures** or changes
- **Similar names** in different geographic locations

### Research Process

#### Step 1: Search for Organization Information

Use search engines to find current information about the organization:

**Search Strategy**:
```
"[Organization Name]" "[City]" "[State]" phone "[phone number]"
"[Organization Name]" "[City]" "[State]" address
"[Organization Name]" "[City]" "[State]" website
```

**Example Searches**:
- `"Cedaridge Ministries" "Williamsburg" "KY" phone "6065491373"`
- `"Wellness Recovery" "London" "KY" phone "6066180125"`
- `"House of Hope Ministry" "Louisville" "KY" phone "5025514270"`

#### Step 2: Check Multiple Sources

Verify information across multiple reliable sources:

**Primary Sources**:
- **Official websites** (organization's own website)
- **Social media pages** (Facebook, Instagram, LinkedIn)
- **Business directories** (Yelp, Google Business, Yellow Pages)
- **Government databases** (nonprofit registries, business licenses)

**Secondary Sources**:
- **News articles** about the organization
- **Reviews and ratings** (Google Reviews, Yelp)
- **Charity watchdog sites** (GuideStar, Charity Navigator)

#### Step 3: Verify Key Information

For each source, verify and document:

**Contact Information**:
- Phone numbers (current vs. database)
- Email addresses
- Physical addresses
- Website URLs

**Operational Status**:
- Active vs. closed/inactive
- Hours of operation
- Current services offered
- Recent activity (posts, updates, reviews)

**Organizational Details**:
- Official name variations
- Service types and programs
- Geographic coverage
- Target populations

#### Step 4: Document Research Findings

Create a research summary for each duplicate case:

```markdown
## Research Summary: [Organization Name]

### Sources Checked:
- [ ] Google Search
- [ ] Facebook Page
- [ ] Yelp Listing
- [ ] Official Website
- [ ] Other: ________

### Key Findings:
- **Status**: Active/Closed/Inactive
- **Current Address**: [Address]
- **Current Phone**: [Phone]
- **Current Website**: [URL]
- **Services**: [List of services]
- **Notes**: [Additional findings]

### Decision:
- [ ] Merge entries (keep primary ID: ___)
- [ ] Keep separate (different organizations)
- [ ] Archive all (organization closed)
- [ ] Need more research
```

### Research Tools and Commands

#### Browser Automation Commands

When using browser automation for research:

```bash
# Navigate to search engine
mcp_Playwright_browser_navigate --url "https://www.google.com"

# Search for organization
mcp_Playwright_browser_type --element "Search box" --text "[Organization Name] [City] [State] phone [phone number]"

# Click on relevant results
mcp_Playwright_browser_click --element "[Result description]"

# Extract information from pages
mcp_Playwright_browser_snapshot
```

#### Manual Research Checklist

For manual research, use this checklist:

- [ ] **Google Search**: Basic organization information
- [ ] **Facebook**: Current status and recent activity
- [ ] **Yelp**: Business details and reviews
- [ ] **Official Website**: Services and contact info
- [ ] **Business Directories**: Verification of details
- [ ] **News Articles**: Recent developments or closures

### Decision-Making Based on Research

#### Merge When Research Shows:
- **Same organization** with different name variations
- **Same location** with updated contact information
- **Same services** with expanded offerings
- **Recent rebranding** or name changes

#### Keep Separate When Research Shows:
- **Different organizations** with similar names
- **Different geographic locations** (even if same name)
- **Different service types** or target populations
- **Different ownership** or management

#### Rename and Keep Separate When Research Shows:
- **Same organization name** but **different geographic service areas**
- **Multiple locations** serving **different communities** with **separate contact information**
- **Branch offices** or **satellite locations** with **distinct operational areas**

**Naming Convention for Multiple Locations:**
When an organization has multiple locations serving different geographic areas, rename each entry to clearly indicate the service area:

**Examples:**
- "Food Pantry" serving Corbin → "Food Pantry of Corbin"
- "Food Pantry" serving London → "Food Pantry of London"
- "Community Center" serving Manchester → "Community Center of Manchester"
- "Health Clinic" serving Barbourville → "Health Clinic of Barbourville"

**Criteria for Renaming:**
- ✅ **Different addresses** for each location
- ✅ **Different contact information** (phone, email, website)
- ✅ **Different geographic service areas** or communities
- ✅ **Separate operational management** or hours
- ❌ **Same location** with multiple phone numbers
- ❌ **Same organization** with updated contact info

**Process for Renaming:**
1. **Investigate** each location's service area and contact information
2. **Verify** they serve different geographic communities
3. **Rename** each entry to include the geographic identifier
4. **Update notes** to clarify the specific service area
5. **Keep separate** as distinct resources for different communities

#### Archive When Research Shows:
- **Organization permanently closed**
- **No longer providing services**
- **Merged into another organization**
- **Outdated or incorrect information**

### Example Research Cases

#### Case 1: Cedaridge Ministries
**Research Findings**:
- Facebook page: "We are no longer in business" (August 2023)
- Yelp: Address 537 S 10th St, Williamsburg, KY
- Status: Permanently closed

**Decision**: Archive all entries with closure information

#### Case 2: Wellness Recovery
**Research Findings**:
- Yelp: Active at 1114 Reuben St Ste 4, London, KY
- Phone: (606) 618-0125 verified
- Services: Addiction Medicine, Rehabilitation Center
- Status: Active business

**Decision**: Merge entries, keep most complete information

#### Case 3: House of Hope Ministry
**Research Findings**:
- Louisville: Active women's shelter at 1157 Dixie Hwy
- London: Different organization with limited info
- Different services and locations

**Decision**: Keep separate - different organizations

#### Case 4: Food Pantry Multiple Locations
**Research Findings**:
- Corbin location: 123 Main St, Corbin, KY - Phone: (606) 123-4567
- London location: 456 Oak Ave, London, KY - Phone: (606) 987-6543
- Both serve different communities with separate contact information
- Same organization name but different geographic service areas

**Decision**: Rename and keep separate
- "Food Pantry" (Corbin) → "Food Pantry of Corbin"
- "Food Pantry" (London) → "Food Pantry of London"

### Best Practices

1. **Always verify current status** before making merge decisions
2. **Check multiple sources** to confirm information
3. **Document research process** for audit trail
4. **Consider geographic separation** when names are similar
5. **Preserve historical information** about closed organizations
6. **Update contact information** based on current findings
7. **Flag entries needing follow-up** if research is inconclusive

### Common Research Challenges

#### Limited Online Presence
- **Solution**: Check government databases, local directories
- **Fallback**: Contact organization directly if possible

#### Conflicting Information
- **Solution**: Prioritize official sources over user-generated content
- **Decision**: Use most recent and authoritative information

#### Similar Names in Different Locations
- **Solution**: Verify each location independently
- **Decision**: Keep separate unless clearly the same organization

#### Outdated Information
- **Solution**: Look for recent activity indicators
- **Decision**: Archive outdated entries, keep current information

## Primary Resource Selection

### Enhanced Decision-Making Criteria

Use this decision tree to choose the primary resource:

#### 1. Verification Status (Highest Priority)
- ✅ **Verified information** with citations, official websites, or social media presence
- ✅ **Cross-referenced data** from multiple sources
- ❌ **Unverified or questionable** information

#### 2. Completeness (Second Priority)
- ✅ **Complete contact information** (phone, email, website, address)
- ✅ **Detailed operational notes** with hours, requirements, etc.
- ✅ **Comprehensive service types** that make sense for the organization
- ❌ **Missing or incomplete** information

#### 3. Recency (Third Priority)
- ✅ **Recently updated** information
- ✅ **Current business status** and active operations
- ❌ **Outdated or historical** information

#### 4. Name Appropriateness (Fourth Priority)
- ✅ **Current operating name** or official business name
- ✅ **Name matches services** provided
- ❌ **Outdated, incorrect, or generic** names

### Selection Criteria for Primary Resource

Choose the primary resource based on:

- **Verification Status**: Prefer verified resources with citations
- **Completeness**: Most complete contact information
- **Recency**: Most recently updated
- **Service Types**: Most comprehensive and appropriate service offerings
- **Notes/Description**: Most detailed operational information
- **Name Accuracy**: Most current and appropriate name

## Merge Strategy

### Pre-Merge Analysis

Before merging, analyze what information will be consolidated:

1. **Service Types**: Combine all unique service types (review for appropriateness)
2. **Contact Information**: Merge phone numbers, emails, websites
3. **Descriptions**: Combine complementary descriptions
4. **Notes**: Preserve important operational notes
5. **Hours/Requirements**: Consolidate operational details

### Merge Process

The merge process:

1. **Creates Backup**: Automatically creates a version backup of the primary resource
2. **Consolidates Data**: Merges complementary information from duplicates
3. **Archives Duplicates**: Soft-archives duplicate resources with clear reasons
4. **Logs Operations**: Creates comprehensive audit trail
5. **Updates Primary**: Enhances the primary resource with merged data

## Multi-Step Merges

### When to Use Multi-Step Merges

Use multi-step merges when dealing with:
- Multiple duplicate groups that may be related
- Resources that share contact information across different name variations
- Complex scenarios requiring sequential consolidation

### Multi-Step Merge Strategy

1. **Identify Related Groups**:
   ```bash
   # Find all resources sharing the same contact information
   python manage.py shell -c "
   from directory.models import Resource
   phone = 'PHONE_NUMBER'
   resources = Resource.objects.filter(phone=phone)
   print(f'Resources with phone {phone}:')
   for r in resources:
       print(f'  ID {r.id}: {r.name} | Address: {r.address1}')
   "
   ```

2. **Plan the Merge Sequence**:
   - Start with the most obvious duplicates (same name, same contact)
   - Then address related resources (same contact, different names)
   - Always verify after each step before proceeding

3. **Example Multi-Step Process**:
   ```bash
   # Step 1: Merge obvious duplicates
   python manage.py merge_duplicates --primary-id=271 --duplicate-ids=126,168 --dry-run
   
   # Step 2: Verify first merge
   python manage.py find_duplicates --confidence=high
   
   # Step 3: Merge related resources
   python manage.py merge_duplicates --primary-id=153 --duplicate-ids=271 --dry-run
   
   # Step 4: Final verification
   python manage.py find_duplicates --confidence=high
   ```

## Resource Renaming for Multiple Locations

### When to Rename Resources

Rename resources when you discover:
- **Same organization name** but **different geographic service areas**
- **Multiple locations** with **separate contact information**
- **Branch offices** serving **different communities**

### Renaming Process

#### Step 1: Investigate Each Location
```bash
# Get detailed information about resources with same name
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.filter(name__icontains='FOOD_PANTRY_NAME')
for r in resources:
    print(f'ID: {r.id}')
    print(f'Name: {r.name}')
    print(f'Address: {r.address1}, {r.city}, {r.state}')
    print(f'Phone: {r.phone}')
    print(f'Service Area: {r.notes[:100]}')
    print('-' * 50)
"
```

#### Step 2: Verify Geographic Separation
- Check if locations serve different communities
- Verify different contact information
- Confirm separate operational areas

#### Step 3: Rename Resources
```bash
# Rename resources to include geographic identifiers
python manage.py shell -c "
from directory.models import Resource
# Rename Corbin location
corbin_resource = Resource.objects.get(id=CORBIN_ID)
corbin_resource.name = 'Food Pantry of Corbin'
corbin_resource.notes = corbin_resource.notes + '\\n\\nGEOGRAPHIC SERVICE AREA: Serves Corbin and surrounding communities.'
corbin_resource.save()
print(f'Renamed ID {CORBIN_ID} to: {corbin_resource.name}')

# Rename London location
london_resource = Resource.objects.get(id=LONDON_ID)
london_resource.name = 'Food Pantry of London'
london_resource.notes = london_resource.notes + '\\n\\nGEOGRAPHIC SERVICE AREA: Serves London and surrounding communities.'
london_resource.save()
print(f'Renamed ID {LONDON_ID} to: {london_resource.name}')
"
```

#### Step 4: Verify Renaming
```bash
# Check that duplicates are resolved
python manage.py find_duplicates --confidence=high

# Verify the renamed resources
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.filter(name__icontains='Food Pantry of')
for r in resources:
    print(f'ID {r.id}: {r.name} | Address: {r.address1}, {r.city}')
"
```

### Naming Convention Examples

| Original Name | Location | New Name |
|---------------|----------|----------|
| Food Pantry | Corbin | Food Pantry of Corbin |
| Food Pantry | London | Food Pantry of London |
| Community Center | Manchester | Community Center of Manchester |
| Health Clinic | Barbourville | Health Clinic of Barbourville |
| Salvation Army | Corbin | Salvation Army of Corbin |
| Salvation Army | London | Salvation Army of London |

### Pre-Merge and Post-Merge Checklists

#### Pre-Merge Checklist
- [ ] Identified all related duplicates
- [ ] Investigated each resource thoroughly
- [ ] Chosen primary resource based on criteria
- [ ] Documented merge reasoning
- [ ] Performed dry-run successfully
- [ ] Verified no conflicts with other operations
- [ ] Planned multi-step sequence (if needed)

#### Post-Merge Checklist
- [ ] Primary resource updated correctly
- [ ] Duplicates properly archived
- [ ] Audit trail created
- [ ] Service types reviewed for appropriateness
- [ ] Duplicate detection re-run
- [ ] No new duplicates introduced
- [ ] Data quality validated

## Execution Process

### Step 1: Dry Run

Always perform a dry run first to preview the merge:

```bash
python manage.py merge_duplicates \
    --primary-id=317 \
    --duplicate-ids=263,68,267 \
    --dry-run
```

### Step 2: Execute Merge

Once satisfied with the preview, execute the merge:

```bash
python manage.py merge_duplicates \
    --primary-id=317 \
    --duplicate-ids=263,68,267 \
    --merge-notes="Consolidated 4 High Street Baptist Church entries into single comprehensive record. Kept most complete version (ID 317) with verified information."
```

### Command Options

```bash
python manage.py merge_duplicates \
    --primary-id=<ID> \                    # ID of resource to keep
    --duplicate-ids=<ID1,ID2,ID3> \       # Comma-separated duplicate IDs
    --merge-notes="<notes>" \             # Documentation of merge
    --dry-run                             # Preview without making changes
```

## Post-Merge Validation

### Service Type Review

After merging, review the combined service types for appropriateness:

#### Check Service Type Logic

```bash
python manage.py shell -c "
from directory.models import Resource
resource = Resource.objects.get(id=<PRIMARY_ID>)
print(f'Name: {resource.name}')
print(f'Service Types: {[st.name for st in resource.service_types.all()]}')
# Manually review if service types make sense for this organization
"
```

#### Service Type Cleanup

If inappropriate service types are found:

```bash
# Remove inappropriate service types
python manage.py shell -c "
from directory.models import Resource, ServiceType
resource = Resource.objects.get(id=<PRIMARY_ID>)
inappropriate_types = ServiceType.objects.filter(name__in=['Domestic Violence', 'Medical Care'])
resource.service_types.remove(*inappropriate_types)
resource.save()
print(f'Updated service types: {[st.name for st in resource.service_types.all()]}')
"
```

### Data Quality Validation

#### Contact Information Validation

```bash
# Verify contact information consistency
python manage.py shell -c "
from directory.models import Resource
resource = Resource.objects.get(id=<PRIMARY_ID>)
print(f'Name: {resource.name}')
print(f'Phone: {resource.phone}')
print(f'Email: {resource.email}')
print(f'Website: {resource.website}')
print(f'Address: {resource.address1}, {resource.city}, {resource.state}')

# Check for consistency issues
if resource.phone and len(resource.phone) < 10:
    print('⚠️  WARNING: Phone number seems too short')
if resource.email and '@' not in resource.email:
    print('⚠️  WARNING: Email format seems invalid')
"
```

#### Notes Consolidation Review

```bash
# Review merged notes for clarity and completeness
python manage.py shell -c "
from directory.models import Resource
resource = Resource.objects.get(id=<PRIMARY_ID>)
print(f'Notes: {resource.notes}')
# Check for duplicate information or unclear formatting
"
```

## Verification

### Step 1: Verify Primary Resource

Check that the primary resource was properly updated:

```bash
python manage.py shell -c "
from directory.models import Resource
primary = Resource.objects.get(id=317)
print(f'Name: {primary.name}')
print(f'Phone: {primary.phone}')
print(f'Email: {primary.email}')
print(f'Service Types: {[st.name for st in primary.service_types.all()]}')
print(f'Notes: {primary.notes[:200] if primary.notes else \"N/A\"}')
"
```

### Step 2: Verify Duplicates Archived

Confirm duplicates were properly archived:

```bash
python manage.py shell -c "
from directory.models import Resource
archived = Resource.objects.all_including_archived().filter(id__in=[263, 68, 267])
for r in archived:
    print(f'ID {r.id}: {r.name} | Archived: {r.is_archived} | Reason: {r.archive_reason[:100]}')
"
```

### Step 3: Verify Audit Trail

Check that operations were properly logged:

```bash
python manage.py shell -c "
from directory.models import AuditLog
logs = AuditLog.objects.filter(action__in=['merge_duplicates', 'archive_duplicate']).order_by('-created_at')[:5]
for log in logs:
    print(f'{log.created_at}: {log.action} - {log.metadata}')
"
```

### Step 4: Re-run Duplicate Detection

Confirm duplicates are no longer detected:

```bash
python manage.py find_duplicates --confidence=high
```

## Best Practices

### Investigation Best Practices

1. **Always investigate thoroughly** before merging
2. **Document your decisions** in merge notes
3. **Consider service differences** - some "duplicates" may be different programs
4. **Check for verification status** - prefer verified resources
5. **Review contact information** - ensure accuracy
6. **Look for business name variations** - legal vs. operating names
7. **Validate service type appropriateness** - flag suspicious combinations

### Merge Best Practices

1. **Always use dry-run first** to preview changes
2. **Use descriptive merge notes** for audit trail
3. **Choose the most complete resource** as primary
4. **Preserve unique information** from duplicates
5. **Verify results** after each merge
6. **Review service types** for appropriateness after merging
7. **Plan multi-step sequences** for complex scenarios

### Data Integrity Best Practices

1. **Never delete resources** - always archive
2. **Maintain audit trails** for all operations
3. **Create version backups** before merging
4. **Use transaction safety** for all operations
5. **Document all decisions** in merge notes
6. **Validate data quality** after each operation
7. **Review merged content** for consistency

## Troubleshooting

### Common Issues

#### Issue: Resources Not Found
```bash
# Check if resources exist and are not already archived
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.all_including_archived().filter(id__in=[ID1, ID2])
for r in resources:
    print(f'ID {r.id}: {r.name} | Archived: {r.is_archived}')
"
```

#### Issue: Merge Fails
```bash
# Check for validation errors
python manage.py shell -c "
from directory.models import Resource
try:
    resource = Resource.objects.get(id=<ID>)
    resource.full_clean()
    print('Resource is valid')
except Exception as e:
    print(f'Validation error: {e}')
    # Check specific fields that might be causing issues
"
```

#### Issue: Duplicates Still Appear
```bash
# Check if resources were properly archived
python manage.py shell -c "
from directory.models import Resource
resources = Resource.objects.all_including_archived().filter(name__icontains='<NAME>')
for r in resources:
    print(f'ID {r.id}: {r.name} | Archived: {r.is_archived}')
"
```

#### Issue: Inappropriate Service Types After Merge
```bash
# Review and clean up service types
python manage.py shell -c "
from directory.models import Resource, ServiceType
resource = Resource.objects.get(id=<ID>)
print(f'Current service types: {[st.name for st in resource.service_types.all()]}')
# Manually identify inappropriate types and remove them
"
```

### Recovery Procedures

#### Restore from Backup
If a merge needs to be undone:

```bash
python manage.py shell -c "
from directory.models import ResourceVersion
# Find the backup version
versions = ResourceVersion.objects.filter(resource_id=<ID>, change_type='pre_merge_backup')
if versions.exists():
    backup = versions.first()
    print('Backup found, can restore from version data')
"
```

#### Unarchive Resources
To unarchive resources if needed:

```bash
python manage.py shell -c "
from directory.models import Resource
archived = Resource.objects.all_including_archived().filter(id__in=[ID1, ID2])
for resource in archived:
    resource.is_archived = False
    resource.archived_at = None
    resource.archived_by = None
    resource.archive_reason = ''
    resource.save()
    print(f'Unarchived resource {resource.id}')
"
```

#### Fix Service Type Issues
To correct inappropriate service types:

```bash
python manage.py shell -c "
from directory.models import Resource, ServiceType
resource = Resource.objects.get(id=<ID>)
# Remove inappropriate types
inappropriate = ServiceType.objects.filter(name__in=['Domestic Violence', 'Medical Care'])
resource.service_types.remove(*inappropriate)
# Add appropriate types
appropriate = ServiceType.objects.filter(name='Child Care')
resource.service_types.add(*appropriate)
resource.save()
print(f'Updated service types: {[st.name for st in resource.service_types.all()]}')
"
```

## Real-World Examples

### Example 1: Child Care Center Duplicates

**Scenario**: Multiple entries for the same child care center with different names and service types.

**Investigation Results**:
- ID 126: "Miss Barbara's Child Care Center Inc" - Mental Health Counseling
- ID 168: "Miss Barbara's Child Care Center Inc" - Education  
- ID 271: "Miss Barbara's Child Care Center Inc" - Multiple inappropriate types
- ID 153: "A Time to Shine Child Care" - Child Care (verified)

**Decision**: Merge all into ID 153 (verified information, appropriate service types)

**Process**: Two-step merge (126,168 → 271 → 153) with service type cleanup

**Commands Used**:
```bash
# Step 1: Merge obvious duplicates
python manage.py merge_duplicates --primary-id=271 --duplicate-ids=126,168 --merge-notes="Consolidated 3 Miss Barbara's Child Care Center Inc entries into single comprehensive record."

# Step 2: Merge related resources
python manage.py merge_duplicates --primary-id=153 --duplicate-ids=271 --merge-notes="Consolidated Miss Barbara's Child Care Center Inc into A Time to Shine Child Care. Kept verified information."

# Step 3: Clean up inappropriate service types
python manage.py shell -c "
from directory.models import Resource, ServiceType
resource = Resource.objects.get(id=153)
inappropriate = ServiceType.objects.filter(name__in=['Domestic Violence', 'Medical Care', 'Substance Abuse Treatment', 'Transportation'])
resource.service_types.remove(*inappropriate)
resource.save()
"
```

### Example 2: High Street Baptist Church

1. **Detect Duplicates**:
   ```bash
   python manage.py find_duplicates --show-details
   # Found 4 High Street Baptist Church entries
   ```

2. **Investigate Details**:
   ```bash
   python manage.py shell -c "
   from directory.models import Resource
   resources = Resource.objects.filter(id__in=[263, 68, 267, 317])
   for r in resources:
       print(f'ID {r.id}: {r.name} | Phone: {r.phone} | Email: {r.email}')
   "
   ```

3. **Choose Primary**: ID 317 (most complete, verified information)

4. **Dry Run**:
   ```bash
   python manage.py merge_duplicates \
       --primary-id=317 \
       --duplicate-ids=263,68,267 \
       --dry-run
   ```

5. **Execute Merge**:
   ```bash
   python manage.py merge_duplicates \
       --primary-id=317 \
       --duplicate-ids=263,68,267 \
       --merge-notes="Consolidated 4 High Street Baptist Church entries into single comprehensive record. Kept most complete version (ID 317) with verified information."
   ```

6. **Verify Results**:
   ```bash
   python manage.py find_duplicates --confidence=high
   # High Street Baptist Church no longer appears in duplicates
   ```

## Command Reference

### Duplicate Detection Commands

```bash
# Basic detection
python manage.py find_duplicates

# Detailed output
python manage.py find_duplicates --show-details

# Specific confidence level
python manage.py find_duplicates --confidence=high

# Export to CSV
python manage.py find_duplicates --export-csv

# Custom similarity threshold
python manage.py find_duplicates --threshold=0.9
```

### Merge Commands

```bash
# Dry run
python manage.py merge_duplicates \
    --primary-id=<ID> \
    --duplicate-ids=<ID1,ID2> \
    --dry-run

# Execute merge
python manage.py merge_duplicates \
    --primary-id=<ID> \
    --duplicate-ids=<ID1,ID2> \
    --merge-notes="<notes>"
```

### Verification Commands

```bash
# Check resource details
python manage.py shell -c "from directory.models import Resource; r = Resource.objects.get(id=<ID>); print(f'Name: {r.name}, Phone: {r.phone}')"

# Check archived resources
python manage.py shell -c "from directory.models import Resource; archived = Resource.objects.all_including_archived().filter(is_archived=True); print(f'Archived count: {archived.count()}')"

# Check audit logs
python manage.py shell -c "from directory.models import AuditLog; logs = AuditLog.objects.filter(action='merge_duplicates').order_by('-created_at')[:5]; [print(f'{log.created_at}: {log.metadata}') for log in logs]"

# Check service types
python manage.py shell -c "from directory.models import Resource; r = Resource.objects.get(id=<ID>); print(f'Service Types: {[st.name for st in r.service_types.all()]}')"
```

## Investigated Duplicates - Keep Separate

This section documents duplicate groups that have been thoroughly investigated and determined to be **legitimate separate resources** that should **NOT be merged**. These entries appear as duplicates due to shared contact information but serve different purposes, populations, or geographic areas.

### Purpose of This Section

- **Prevent re-investigation** of already-resolved cases
- **Document reasoning** for keeping resources separate
- **Provide guidance** for future duplicate resolution work
- **Maintain consistency** in decision-making

### How to Use This Section

1. **Before investigating duplicates**, check this list to avoid re-investigating known cases
2. **When new duplicates are found**, investigate thoroughly before adding to this list
3. **Keep this list updated** as new investigations are completed
4. **Reference this section** when explaining decisions to stakeholders

### Current Investigated Duplicates

#### 1. Cumberland River Behavioral Health Network
**Duplicate Type**: Website duplicates (crbhky.org)
**Resources**: Multiple locations and programs
**Investigation Date**: 2025-01-27
**Decision**: Keep separate - different programs and locations

**Resources to Keep Separate**:
- ID 134: Main Office (Corbin) - 1203 American Greeting Rd
- ID 142: Barbourville Office - 704 Pitzer Street, Barbourville
- ID 327: Capers Office (Corbin) - 175 East Peachtree Street
- ID 322: Appalachian Phoenix House (Education & Housing) - 401 Roy Kidd Ave
- ID 290: Turning Point (Substance Abuse Treatment) - 2932 Level Green Road
- ID 273: Independence House (Domestic Violence Program) - 3110 Cumberland Falls Highway
- ID 270: Evarts Office - Different address
- ID 331: Williamsburg Office - Different address
- ID 110: Manchester Office - Different address

**Reasoning**: Each location serves different geographic areas and/or different specialized programs (substance abuse, domestic violence, education, etc.). They share the same parent organization but operate as distinct service locations.

#### 2. 988 Crisis Services
**Duplicate Type**: Phone duplicates (988)
**Resources**: Multiple crisis services
**Investigation Date**: 2025-01-27
**Decision**: Keep separate - different populations and languages

**Resources to Keep Separate**:
- ID 355: 988 Suicide & Crisis Lifeline (English)
- ID 55: 988 Suicide & Crisis Lifeline - Spanish Services
- ID 27: Kentucky Crisis Prevention and Response System

**Reasoning**: These serve different populations (English vs Spanish speakers) and represent different aspects of the crisis response system (national vs state-level coordination).

#### 3. Kentucky Government Services - Shared Phone Numbers
**Duplicate Type**: Phone duplicates (855-306-8959, 800-462-6122)
**Resources**: Multiple government programs
**Investigation Date**: 2025-01-27
**Decision**: Keep separate - different programs and services

**Resources to Keep Separate**:
- Phone 855-306-8959:
  - ID 83: Kentucky SNAP (Supplemental Nutrition Assistance Program)
  - ID 18: Kentucky Child Care Assistance Program (CCAP)
  - ID 14: Kentucky Cabinet for Health and Family Services

- Phone 800-462-6122:
  - ID 97: Kentucky Women's Cancer Screening Program
  - ID 7: Kentucky Maternal and Child Health Hotline
  - ID 96: Kentucky WIC Program - Women, Infants and Children

**Reasoning**: These are different government programs that happen to share centralized phone numbers. Each serves distinct populations and provides different services.

#### 4. First Steps (Kentucky Early Intervention System)
**Duplicate Type**: Website duplicates
**Resources**: State vs Regional offices
**Investigation Date**: 2025-01-27
**Decision**: Keep separate - different organizational levels

**Resources to Keep Separate**:
- ID 295: First Steps (Kentucky Early Intervention System) - State office in Frankfort
- ID 13: Bluegrass First Steps - Regional office in Lexington

**Reasoning**: These represent different organizational levels within the same system - state administration vs regional service delivery.

#### 5. God's Pantry Food Bank
**Duplicate Type**: Website duplicates (godspantry.org)
**Resources**: Different programs
**Investigation Date**: 2025-01-27
**Decision**: Keep separate - different functions

**Resources to Keep Separate**:
- ID 332: God's Pantry Food Bank Southeast Regional Distribution Center (London, KY)
- ID 214: God's Pantry Emergency Food Box Program (Lexington, KY)

**Reasoning**: These are different programs within the same organization - physical distribution center vs centralized emergency assistance program.

#### 6. VOA Recovery - Freedom House
**Duplicate Type**: Email and website duplicates
**Resources**: Multiple locations
**Investigation Date**: 2025-01-27
**Decision**: Renamed to clarify geographic service areas

**Resources Renamed**:
- ID 123: VOA Recovery - Freedom House of Manchester
- ID 191: VOA Recovery - Freedom House of Louisville

**Reasoning**: Same organization but different geographic service areas with separate contact information. Renamed to clearly indicate service areas.

#### 7. Daniel Boone Community Action Agency
**Duplicate Type**: Email duplicates
**Resources**: Multiple county offices
**Investigation Date**: 2025-01-27
**Decision**: Renamed to clarify geographic service areas

**Resources Renamed**:
- ID 210: Daniel Boone Community Action Agency - Laurel County Office
- ID 111: Daniel Boone Community Action Agency - Clay County Office

**Reasoning**: Same organization but different county service areas with separate contact information. Renamed to clearly indicate service areas.

### Adding New Entries to This List

When you investigate a duplicate group and determine they should be kept separate:

1. **Document the investigation** with date and reasoning
2. **List all resources** in the duplicate group
3. **Explain the decision** clearly
4. **Add to this section** following the established format
5. **Update the table of contents** if needed

### Template for New Entries

```markdown
#### [Number]. [Organization/Service Name]
**Duplicate Type**: [Phone/Email/Website/Address duplicates]
**Resources**: [Brief description]
**Investigation Date**: [YYYY-MM-DD]
**Decision**: Keep separate - [reason]

**Resources to Keep Separate**:
- ID [X]: [Name] - [Location/Function]
- ID [Y]: [Name] - [Location/Function]

**Reasoning**: [Clear explanation of why these should remain separate]
```

### Maintenance Guidelines

- **Review this list quarterly** to ensure accuracy
- **Remove entries** if circumstances change (e.g., organization closes, merges)
- **Update reasoning** if new information becomes available
- **Cross-reference** with audit logs for consistency
- **Document any changes** in the investigation date

## Conclusion

This duplicate resolution process ensures data integrity while systematically cleaning up the resource database. By following this guide, you can safely identify, investigate, and merge duplicate resources while maintaining comprehensive audit trails and preserving important information.

Remember to always:
- Investigate thoroughly before merging
- Use dry-runs to preview changes
- Document your decisions
- Verify results after each operation
- Maintain data integrity throughout the process
- Review service types for appropriateness
- Plan multi-step sequences for complex scenarios
- Validate data quality after each operation
