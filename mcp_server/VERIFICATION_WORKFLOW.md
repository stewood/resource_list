# Resource Verification Workflow

This document guides users through the process of verifying resources in the Community Resource Directory using the MCP server tools.

## Overview

Resource verification is a critical process to ensure that the information in the Community Resource Directory remains accurate, up-to-date, and reliable for users seeking services. This workflow document provides step-by-step guidance for verifying resources using the available MCP tools.

## Prerequisites

- Access to the MCP server
- Understanding of the resource verification requirements
- Knowledge of the resource's service area and contact information

## Verification Process

### Step 1: Identify Resources Needing Verification

The first step in the verification process is to identify which resources require verification. Use the `mcp_resource-directory_list_unverified_resources_tool` to find resources that need attention.

#### Tool: `mcp_resource-directory_list_unverified_resources_tool`

**Purpose**: Identifies resources that require verification based on their verification status and frequency settings.

**Parameters**:
- `limit` (int, optional): Maximum number of results to return (default: 50, max: 100)
- `offset` (int, optional): Number of results to skip for pagination (default: 0)

**What it identifies**:
1. **Never Verified**: Resources that have never been verified (last_verified_at is null)
2. **Overdue**: Resources that are past their verification due date based on verification_frequency_days
3. **No Frequency Set**: Resources that don't have a verification frequency configured

**Example Usage**:
```
mcp_resource-directory_list_unverified_resources_tool(limit=1, offset=0)
```

**Response includes**:
- List of resources needing verification with complete details
- Verification status for each resource
- Pagination information
- Summary counts by verification status

**Key Information Provided**:
- Resource ID, name, description, and status
- Contact information (phone, email, website)
- Location details (city, state, county)
- Verification metadata:
  - Verification status ("never_verified", "overdue", "no_frequency_set")
  - Last verification date
  - Verification frequency (typically 180 days = 6 months)
  - Days overdue (for overdue resources)

**Next Steps**: Once you have identified resources needing verification, proceed to Step 2 to research and gather current information about the resource.

### Step 2: Research and Identify Information Sources

The second step is to find reliable sources of information about the resource that contain current, accurate data we can extract to update our resource record.

#### Purpose
Find reliable sources of information about the resource that contain current, accurate data we can extract to update our resource record.

#### Information Sources to Target

**Primary Data Sources** (Highest Priority):
1. **Official Organization Website**
   - Current contact information (phone, email, address)
   - Updated service descriptions
   - Hours of operation
   - Eligibility requirements
   - Service areas/coverage

2. **Official Social Media Pages** (Verified accounts)
   - Recent posts about services or contact changes
   - Updated hours or location information
   - Service announcements or changes
   - Current contact details in bio/about sections

3. **Government Directories and Listings**
   - State/county service directories
   - Licensing boards or regulatory agencies
   - Official government service listings
   - Public health or social service directories

**Secondary Data Sources** (Supporting Information):
4. **Nonprofit/Business Directories**
   - GuideStar, Charity Navigator
   - Local chamber of commerce listings
   - Professional association directories
   - Better Business Bureau listings

5. **News Articles and Press Releases**
   - Recent announcements about service changes
   - Contact information updates
   - New location or hours announcements
   - Service expansion or reduction news

6. **Location-Based Services**
   - Google Maps business listings
   - Yelp business pages
   - Local business directories

#### Data Points to Extract from Each Source

- **Contact Information**: Phone numbers, email addresses, website URLs
- **Location Details**: Street addresses, cities, states, counties, ZIP codes
- **Service Information**: What services are actually provided
- **Operational Details**: Hours of operation, availability
- **Eligibility**: Who can access services, requirements
- **Coverage Areas**: Geographic service areas
- **Status**: Whether the organization is currently operating

#### Source Verification Criteria
- **Recency**: Information should be current (within last 6-12 months)
- **Authority**: Source should be official or verified
- **Consistency**: Information should align across multiple sources
- **Completeness**: Source should have the specific data we need

#### Information Gathered at End of Step 2

**Source Documentation**:
- List of verified sources we found and checked
- Source URLs for each piece of information
- Date of information (when the source was last updated)
- Source type (official website, social media, government directory, etc.)

**Current Contact Information**:
- Phone numbers (primary and any additional numbers)
- Email addresses (primary contact and any specific department emails)
- Website URL (current, working website)
- Physical address (complete street address)
- Mailing address (if different from physical address)

**Location Details**:
- Street address (address1, address2)
- City (current city name)
- State (state abbreviation)
- County (county or parish name)
- ZIP/Postal code (current postal code)

**Service Information**:
- Current service descriptions (what they actually provide now)
- Service types (specific services offered)
- Service categories (which taxonomy category they belong to)
- Eligibility requirements (who can access services)
- Populations served (target demographics)

**Operational Details**:
- Hours of operation (current business hours)
- Availability (24-hour service, emergency services, etc.)
- Languages available (what languages services are provided in)
- Insurance accepted (payment methods, insurance types)
- Cost information (fees, sliding scale, free services)

**Status and Coverage**:
- Current operating status (active, temporarily closed, etc.)
- Service area coverage (geographic areas served)
- Capacity information (waiting lists, service limits)

#### Service Area Verification Process

**Critical Step**: Verify the resource's actual service areas against the coverage areas assigned in the database.

**Why This Matters**:
- Users search for services by location
- Missing coverage areas mean users can't find available services
- Incorrect coverage areas lead to wasted time and missed opportunities
- Service area gaps are often the most critical verification issues

**Verification Steps**:

1. **Check Current Coverage Areas**:
   - Use `mcp_resource-directory_get_resource_coverage_areas_tool` to see what areas are currently assigned
   - Note the total number of coverage areas assigned

2. **Research Official Service Areas**:
   - Check the organization's official website for service area information
   - Look for statements like "serves X counties" or "service area includes..."
   - Check government directories and regulatory listings
   - Review regional planning documents or development district information

3. **Cross-Reference Multiple Sources**:
   - Verify service areas from at least 2-3 official sources
   - Check for consistency across different listings
   - Look for recent changes in service areas

4. **Identify Discrepancies**:
   - Compare assigned coverage areas vs. official service areas
   - Note any missing coverage areas (most common issue)
   - Note any incorrectly assigned areas
   - Document the complete list of counties/areas the resource actually serves

**Common Service Area Sources**:
- Official organization website
- Government service directories
- Regional planning agency websites
- State health/human services directories
- Professional association listings
- Licensing board information

**Service Area Documentation**:
- Complete list of counties/areas served (from official sources)
- List of currently assigned coverage areas (from database)
- List of missing coverage areas that need to be added
- List of incorrectly assigned areas that need to be removed
- Source URLs for service area information
- Confidence level for service area verification

## 🚨 **CRITICAL: National Resource Handling**

**National resources require special attention during verification. These resources serve the entire United States and must be properly configured to appear in searches from any location.**

### **National Coverage Area Configuration**

**Coverage Area Details**:
- **Coverage Area Name**: "United States (All States and Territories)"
- **Coverage Area ID**: 43273 (verify current ID using `list_coverage_areas_tool`)
- **Kind**: POLYGON
- **Purpose**: Represents services available nationwide

### **When to Assign National Coverage**

**Assign national coverage (ID: 43273) for resources that serve the entire United States, including**:

**Federal Government Services**:
- HUD (Housing and Urban Development) programs
- HHS (Health and Human Services) services
- VA (Veterans Affairs) programs
- SSA (Social Security Administration) services
- Federal emergency services

**National Hotlines and Crisis Services**:
- 988 Suicide & Crisis Lifeline
- National Domestic Violence Hotline
- National Human Trafficking Hotline
- Poison Control Centers
- National Child Abuse Hotline

**National Nonprofit Organizations**:
- Organizations with verified nationwide reach
- National advocacy organizations
- National service providers with local chapters
- National information and referral services

**Online and Digital Services**:
- Web-based directories available to all US residents
- Online counseling or support services
- National information databases
- Digital resources accessible from anywhere

**National Programs and Services**:
- Federal benefit programs
- National insurance programs
- National emergency response services
- National public health programs

### **National Coverage Assignment Process**

**Step 1: Verify National Scope**
- Confirm the resource actually serves all US states and territories
- Check for any geographic restrictions or limitations
- Verify the organization has the capacity to serve nationwide

**Step 2: Check Official Sources**
- Look for explicit statements like "serves all 50 states" or "nationwide service"
- Check official websites for service area information
- Review government directories and listings
- Verify through multiple authoritative sources

**Step 3: Assign National Coverage**
```bash
# Use the MCP tool to assign national coverage
mcp_resource-directory_assign_coverage_area_to_resource_tool(
    resource_id=[RESOURCE_ID],
    coverage_area_id=43273,  # United States (All States and Territories)
    assigned_by_user_id=1
)
```

**Step 4: Remove Local Coverage (if applicable)**
- If the resource is truly national, remove any state/county-specific coverage areas
- Use `mcp_resource-directory_remove_coverage_area_tool` to remove local areas
- Keep local coverage only if the resource serves both nationally AND locally

**Step 5: Document Decision**
- Include clear rationale for national coverage assignment in verification notes
- Document the sources that confirmed nationwide service
- Note any limitations or special considerations

### **National Resource Verification Checklist**

**Before Assigning National Coverage**:
- [ ] **Official website confirms nationwide service**
- [ ] **Government directories list national scope**
- [ ] **No geographic restrictions found**
- [ ] **Organization has capacity for nationwide service**
- [ ] **Multiple sources confirm national reach**

**After Assigning National Coverage**:
- [ ] **National coverage area (ID: 43273) assigned**
- [ ] **Local coverage areas removed (if resource is purely national)**
- [ ] **Verification notes document national scope**
- [ ] **Resource appears in searches from any location**
- [ ] **No conflicting local coverage areas remain**

### **Common National Resource Scenarios**

**Scenario 1: Pure National Resource**
- **Example**: 988 Suicide & Crisis Lifeline
- **Action**: Assign only national coverage (ID: 43273)
- **Remove**: All local/state coverage areas

**Scenario 2: National Organization with Local Chapters**
- **Example**: American Red Cross
- **Action**: Assign both national coverage AND specific local areas
- **Keep**: Both national and local coverage areas

**Scenario 3: Online Service with National Reach**
- **Example**: National online directory
- **Action**: Assign national coverage (ID: 43273)
- **Remove**: Any location-specific coverage areas

**Scenario 4: Federal Program with Local Implementation**
- **Example**: SNAP (Food Stamps) program
- **Action**: Assign national coverage (ID: 43273)
- **Note**: Document that local offices handle implementation

### **Troubleshooting National Resources**

**Issue**: Resource serves nationwide but not assigned to national coverage
**Solution**:
- Verify the resource actually serves all US states and territories
- Check official sources for nationwide service statements
- Assign the national coverage area: "United States (All States and Territories)" (ID: 43273)
- Remove any state/county-specific coverage areas if resource is truly national
- Document the national scope in verification notes

**Issue**: Resource has both national and local coverage areas
**Solution**:
- Determine if this is appropriate (national org with local chapters)
- If purely national, remove local coverage areas
- If hybrid, keep both but document the relationship
- Ensure no conflicting or redundant coverage areas

**Issue**: National resource not appearing in location searches
**Solution**:
- Verify national coverage area (ID: 43273) is assigned
- Check that no local coverage areas are conflicting
- Test search functionality from different locations
- Ensure resource status is "published"

**Verification Metadata**:
- Date of verification (when we gathered this information)
- Sources used (which sources provided which information)
- Confidence level (how reliable we consider each piece of information)
- Discrepancies found (any conflicts between sources)

**Next Steps**: Once you have gathered comprehensive information from reliable sources, proceed to Step 3 to review, compare, and decide what changes to make to the resource record.

### Step 3: Review and Decide on Record Updates

The third step is the decision-making phase where you analyze the information gathered in Step 2, compare it with the current resource record, and determine what changes need to be made. This step involves careful evaluation of discrepancies, verification of conflicting information, and planning specific updates to ensure the record is accurate and current.

#### Purpose
Review the current resource record against verified information sources to identify discrepancies, contradictions, and missing information, then make informed decisions about what changes to implement.

#### 3.1 Data Comparison and Analysis

**Comprehensive Field-by-Field Verification Process**:

**CRITICAL**: Evaluate EVERY field in the resource record against verified sources. Do not skip any field - each one impacts user experience and service accessibility.

#### **Basic Information Fields**:
- **Name**: Verify the official name matches current branding
- **Description**: Review for accuracy, completeness, and user-friendliness
  - Does it reflect current services?
  - Is it comprehensive based on verified sources?
  - Does it use clear, accessible language?
  - Are there outdated or inaccurate statements?
  - Is it structured logically for users?
  - **CRITICAL**: Keep descriptions user-focused - remove any internal system references, verification notes, or administrative information. All verification documentation belongs in the notes field, not the description.

#### **Contact Information Fields**:
- **Phone**: Verify number, format for readability, check for additional numbers
- **Email**: Verify primary contact email, check for general/department emails
- **Website**: Test URL functionality, verify it's current and secure

#### **Location Fields**:
- **Address1**: Verify street address accuracy
- **Address2**: Check for suite/unit information
- **City**: Verify current city name
- **State**: Confirm state abbreviation
- **County**: Verify county/parish name
- **Postal Code**: Confirm ZIP/postal code accuracy

#### **Operational Fields**:
- **Hours of Operation**: Verify current business hours
- **Is Emergency Service**: Confirm if 24/7 emergency services provided
- **Is 24 Hour Service**: Verify round-the-clock availability
- **Eligibility Requirements**: Review who can access services
- **Populations Served**: Verify target demographics
- **Insurance Accepted**: Check payment methods and insurance types
- **Cost Information**: Verify fee structure, sliding scale, free services
- **Languages Available**: Confirm languages services are provided in
- **Capacity**: Check for waiting lists, service limits, availability

#### **Service Classification Fields**:
- **Category**: Verify the resource is in the correct taxonomy category
  - Does the current category accurately reflect the primary service type?
  - Should it be moved to a different category?
  - Is the category specific enough for user searches?
- **Service Types**: Review and verify all service types assigned
  - Are all current services represented?
  - Are there services that should be added?
  - Are there service types that should be removed?
  - Do the service types match the organization's actual offerings?

#### **Coverage Area Fields**:
- **Service Areas**: Verify all geographic areas served (see Service Area Verification Process above)
- **Coverage Assignments**: Ensure all counties/areas are properly assigned

#### **Status and Metadata Fields**:
- **Status**: Confirm current operating status (published, draft, needs review)
- **Verification Information**: Update verification dates and notes

#### **Category and Service Type Evaluation Process**:

**CRITICAL**: Category and service type accuracy directly impacts user searchability and resource discovery.

**Category Evaluation**:
1. **Review Current Category**: Is the resource in the most appropriate category?
2. **Check Category Accuracy**: Does the current category match the primary service focus?
3. **Consider Category Changes**: Should the resource be moved to a different category?
4. **Verify Category Completeness**: Is the category specific enough for user searches?

**Service Type Evaluation**:
1. **List Current Service Types**: What service types are currently assigned?
2. **Research Actual Services**: What services does the organization actually provide?
3. **Compare and Identify Gaps**: 
   - Are there service types that should be added?
   - Are there service types that should be removed?
   - Do the service types accurately reflect current offerings?
4. **Use Available Service Types**: Check the taxonomy for appropriate service types to assign

**Service Type Research Sources**:
- Official organization website service descriptions
- Program listings and service catalogs
- Government service directories
- Professional association listings
- Recent service announcements or changes

**Category and Service Type Documentation**:
- Current category and service types assigned
- Recommended category and service types based on research
- Rationale for any changes
- Sources used for verification

**Comparison Framework**:
- Current database record vs. verified sources
- Identify exact matches (no changes needed)
- Identify discrepancies (requires decision)
- Identify missing information (consider adding)
- Identify unverified information (consider removing)

#### 3.2 Decision Framework for Information Management

**For Unverified Information**:
- **Remove**: Information that cannot be confirmed from reliable sources
- **Flag**: Information that needs further investigation using additional web searches
- **Note**: Add verification notes about uncertainty for future review

**For Contradictory Information**:
- **Source Hierarchy**: Official website > Government directory > Third-party listings
- **Recency Priority**: Most recent information takes precedence
- **Consensus Approach**: Information appearing in multiple sources is more reliable
- **Additional Research**: Use web search tools to resolve conflicts when needed

**For Missing Information**:
- **Add**: Information that is verified and adds value to the record
- **Consider**: Whether the information is essential for users seeking services
- **Document**: Source and verification method for all additions

#### 3.3 Service Area Decision Framework

**Critical Priority**: Service area discrepancies are often the most impactful issues for users.

**For Missing Coverage Areas**:
- **Add Immediately**: Any counties/areas the resource officially serves but are missing from the database
- **High Priority**: Missing coverage areas prevent users from finding available services
- **Document**: Source of service area information and verification method
- **Verify**: Use multiple official sources to confirm service areas

**For Incorrectly Assigned Areas**:
- **Remove**: Areas the resource does not actually serve
- **Verify**: Double-check with official sources before removing
- **Document**: Reason for removal and source verification

**For Service Area Changes**:
- **Recent Changes**: Check if service areas have expanded or contracted recently
- **Official Announcements**: Look for press releases or official statements about service area changes
- **Government Updates**: Check if regulatory changes affected service areas

**Service Area Decision Documentation**:
- **Current Coverage Areas**: List of areas currently assigned in database
- **Official Service Areas**: List of areas resource actually serves (from verified sources)
- **Areas to Add**: Missing coverage areas that need to be assigned
- **Areas to Remove**: Incorrectly assigned areas that need to be removed
- **Sources Used**: URLs and dates of sources used for service area verification
- **Confidence Level**: How certain we are about each service area decision

**Common Service Area Issues**:
- **Missing Counties**: Resource serves 8 counties but only 4 are assigned
- **Outdated Areas**: Service areas changed but database not updated
- **Incorrect Boundaries**: Resource serves different area than assigned
- **Regional vs. Local**: Confusion between regional and local service areas

#### 3.4 Description Review and Refactoring

**Current Description Analysis**:
- Does it accurately reflect current services?
- Is it comprehensive based on verified sources?
- Does it use clear, accessible language?
- Are there outdated or inaccurate statements?
- Is it structured logically for users?

**Refactoring Considerations**:
- **Structure**: Organize information logically (services, eligibility, contact)
- **Accuracy**: Ensure all claims can be verified from reliable sources
- **Completeness**: Include all verified services and programs
- **Clarity**: Use plain language, avoid jargon
- **Consistency**: Match terminology used in official sources
- **User Focus**: Write from the perspective of someone seeking services

#### 3.5 Using Web Search Tools for Decision Support

When discrepancies or uncertainties arise, use available web search and browsing tools to:

**Resolve Conflicts**:
- Search for additional sources to verify conflicting information
- Check multiple directories or listings for consensus
- Look for recent news or announcements about changes

**Verify Missing Information**:
- Search for current contact details not found in initial sources
- Look up recent service changes or program updates
- Find additional service descriptions or eligibility requirements

**Quality Assurance**:
- Cross-reference information across multiple sources
- Verify that websites and phone numbers are current and working
- Check for recent organizational changes or relocations

#### 3.6 Decision Documentation

**Update Plan Documentation**:
- **Fields to Update**: List each field that needs changes
- **Fields to Add**: New information to be added to the record
- **Fields to Remove**: Unverified or outdated information to be removed
- **Description Changes**: Specific changes to the description field
- **Rationale**: Brief explanation for each decision

**Verification Notes**:
- Source URLs for each piece of information
- Date of verification
- Confidence level for each field
- Notes about discrepancies or uncertainties
- Additional research performed

#### 3.7 Quality Assurance Checklist

Before finalizing update decisions, verify:
- [ ] **ALL FIELDS evaluated against verified sources** (CRITICAL)
- [ ] All contact information verified from official sources
- [ ] Location details match official records
- [ ] Service descriptions are current and accurate
- [ ] Eligibility requirements are clearly stated
- [ ] **Coverage areas are properly defined and complete** (CRITICAL)
- [ ] All counties/areas the resource serves are assigned as coverage areas
- [ ] No incorrectly assigned coverage areas remain
- [ ] **Category is accurate and appropriate** (CRITICAL)
- [ ] **Service types accurately reflect current offerings** (CRITICAL)
- [ ] All current services are represented in service types
- [ ] No outdated or incorrect service types remain
- [ ] Cost information is accurate and complete
- [ ] Hours of operation are current
- [ ] Languages available are correctly listed
- [ ] No unverified claims remain in the record
- [ ] Description is comprehensive and user-friendly
- [ ] All changes are documented with sources

#### Information Gathered at End of Step 3

**Update Decisions**:
- Complete list of fields to be updated with new values
- List of new fields to be added to the record
- List of fields to be removed or marked as unverified
- New description text (if description needs rewriting)
- **Service Area Decisions**: Coverage areas to add, remove, or modify
- **Category Decision**: Whether to change the resource's category
- **Service Type Decisions**: Service types to add, remove, or modify

**Verification Documentation**:
- Sources used for each piece of information
- Confidence levels for all changes
- Rationale for decisions made
- Notes about any remaining uncertainties

**Next Steps**: Once you have a clear update plan with all decisions documented, proceed to Step 4 to implement the changes to the resource record.

### Step 4: Implement Resource Updates

The fourth step is the implementation phase where you apply all the verified changes to the resource record using the available MCP tools. This step involves executing the update plan developed in Step 3, ensuring all changes are properly applied, and documenting the verification process.

#### Purpose
Implement all verified changes to the resource record using the appropriate MCP tools, ensuring data integrity and proper documentation of the verification process.

#### 4.1 Pre-Implementation Checklist

Before implementing changes, verify you have:
- [ ] Complete update plan from Step 3
- [ ] All source URLs and verification dates documented
- [ ] Service type IDs identified for any service type changes
- [ ] Coverage area IDs identified for any coverage area changes
- [ ] Verification report ready for the notes field

#### 4.2 Implementation Tools and Process

**Primary Update Tool**: `mcp_resource-directory_update_resource_tool`

**Purpose**: Updates any field of an existing resource record.

**Key Parameters**:
- `resource_id` (required): The ID of the resource to update
- `service_type_ids` (optional): Array of service type IDs to assign
- `phone` (optional): Updated phone number
- `email` (optional): Updated email address
- `website` (optional): Updated website URL
- `address1`, `address2`, `city`, `state`, `county`, `postal_code` (optional): Location updates
- `hours_of_operation` (optional): Updated business hours
- `eligibility_requirements` (optional): Updated eligibility information
- `populations_served` (optional): Updated target demographics
- `cost_information` (optional): Updated cost details
- `languages_available` (optional): Updated language information
- `notes` (optional): Verification report and documentation
- `status` (optional): Update status (typically set to "needs_review")

**Coverage Area Management Tools**:
- `mcp_resource-directory_assign_coverage_area_to_resource_tool`: Add new coverage areas
- `mcp_resource-directory_remove_coverage_area_tool`: Remove incorrect coverage areas
- `mcp_resource-directory_get_resource_coverage_areas_tool`: Verify current coverage areas

#### 4.3 Implementation Sequence

**Step 4.3.1: Update Basic Resource Information**

Use `mcp_resource-directory_update_resource_tool` to update:
- Service types (if any changes)
- Contact information (phone, email, website)
- Location details (address fields)
- Operational information (hours, eligibility, etc.)
- Notes field with verification report
- Status (set to "needs_review" for review)

**Example Implementation**:
```
mcp_resource-directory_update_resource_tool(
    resource_id=29,
    service_type_ids=[39, 5, 6, 7],  # Case management, Legal, Healthcare, Employment
    phone="606-877-5763",
    notes="# Verification Report - 2025-01-27\n\n## Verification Sources..."
)
```

**Step 4.3.2: Manage Coverage Areas**

**For Adding Coverage Areas**:
1. Use `mcp_resource-directory_list_coverage_areas_tool` to find coverage area IDs
2. Use `mcp_resource-directory_assign_coverage_area_to_resource_tool` for each new area

**For Removing Coverage Areas**:
1. Use `mcp_resource-directory_remove_coverage_area_tool` for incorrect areas

**Example Coverage Area Management**:
```
# Add new coverage areas
mcp_resource-directory_assign_coverage_area_to_resource_tool(
    resource_id=29,
    coverage_area_id=35526  # Clay County
)

# Remove incorrect coverage areas
mcp_resource-directory_remove_coverage_area_tool(
    resource_id=29,
    coverage_area_id=35565  # Incorrect county
)

# Assign national coverage area for nationwide resources
mcp_resource-directory_assign_coverage_area_to_resource_tool(
    resource_id=63,
    coverage_area_id=43273  # United States (All States and Territories)
)
```

#### 4.4 Verification Report Format

The verification report in the notes field should follow this structure:

```markdown
# Verification Report - [DATE]

## Verification Sources
- **Primary**: [Source name] ([URL])
- **Secondary**: [Source name] ([URL])
- **Cross-reference**: [Source name] ([URL])

## Field-by-Field Verification

### Basic Information
- **Name**: ✅ **VERIFIED UNCHANGED** - [Verification details]
- **Description**: ✅ **VERIFIED UNCHANGED** - [Verification details]
- **Phone**: ✅ **UPDATED** - [Change details and source]
- **Email**: ✅ **VERIFIED UNCHANGED** - [Verification details]

### Location and Coverage
- **Address**: ✅ **VERIFIED UNCHANGED** - [Verification details]
- **Coverage Areas**: ✅ **UPDATED** - [Changes made and sources]

### Services
- **Service Types**: ✅ **UPDATED** - [Changes made and sources]
```

**Key Elements**:
- **Date**: Current verification date
- **Sources**: All sources used with URLs
- **Status Indicators**: ✅ for verified, 🔄 for updated
- **Field-by-Field**: Every field evaluated and documented
- **Source References**: Where each piece of information was found

#### 4.5 Post-Implementation Verification

**Step 4.5.1: Verify Updates Applied**

Use `mcp_resource-directory_get_resource_tool` to confirm:
- [ ] All field updates were applied correctly
- [ ] Service types are properly assigned
- [ ] Verification report is in notes field
- [ ] Status is set to "needs_review"

**Step 4.5.2: Verify Coverage Areas**

Use `mcp_resource-directory_get_resource_coverage_areas_tool` to confirm:
- [ ] All intended coverage areas are assigned
- [ ] No incorrect coverage areas remain
- [ ] Total count matches expected number

**Step 4.5.3: Final Quality Check**

- [ ] All changes from Step 3 have been implemented
- [ ] No errors occurred during implementation
- [ ] Resource status is appropriate for next steps
- [ ] Verification documentation is complete

#### 4.6 Common Implementation Issues and Solutions

**Issue**: Service type IDs not found
**Solution**: Use `mcp_resource-directory_list_service_types_tool` to find correct IDs

**Issue**: Coverage area IDs not found
**Solution**: Use `mcp_resource-directory_list_coverage_areas_tool` with appropriate filters

**Issue**: Update fails due to validation errors
**Solution**: Check parameter formats (phone numbers, email addresses, URLs)

**Issue**: Coverage area assignment fails
**Solution**: Verify coverage area ID exists and resource ID is correct

#### 4.7 Implementation Documentation

**Record the Following**:
- **Implementation Date**: When updates were applied
- **Tools Used**: Which MCP tools were used for updates
- **Changes Applied**: Summary of all changes made
- **Issues Encountered**: Any problems and how they were resolved
- **Final Status**: Resource status after implementation
- **Next Steps**: What happens next (review, publish, etc.)

#### 4.8 Success Criteria

Implementation is successful when:
- [ ] All planned updates have been applied
- [ ] No implementation errors occurred
- [ ] Resource status is set to "needs_review"
- [ ] Verification report is complete and accurate
- [ ] Coverage areas are correctly assigned
- [ ] Service types accurately reflect current offerings
- [ ] All contact and location information is current

#### Information Gathered at End of Step 4

**Implementation Summary**:
- Complete list of changes successfully applied
- Any issues encountered and resolutions
- Final resource status and next steps
- Verification documentation completeness

**Resource Status**:
- Updated resource record with all verified information
- Proper status for workflow continuation
- Complete verification trail in notes field

**Next Steps**: The resource is now ready for review and potential publication. The verification process is complete, and all changes have been properly documented and implemented.

## Available Tools

### Resource Management Tools

**`mcp_resource-directory_list_unverified_resources_tool`**
- **Purpose**: Find resources needing verification
- **Key Use**: Step 1 - Identify verification candidates
- **Parameters**: `limit`, `offset` for pagination

**`mcp_resource-directory_get_resource_tool`**
- **Purpose**: Retrieve complete resource details
- **Key Use**: Step 2 - Get current record for comparison
- **Parameters**: `resource_id` (required)

**`mcp_resource-directory_update_resource_tool`**
- **Purpose**: Update any resource field
- **Key Use**: Step 4 - Implement verified changes
- **Parameters**: `resource_id` (required), plus any fields to update

### Coverage Area Tools

**`mcp_resource-directory_get_resource_coverage_areas_tool`**
- **Purpose**: View current coverage areas
- **Key Use**: Step 2 - Check service area assignments

**`mcp_resource-directory_assign_coverage_area_to_resource_tool`**
- **Purpose**: Add coverage areas to resource
- **Key Use**: Step 4 - Add missing service areas

**`mcp_resource-directory_remove_coverage_area_tool`**
- **Purpose**: Remove coverage areas from resource
- **Key Use**: Step 4 - Remove incorrect service areas

**`mcp_resource-directory_list_coverage_areas_tool`**
- **Purpose**: Find coverage area IDs by name/type
- **Key Use**: Step 4 - Locate correct coverage area IDs

### Service Type Tools

**`mcp_resource-directory_list_service_types_tool`**
- **Purpose**: Find available service types
- **Key Use**: Step 4 - Locate correct service type IDs

**`mcp_resource-directory_get_service_type_tool`**
- **Purpose**: Get service type details
- **Key Use**: Step 3 - Verify service type accuracy

### Search and Research Tools

**`mcp_mcp-search_web_search`**
- **Purpose**: Search for current information
- **Key Use**: Step 2 - Find official sources

**`mcp_mcp-search_pull_markdown`**
- **Purpose**: Extract content from websites
- **Key Use**: Step 2 - Get detailed information from sources

### Taxonomy Tools

**`mcp_resource-directory_list_categories_tool`**
- **Purpose**: View available categories
- **Key Use**: Step 3 - Verify category accuracy

**`mcp_resource-directory_get_category_tool`**
- **Purpose**: Get category details
- **Key Use**: Step 3 - Understand category scope

## Best Practices

### Efficiency and Prioritization

**Resource Prioritization**:
1. **High Priority**: Resources with missing coverage areas
2. **Medium Priority**: Resources with outdated contact information
3. **Low Priority**: Resources with minor description updates

**Batch Processing**:
- Process 1 resource at a time for focused verification
- Group by geographic area or service type for efficiency
- Use consistent verification sources across similar resources

**Time Management**:
- **Simple Updates**: 15-30 minutes per resource
- **Complex Verification**: 45-90 minutes per resource
- **New Resource Research**: 60-120 minutes per resource

### Quality Assurance

**Source Verification Hierarchy**:
1. **Official Organization Website** (Highest Priority)
2. **Government Directories** (High Priority)
3. **Verified Social Media** (Medium Priority)
4. **Third-party Listings** (Low Priority)

**Cross-Reference Requirements**:
- Verify critical information from at least 2 sources
- Use 3+ sources for service area verification
- Document source conflicts and resolution approach

**Documentation Standards**:
- Always include source URLs in verification reports
- Use consistent date format (YYYY-MM-DD)
- Include confidence levels for all changes
- Document any uncertainties or limitations

**System Behavior Notes**:
- **Phone Formatting**: The system automatically formats phone numbers consistently (e.g., "(606) 877-5763" becomes "606-877-5763"). This formatting is applied internally and may not be visible in tool outputs.
- **Data Validation**: The system validates and standardizes certain fields automatically
- **Status Updates**: Resources are typically set to "needs_review" after verification for human review

### Communication and Collaboration

**Status Management**:
- Set resources to "needs_review" after verification
- Use notes field for detailed verification documentation
- Include contact information for follow-up questions

**Escalation Process**:
- Flag complex cases requiring human review
- Document unresolved conflicts or uncertainties
- Provide clear rationale for all decisions

## Troubleshooting

### Common Technical Issues

**Issue**: Website is down or inaccessible
**Solutions**:
- Try alternative URLs (www vs. non-www)
- Check social media for current information
- Use government directories as backup sources
- Document the issue in verification notes
- Set verification frequency to shorter interval

**Issue**: Conflicting information between sources
**Solutions**:
- Apply source hierarchy (official > government > third-party)
- Use most recent information as tiebreaker
- Document all sources and conflicts in notes
- Consider contacting organization directly for clarification

**Issue**: Service type IDs not found in system
**Solutions**:
- Use `mcp_resource-directory_list_service_types_tool` to browse all options
- Check for similar service types with different names
- Consider if service should be in different category
- Document the gap for system improvement

**Issue**: Coverage area IDs not found
**Solutions**:
- Use `mcp_resource-directory_list_coverage_areas_tool` with different filters
- Try searching by state, then county
- Check for alternative county names or spellings
- Verify the area should be covered by this resource

**Issue**: Resource serves nationwide but not assigned to national coverage
**Solutions**:
- Verify the resource actually serves all US states and territories
- Check official sources for nationwide service statements
- Assign the national coverage area: "United States (All States and Territories)" (ID: 43273)
- Remove any state/county-specific coverage areas if resource is truly national
- Document the national scope in verification notes

### Data Quality Issues

**Issue**: Resource appears to be duplicate
**Solutions**:
- Compare all fields carefully
- Check if different locations of same organization
- Verify if different programs of same organization
- Document findings and recommend consolidation if needed

**Issue**: Resource has changed significantly (name, mission, services)
**Solutions**:
- Research if this is the same organization
- Check for merger, acquisition, or rebranding
- Update all relevant fields to reflect current state
- Document the changes in verification notes

**Issue**: Resource appears to be inactive or closed
**Solutions**:
- Verify closure from multiple sources
- Check for relocation or merger
- Update status to "draft" or archive if confirmed closed
- Document closure date and reason if available

### Process Issues

**Issue**: Verification taking too long
**Solutions**:
- Focus on critical fields first (contact, coverage areas)
- Use official sources primarily to reduce research time
- Set reasonable time limits per resource
- Document partial verification for follow-up

**Issue**: Unable to find reliable sources
**Solutions**:
- Try broader web searches with different keywords
- Check government licensing or registration databases
- Look for news articles about the organization
- Document search attempts and limitations

**Issue**: Information seems outdated but no current sources found
**Solutions**:
- Use most recent information available
- Document the date of last verification
- Set shorter verification frequency
- Flag for priority re-verification

### System Integration Issues

**Issue**: Update tool fails with validation errors
**Solutions**:
- Check phone number format (remove parentheses, use dashes)
- Verify email address format
- Ensure URLs include protocol (http:// or https://)
- Check for special characters in text fields

**Note**: Phone number formatting is handled automatically by the system. When you update a phone number, the system will automatically format it consistently (e.g., converting "(606) 877-5763" to "606-877-5763"). This formatting change is not reflected in the tool output - the system stores the formatted version internally.

**Issue**: Coverage area assignment fails
**Solutions**:
- Verify coverage area ID exists
- Check if area is already assigned
- Ensure resource ID is correct
- Try assigning one area at a time

**Issue**: Service type assignment fails
**Solutions**:
- Verify service type ID exists
- Check if service type is appropriate for resource category
- Ensure array format is correct
- Try assigning one service type at a time

### Emergency and Crisis Situations

**Issue**: Resource provides emergency services but not marked correctly
**Solutions**:
- Verify emergency service status from official sources
- Update `is_emergency_service` and `is_24_hour_service` flags
- Ensure coverage areas include all emergency service areas
- Prioritize verification of emergency service resources

**Issue**: Resource contact information is critical but unverified
**Solutions**:
- Use multiple verification methods (phone, email, website)
- Test contact methods if possible
- Document verification attempts
- Set shorter verification frequency for critical resources

### Quality Control and Review

**Issue**: Verification seems incomplete or uncertain
**Solutions**:
- Document all uncertainties in verification notes
- Set shorter verification frequency
- Flag for human review
- Provide clear rationale for decisions made

**Issue**: Changes seem significant but sources are limited
**Solutions**:
- Use conservative approach (verify before changing)
- Document source limitations
- Set status to "needs_review" for human verification
- Include detailed rationale in notes

### Performance and Efficiency

**Issue**: Verification process is too slow
**Solutions**:
- Focus on high-impact changes first
- Use batch processing for similar resources
- Streamline source verification process
- Set reasonable time limits per resource

**Issue**: Too many resources need verification
**Solutions**:
- Prioritize by user impact (coverage areas, contact info)
- Focus on resources with missing critical information
- Use systematic approach (geographic or service type grouping)
- Consider resource importance and usage patterns

## Quick Reference Guide

### Common Verification Scenarios

**Scenario 1: Simple Contact Update**
- **Time**: 15-20 minutes
- **Steps**: Get resource → Check website → Update phone/email → Add notes
- **Tools**: `get_resource_tool`, `web_search`, `update_resource_tool`

**Scenario 2: Missing Coverage Areas**
- **Time**: 30-45 minutes
- **Steps**: Get resource → Check coverage areas → Research service area → Find coverage IDs → Add areas → Update notes
- **Tools**: `get_resource_tool`, `get_resource_coverage_areas_tool`, `web_search`, `list_coverage_areas_tool`, `assign_coverage_area_tool`, `update_resource_tool`

**Scenario 3: Service Type Updates**
- **Time**: 25-35 minutes
- **Steps**: Get resource → Research services → Find service type IDs → Update service types → Add notes
- **Tools**: `get_resource_tool`, `web_search`, `list_service_types_tool`, `update_resource_tool`

**Scenario 4: National Resource Assignment** 🚨
- **Time**: 20-30 minutes
- **Steps**: Get resource → Verify national scope → Assign national coverage (ID: 43273) → Remove local areas → Document decision
- **Tools**: `get_resource_tool`, `get_resource_coverage_areas_tool`, `web_search`, `assign_coverage_area_tool`, `remove_coverage_area_tool`, `update_resource_tool`
- **Critical**: Verify resource actually serves all US states and territories

**Scenario 5: Complete Resource Verification**
- **Time**: 60-90 minutes
- **Steps**: Full 4-step process with comprehensive research and updates
- **Tools**: All tools as needed

### Priority Matrix

| Issue Type | User Impact | Priority | Time to Fix |
|------------|-------------|----------|-------------|
| Missing Coverage Areas | High | Critical | 30-45 min |
| **National Resource Not Assigned** | **High** | **Critical** | **20-30 min** |
| Wrong Contact Info | High | Critical | 15-20 min |
| Missing Service Types | Medium | High | 25-35 min |
| Outdated Description | Medium | Medium | 20-30 min |
| Wrong Category | Low | Medium | 15-25 min |
| Minor Format Issues | Low | Low | 5-10 min |

### Verification Checklist Template

**Pre-Verification**:
- [ ] Resource ID confirmed
- [ ] Current record retrieved
- [ ] Verification sources identified

**Research Phase**:
- [ ] Official website checked
- [ ] Government directories consulted
- [ ] Contact information verified
- [ ] Service areas confirmed
- [ ] Service types researched
- [ ] **National scope verified (if applicable)** 🚨

**Decision Phase**:
- [ ] All fields evaluated
- [ ] Changes documented
- [ ] Sources recorded
- [ ] Confidence levels assigned

**Implementation Phase**:
- [ ] Updates applied
- [ ] Coverage areas managed
- [ ] **National coverage assigned (if applicable)** 🚨
- [ ] Verification report added
- [ ] Status updated to "needs_review"

**Post-Implementation**:
- [ ] Changes verified
- [ ] No errors occurred
- [ ] Documentation complete
- [ ] Ready for review
