# Resource Verification Process Guide

## 🚨 IMMEDIATE EXECUTION REQUIRED

**⚠️ CRITICAL INSTRUCTION**: When asked to verify a record, execute this verification process immediately without asking for permission, confirmation, or resource selection. The task is to:
1. **START VERIFICATION IMMEDIATELY** - Find and verify a resource
2. **FOLLOW PROCESS EXACTLY** - Use the systematic approach outlined below
3. **VERIFY EVERY FIELD** - Complete comprehensive field-by-field verification
4. **NO PERMISSION REQUESTS** - Do not ask "what should I do next" or wait for confirmation

**EXECUTION ORDER**: Resource Selection → Data Extraction → Field Verification → Updates → Status Management → Documentation

---

## 📋 Overview

This document outlines the systematic manual verification process for evaluating and updating resource records in the Community Resource Directory. This process ensures data accuracy, completeness, and provides an audit trail for all changes through field-by-field verification using official websites, government resources, Google listings, social media, and other authoritative sources.

**Target Audience**: Data managers, administrators, staff, and AI assistants who need to verify and update resource records. This process supports both human verification and AI-assisted verification workflows.

**⚠️ IMPORTANT**: This process can be significantly enhanced with AI assistance but requires human oversight and final validation. Each field must be verified against multiple sources to ensure data quality. AI tools can handle web-based verification and logical inference, while humans provide context, phone verification, and final validation.

**🚨 CRITICAL FIELD FORMAT REQUIREMENT**: All text fields (Populations Served, Eligibility Requirements, Languages Available, Cost Information, etc.) must use plain text format, NOT Python lists, JSON, or technical notation. Use natural language like "adults, individuals with substance use disorders" NOT `['adults', 'individuals_with_substance_use_disorders']`. See Section 2.6.1.1 for complete format specifications.

**⚠️ IMPORTANT: First Verification Run Considerations**
During the initial verification run, you may encounter resources in inconsistent states:
- **Published resources without verification**: These were published before verification requirements were implemented
- **Resources in various statuses**: draft, needs_review, or published
- **Missing verification fields**: last_verified_at, last_verified_by may be empty

**First Run Workflow:**
1. **Verify all resources** regardless of current status
2. **Apply all necessary corrections** during verification
3. **Move ALL resources to "needs_review" status** after verification
4. **Human review required** before any resource moves to "published" status
5. **Establish consistent baseline** for future verification cycles

---

## 🚨 CRITICAL VERIFICATION REQUIREMENTS - READ FIRST!

### **MANDATORY: Fresh Verification Every Time**
- **NEVER trust existing verification notes** without re-verifying
- **NEVER skip web searches** for current information
- **NEVER assume data is correct** from previous sessions
- **ALWAYS conduct fresh verification** for each verification session
- **ALWAYS check multiple sources** for each field

### **What This Means in Practice:**
1. **Every verification session requires fresh web searches**
2. **Every field must be verified against current sources**
3. **Previous verification notes are reference only, not current truth**
4. **AI assistants must conduct real-time web verification**
5. **Human verifiers must validate AI findings**

### **Common Mistakes to Avoid:**
- ❌ Reading existing notes and assuming they're current
- ❌ Skipping web searches because "it was verified before"
- ❌ Trusting previous verification without re-checking
- ❌ Making updates based on assumptions rather than verification
- ❌ Treating verification as data entry rather than fact-checking

### **Verification vs. Data Entry:**
- **VERIFICATION**: Checking facts against multiple current sources
- **DATA ENTRY**: Copying information from one place to another
- **This process is VERIFICATION, not data entry**

---

## 🚀 Quick Start

### Prerequisites
```bash
# Always start with virtual environment activated
cd /home/stewood/rl
source venv/bin/activate
```

### Basic Workflow
1. **Select Resource**: Use CLI to find resource needing verification
2. **Extract Data**: Get complete current resource information
3. **Verify Fields**: Check each field against multiple sources
4. **Document Changes**: Create comprehensive change summary
5. **Update Record**: Apply changes via CLI with proper documentation
6. **Quality Check**: Verify all changes are correctly applied
7. **Status Management**: Move resource to "needs_review" status after verification

### **⚠️ CRITICAL: Verification Status Workflow**
**The verification process follows this strict workflow:**

1. **Resource Selection**: Find resource in any status (draft, needs_review, published)
2. **Verification Process**: Complete comprehensive field-by-field verification
3. **Status Update**: Move resource to "needs_review" status after verification
4. **Human Review**: Human verifier reviews AI verification and approves
5. **Publication**: Only after human validation can resource move to "published" status

**Key Rules:**
- **After verification**: ALL resources must be in "needs_review" status
- **Verification ≠ Publication**: Verification is technical, publication requires human approval
- **Published resources**: Should never need verification (they should already be verified)
- **Human oversight**: Required for final publication decision

### **NEW: Quick CLI Reference**
```bash
# Always check help when unsure
python manage.py resource_cli --help
python manage.py resource_cli update --help

# Remember: Field names use underscores, not hyphens
# CORRECT: --hours_of_operation, --eligibility_requirements
# WRONG: --hours-of-operation, --eligibility-requirements

# NEW: Category management commands
python manage.py resource_cli update [RESOURCE_ID] --category="Education"
python manage.py resource_cli update [RESOURCE_ID] --category="Mental Health"
```

---

## 📊 Available CLI Commands for Verification

### Resource Selection
```bash
# Show general help
python manage.py resource_cli --help

# List resources needing verification
python manage.py resource_cli list --status=needs_review

# Show specific resource details
python manage.py resource_cli show [RESOURCE_ID]

# Search for specific resources
python manage.py resource_cli search "search term"
```

### Resource Updates
```bash
# Update individual fields (NOTE: Use underscores, not hyphens)
python manage.py resource_cli update [RESOURCE_ID] --phone="[NEW_PHONE]"

# Update multiple fields with JSON
python manage.py resource_cli update [RESOURCE_ID] --json='{"phone":"[NEW_PHONE]","hours_of_operation":"[NEW_HOURS]"}'

# Update status
python manage.py resource_cli update [RESOURCE_ID] --status=published

# NEW: Update resource category
python manage.py resource_cli update [RESOURCE_ID] --category="Education"
python manage.py resource_cli update [RESOURCE_ID] --category="Mental Health"

# NEW: Update resource service types
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Education,Child Care"
python manage.py resource_cli update [RESOURCE_ID] --remove-service-types="Child Care"
python manage.py resource_cli update [RESOURCE_ID] --set-service-types="Education,Health Education"
python manage.py resource_cli update [RESOURCE_ID] --clear-service-types

# IMPORTANT: Field names use underscores, not hyphens
# CORRECT: --hours_of_operation, --eligibility_requirements, --populations_served
# INCORRECT: --hours-of-operation, --eligibility-requirements, --populations-served
```

---

## 🔍 Step-by-Step Verification Process

### **Step 1: Resource Selection & Data Extraction**

#### 1.1 Select Resource to Verify
```bash
# Option A: Find resources WITHOUT verification dates (never verified)
python manage.py resource_cli list --limit=10

# Option B: Specific resource by ID
python manage.py resource_cli show 138

# Option C: Find resources that have never been verified
python manage.py shell -c "
from directory.models import Resource;
unverified = Resource.objects.filter(last_verified_at__isnull=True).order_by('?')[:5];
[print(f'ID: {r.id}, Name: {r.name}, Status: {r.status}') for r in unverified];
"

# Option D: Search by category or location (for unverified resources)
python manage.py resource_cli list --category="Mental Health" --city="London"

# ⚠️ IMPORTANT: Focus on resources WITHOUT verification dates
# - "needs_review" status means already verified, waiting for human approval
# - Resources without last_verified_at need fresh verification
# - Published resources without verification dates are priority targets
```

#### 1.1.1 Resource Selection Priorities - CRITICAL

**⚠️ IMPORTANT: Resource Selection Criteria**

| Resource Status | Verification Date | Priority | Action Required |
|-----------------|-------------------|----------|-----------------|
| **Published** | `last_verified_at` is NULL | 🔴 **HIGHEST** | Fresh verification needed |
| **Published** | `last_verified_at` has date | 🟡 **LOW** | Already verified, check if due for re-verification |
| **Needs Review** | `last_verified_at` has date | 🟡 **LOW** | Already verified, waiting for human approval |
| **Needs Review** | `last_verified_at` is NULL | 🔴 **HIGH** | Verification completed but date not set |
| **Draft** | `last_verified_at` is NULL | 🟢 **MEDIUM** | New resource, needs initial verification |

**🚨 CRITICAL: Focus on resources WITHOUT verification dates**
- **"needs_review" status** = Already verified, waiting for human approval
- **Missing verification date** = Never verified or verification incomplete
- **Published without verification** = High priority for verification

**Recommended Selection Order:**
1. **Published resources without verification dates** (highest priority)
2. **Draft resources without verification dates** (medium priority)  
3. **Resources with old verification dates** (check if due for re-verification)
4. **"needs_review" resources** (already verified, lowest priority)

#### 1.2 Extract Complete Current Data
```bash
# Get comprehensive resource details
python manage.py resource_cli show [RESOURCE_ID]

# Extract specific fields for analysis
python manage.py shell -c "
from directory.models import Resource; 
import json; 
resource = Resource.objects.get(id=[RESOURCE_ID]); 
data = {
    'id': resource.id, 
    'name': resource.name, 
    'category': resource.category.name if resource.category else None, 
    'description': resource.description, 
    'phone': resource.phone, 
    'email': resource.email, 
    'website': resource.website, 
    'address1': resource.address1, 
    'address2': resource.address2, 
    'city': resource.city, 
    'state': resource.state, 
    'county': resource.county, 
    'postal_code': resource.postal_code, 
    'hours_of_operation': resource.hours_of_operation, 
    'eligibility_requirements': resource.eligibility_requirements, 
    'populations_served': resource.populations_served, 
    'cost_information': resource.cost_information, 
    'languages_available': resource.languages_available, 
    'source': resource.source, 
    'notes': resource.notes
}; 
print(json.dumps(data, indent=2))
"
```

---

### **Step 2: PRE-VERIFICATION CHECKLIST - MANDATORY**

**⚠️ CRITICAL: Complete this checklist BEFORE proceeding with any field verification or updates**

#### **2.0 Verification Session Setup**
- [ ] **Fresh verification session started** (not relying on previous notes)
- [ ] **Web browser/tools ready** for real-time source checking
- [ ] **Multiple source strategy planned** (primary + secondary + tertiary)
- [ ] **Verification template prepared** using Section 4.3 format
- [ ] **Time allocated** for systematic field-by-field verification

#### **2.1 Source Verification Preparation**
- [ ] **Official website accessed** and verified as current
- [ ] **Google Business listing** located and checked
- [ ] **Government databases** identified for cross-reference
- [ ] **Social media accounts** located (if applicable)
- [ ] **Alternative contact methods** identified for verification

#### **2.2 Verification Method Confirmation**
- [ ] **MCP Web Search tools ready** for AI assistants (preferred over basic command-line tools)
- [ ] **MCP Playwright browser tools ready** for AI assistants (for direct website access and verification)
- [ ] **Phone verification plan** for human verifiers
- [ ] **Geographic verification tools** (Google Maps, etc.) ready
- [ ] **Documentation template** ready for comprehensive notes
- [ ] **Confidence scoring system** understood and ready

**ONLY PROCEED TO FIELD VERIFICATION AFTER COMPLETING ALL CHECKLIST ITEMS ABOVE**

---

### **Step 2.1: Field-by-Field Verification Matrix**

#### 2.1 Basic Information Fields

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **Name** | **MANDATORY**: • MCP Web Search for current information<br>• MCP Playwright browser access to official website<br>• Google Business listing (current)<br>• Government databases (current)<br>**NEVER**: Trust existing data without checking<br>**NEVER**: Use basic command-line tools when MCP tools are available | • Organization's main website (MUST ACCESS LIVE via MCP Playwright)<br>• MCP Web Search results for current information<br>• Google Maps (MUST SEARCH CURRENT)<br>• State/local government sites (MUST VERIFY CURRENT) | Matches official branding exactly |
| **Description** | • Compare with official materials<br>• Check current services<br>• **CRITICAL**: Verify target populations (men vs. women vs. all)<br>• Check for service scope changes | • About/Service pages<br>• Mission statements<br>• Recent announcements<br>• Program descriptions | Accurately reflects current services and target populations |
| **Category** | • Review actual services offered<br>• Compare with category definitions | • Service descriptions<br>• Program listings<br>• Contact staff | Matches primary service focus |

#### 2.2 Contact Information Fields

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **Phone** | • Call the number<br>• Check website contact page<br>• Verify on Google listing | • Official website<br>• Google Business<br>• Phone directory | Number is active and answered |
| **Email** | • Check website contact page<br>• Test email format<br>• Look for contact forms | • Contact page<br>• Staff directory<br>• About page | Email address is current and functional |
| **Website** | • Test link functionality<br>• Check for redirects<br>• Verify content relevance | • Direct URL test<br>• Google search results<br>• Archive.org for changes | Website loads and contains relevant info |

#### 2.3 Location Fields

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **Address1/2** | • Google Maps verification<br>• Official website<br>• Government records | • Google Maps<br>• Official website<br>• County records | Address exists and is accurate |
| **City** | • Verify with address<br>• Check government boundaries<br>• Confirm with organization | • Google Maps<br>• City government site<br>• USPS database | City name is correct and current |
| **State** | • Verify state code<br>• Check with address<br>• Confirm jurisdiction | • USPS standards<br>• Government sites<br>• Address validation | 2-letter code is correct |
| **County** | • Verify county boundaries<br>• Check government records<br>• Confirm with address | • County government site<br>• Census data<br>• GIS mapping | County name is accurate |
| **Postal Code** | • Verify with address<br>• Check USPS database<br>• Confirm city/county match | • USPS lookup<br>• Google Maps<br>• Address validation | ZIP code matches location |

#### 2.4 Service Information Fields

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **Hours of Operation** | • Check official website<br>• Call organization<br>• Check Google listing | • Website hours page<br>• Phone verification<br>• Google Business | Hours are current and accurate |
| **Eligibility Requirements** | • Review official materials<br>• Check program guidelines<br>• Contact staff<br>• **⚠️ FORMAT**: Use plain text, natural language | • Program descriptions<br>• Application forms<br>• Staff consultation | Requirements are clearly stated in plain text format |
| **Populations Served** | • Check target demographics<br>• Review program focus<br>• Verify with staff<br>• **⚠️ FORMAT**: Use plain text, comma-separated | • Service descriptions<br>• Program materials<br>• Staff consultation | Populations are accurately identified in plain text format |
| **Cost Information** | • Check current pricing<br>• Review fee schedules<br>• Verify with staff<br>• **⚠️ FORMAT**: Use plain text, natural language | • Website pricing<br>• Program materials<br>• Staff consultation | Cost information is current in plain text format |
| **Languages Available** | • Check website language options<br>• Review staff capabilities<br>• Verify with organization<br>• **⚠️ FORMAT**: Use plain text, comma-separated | • Website content<br>• Staff directory<br>• Program materials | Language offerings are accurate in plain text format |

#### 2.5 Service Areas (CRITICAL FIELD)

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **Service Areas** | • **CRITICAL**: Verify where services are actually offered<br>• Check for geographic restrictions<br>• Review transportation arrangements<br>• Look for partnerships/outreach | • Program descriptions<br>• Eligibility criteria<br>• Transportation information<br>• Partnership listings<br>• Outreach programs | Service areas accurately reflect where people can access services |

**⚠️ IMPORTANT DISTINCTION**: Service areas describe **where services are offered**, not just where the organization is physically located. They may be:
- **Same as physical address** (local services only)
- **Larger than physical address** (regional, state, or multi-state services)
- **Different from physical address** (outreach programs, mobile services)

**Verification Process for Service Areas:**

1. **Understand Service Model**: Determine if this is a local, regional, state, or multi-state service
2. **Check Website for Geographic Clues**:
   - Geographic restrictions mentioned
   - Who can apply (residents of specific areas?)
   - Transportation arrangements
   - Partnerships with other organizations
   - Outreach programs in other communities
3. **Look for Service Indicators**:
   - "Serving the Appalachian region" vs. "local community"
   - "Kentucky residents" vs. "open to all"
   - "Transportation provided" vs. "must arrange own transportation"
   - "Partnerships with agencies in [specific counties]"
4. **Use Inference Based on Service Type**:
   - **Local/County**: Immediate area only
   - **Regional**: Multiple counties in a region
   - **State**: All residents of the state
   - **Multi-state**: Accepts out-of-state residents
5. **Check Similar Organizations**: Review service area patterns of similar services in the database

**Common Service Area Patterns**:
- **Emergency Services**: Often serve immediate area + surrounding counties
- **Residential Programs**: May accept people from broader areas (people travel for treatment)
- **Outpatient Services**: Usually local/regional
- **Hotlines**: Often statewide or nationwide
- **Government Services**: Usually restricted to specific jurisdictions

**Practical Steps for Adding Service Areas:**

1. **Check Available Service Areas**:
   ```bash
   # List all available service areas
   python manage.py resource_cli list-areas
   
   # Search for specific areas
   python manage.py resource_cli list-areas --search="Kentucky"
   python manage.py resource_cli list-areas --search="Whitley"
   ```

2. **Add Service Areas to Resource**:
   ```bash
   # Add single service area
   python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky"
   
   # Add multiple service areas
   python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky,Whitley County"
   
   # Note: Use exact names as they appear in list-areas output
   ```

3. **Verify Service Area Assignment**:
   ```bash
   # Check current service areas
   python manage.py resource_cli show [RESOURCE_ID]
   
   # Look for "coverage_areas" section in output
   ```

**Common Service Area Assignment Patterns:**

| Service Type | Typical Service Areas | Rationale |
|--------------|----------------------|------------|
| **Residential Programs** | State + Local County | People travel for treatment; no geographic restrictions |
| **Emergency Services** | Local County + Surrounding Counties | Immediate response + regional coverage |
| **Hotlines** | State or Nationwide | Phone/online access from anywhere |
| **Outpatient Services** | Local County + Regional Counties | Regular attendance required |
| **Government Services** | Specific Jurisdiction Only | Legal restrictions apply |
| **Mobile/Outreach** | Broader than Physical Location | Services delivered in multiple areas |

**🚨 CRITICAL: Nationwide Services Handling**

**⚠️ IMPORTANT**: For nationwide services (available to users in all states), use the special nationwide coverage area:

#### **Nationwide Coverage Area**
- **Name**: "United States (All States and Territories)"
- **ID**: 43273
- **Type**: POLYGON
- **Purpose**: Represents services available nationwide

#### **When to Use Nationwide Coverage Area**
- **Hotlines**: Crisis hotlines, suicide prevention, poison control
- **Online Services**: Web-based directories, information services
- **Government Services**: Federal programs, national resources
- **Emergency Services**: National emergency numbers (like 988)
- **Veterans Services**: National organizations serving all veterans
- **Information Resources**: National databases, directories, helplines

#### **How to Assign Nationwide Coverage**
```bash
# Add nationwide coverage to any resource
python manage.py resource_cli update [RESOURCE_ID] --add-areas="United States (All States and Territories)"

# Verify nationwide coverage assignment
python manage.py resource_cli show [RESOURCE_ID]
# Look for "coverage_areas" section showing nationwide area
```

#### **Nationwide vs. Local Service Areas**
- **Nationwide Services**: Use "United States (All States and Territories)" coverage area
- **Local Services**: Use specific city, county, or state coverage areas
- **Regional Services**: Use multiple specific coverage areas (e.g., "Kentucky, Ohio, Indiana")
- **Hybrid Services**: Can use both nationwide + specific areas if appropriate

#### **Verification Checklist for Nationwide Services**
- [ ] **Service Scope Confirmed**: Service is actually available nationwide
- [ ] **No Geographic Restrictions**: No limitations based on user location
- **Coverage Area Assigned**: "United States (All States and Territories)" assigned
- [ ] **Discoverability Verified**: Service appears in searches from any state
- [ ] **Documentation Updated**: Notes reflect nationwide availability

#### **Common Nationwide Service Examples**
- **988 Suicide & Crisis Lifeline**: National crisis hotline
- **Poison Control Center**: National poison information hotline
- **The Trevor Project**: National LGBTQ+ crisis intervention
- **DAV Veterans Services**: National veterans organization
- **Homeless Shelter Directory**: National online directory
- **Safe to Sleep Campaign**: National public health campaign

**Troubleshooting Service Area Issues:**

- **"Invalid service areas ignored"**: Check exact spelling in `list-areas` output
- **Multiple areas with same name**: Use state context to identify correct area
- **Area not found**: Verify area exists in database before assignment
- **Permission errors**: Ensure you have write access to the resource

**🚨 Nationwide Service Troubleshooting:**

- **"No nationwide coverage area found"**: Use "United States (All States and Territories)" (ID: 43273)
- **Service appears local-only**: Check if service is actually nationwide and assign appropriate coverage
- **Users can't find nationwide services**: Ensure nationwide coverage area is assigned
- **Mixed coverage needed**: Can assign both nationwide + specific areas for hybrid services

**🚨 Service Area Assignment Troubleshooting:**

#### **Common Service Area Issues and Solutions**

**Problem**: "Invalid service areas ignored: [AREA_NAME]"
**Solutions**:
1. **Check exact spelling**: `python manage.py resource_cli list-areas --search="[EXACT_NAME]"`
2. **Look for state context** in results (state_fips field)
3. **Use exact name** as it appears in list-areas output
4. **Common issue**: "Fayette County" vs "Fayette County, KY" - use exact match

**Problem**: "No valid service areas found in: [AREA_NAME]"
**Solutions**:
1. **Check for duplicate names**: Multiple areas may have the same name
2. **Use area context**: Some areas exist in multiple states
3. **Verify area type**: STATE vs COUNTY vs CITY may have same name
4. **✅ NEW: Use area ID**: Use the numeric ID instead of name for precise control

**Problem**: Multiple areas with same name (e.g., "Tennessee")
**Solutions**:
1. **Check area details**: `python manage.py resource_cli list-areas --search="Tennessee"`
2. **Look for state_fips**: Different state_fips indicate different areas
3. **Use state context**: Specify the state when adding areas
4. **✅ NEW: Use area IDs**: Add specific areas by their numeric ID for exact control

#### **Service Area Assignment Best Practices**

**Before Adding Service Areas**:
```bash
# Always check available areas first
python manage.py resource_cli list-areas --search="[AREA_NAME]"

# Look for state context in results
# Example: Tennessee appears in both KY (state_fips: 21) and IL (state_fips: 17)
```

**When Adding Service Areas**:
```bash
# ✅ RECOMMENDED: Use area IDs for precise control
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"

# Add areas one at a time to identify conflicts
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky"
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Tennessee"

# Use set-areas to replace all areas at once
python manage.py resource_cli update [RESOURCE_ID] --set-areas="Kentucky,West Virginia"

# Clear and re-add if needed
python manage.py resource_cli update [RESOURCE_ID] --clear-areas
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky,West Virginia"
```

**✅ NEW: Area ID Method - Best Practice for Duplicate Names**

**Why Use Area IDs?**
- **Precise Control**: Target exact geographic areas (STATE vs CITY vs COUNTY)
- **Avoid Duplicates**: Bypass issues with multiple areas having the same name
- **Reliable Assignment**: Guaranteed to add the specific area you want
- **Audit Trail**: Clear record of which exact areas were assigned

**How to Use Area IDs**:
```bash
# 1. Find the area ID you need
python manage.py resource_cli list-areas --search="Tennessee"

# 2. Look for the specific area type and state
# Example output:
# {
#   "id": 35476,        ← This is the ID you want
#   "name": "Tennessee",
#   "kind": "STATE",    ← This is a STATE (not CITY)
#   "state_fips": "47"  ← This is Tennessee state
# }

# 3. Use the ID to add the area
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476"

# 4. Add multiple areas by ID
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"
```

**Common Area IDs for Appalachian Region**:
```bash
# Kentucky (STATE) - ID: 35480
# Tennessee (STATE) - ID: 35476  
# Virginia (STATE) - ID: 35499
# West Virginia (STATE) - ID: 35447

# Example: Add all four Appalachian states
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"
```

**Verifying Service Area Assignment**:
```bash
# Check current service areas
python manage.py resource_cli show [RESOURCE_ID]

# Look for "coverage_areas" section in output
# Should show all assigned areas with their IDs and types
```

**⚠️ Common Nationwide Service Mistakes:**
- ❌ **Assigning only local areas** to nationwide services (limits discoverability)
- ❌ **Using multiple state areas** instead of nationwide area (redundant and confusing)
- ❌ **Leaving nationwide services** without any coverage areas (undiscoverable)
- ✅ **Using nationwide coverage area** for truly nationwide services
- ✅ **Combining nationwide + local** for services with national scope + local offices

#### 2.6 Service Flags

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **is_emergency_service** | • Check website emergency info<br>• Review service descriptions<br>• Contact organization | • Emergency service pages<br>• Crisis intervention info<br>• Staff consultation | Flag accurately reflects emergency capability |
| **is_24_hour_service** | • Verify hours of operation<br>• Check emergency protocols<br>• Contact organization | • Hours page<br>• Emergency procedures<br>• Staff consultation | Flag accurately reflects 24/7 availability |

#### 2.7 Verification Tracking Fields

| Field | Verification Method | Sources to Check | Success Criteria |
|-------|-------------------|------------------|------------------|
| **verification_frequency_days** | • Check service type and stability<br>• Review organization characteristics<br>• Compare with similar services | • Service type patterns<br>• Organization stability<br>• Industry standards | Appropriate frequency for service type (180 days typical) |
| **last_verified_at** | • Set when verification completed<br>• Update when moving to published status<br>• Track verification completion | • Verification completion timestamp<br>• Status change to published<br>• Verification session completion | Timestamp set when verification is fully completed |
| **last_verified_by** | • Set verifier name/ID<br>• Track who completed verification<br>• Maintain audit trail | • Verifier identification<br>• Verification session completion<br>• Audit trail requirements | Verifier properly identified and recorded |

---

### **Step 2.6: Advanced Verification Techniques for AI and Human Verifiers**

#### 2.6.1 Inference-Based Verification
When direct verification is not possible, use logical inference from available information to verify fields:

**⚠️ IMPORTANT: Test Resources vs. Real Resources**
- **Test Resources**: May contain fictional data for training purposes
- **Real Resources**: Must be verified against actual sources
- **Verification Approach**: Different for each type
  - Test Resources: Focus on data quality and completeness
  - Real Resources: Focus on source verification and accuracy

| Field Type | Inference Method | Confidence Level | Example |
|------------|------------------|------------------|---------|
| **Eligibility Requirements** | • Analyze program descriptions<br>• Review target populations<br>• Check service restrictions | HIGH (85-95%) | "Men seeking recovery" → "Must be male, seeking addiction recovery" |
| **Populations Served** | • Review program focus<br>• Analyze service descriptions<br>• Check demographic mentions | HIGH (85-95%) | "Men seeking recovery" → "adults, men, individuals with substance use disorders" |
| **Languages Available** | • Analyze website content<br>• Check social media posts<br>• Review program materials | HIGH (90-95%) | All content in English → "English only" |
| **Cost Information** | • Review program descriptions<br>• Check for fee mentions<br>• Analyze financial statements | HIGH (85-95%) | "Free program" → "Free program, no cost to participants" |
| **Insurance Acceptance** | • Check program cost structure<br>• Review billing information<br>• Analyze service descriptions | HIGH (85-95%) | "No cost program" → "Insurance not applicable" |

#### 2.6.1.1 Field Format Specifications - CRITICAL

**⚠️ IMPORTANT**: The following field format specifications are MANDATORY. Incorrect formatting will cause display issues and user confusion.

| Field | Expected Format | ✅ CORRECT Examples | ❌ WRONG Examples |
|-------|-----------------|---------------------|-------------------|
| **Populations Served** | Plain text, comma-separated | "adults, individuals with substance use disorders, kentucky residents" | `['adults', 'individuals_with_substance_use_disorders']` |
| **Eligibility Requirements** | Plain text, natural language | "Must be 18 years or older, seeking recovery from addiction" | `['18+', 'addiction_recovery']` |
| **Languages Available** | Plain text, comma-separated | "English, Spanish, French" | `['English', 'Spanish', 'French']` |
| **Cost Information** | Plain text, natural language | "Free program, no cost to participants" | `['free', 'no_cost']` |
| **Insurance Accepted** | Plain text, natural language | "Medicaid, Medicare, private insurance accepted" | `['Medicaid', 'Medicare', 'private']` |
| **Capacity** | Plain text, natural language | "Up to 25 residents at a time" | `[25, 'residents']` |

**🚨 CRITICAL REMINDER**: All text fields should use natural, human-readable language. The system will handle the formatting automatically. Never use Python list syntax, JSON format, or technical notation in text fields.

**CLI Command Format Examples**:
```bash
# ✅ CORRECT - Use natural language text
python manage.py resource_cli update [ID] --populations_served="adults, individuals with substance use disorders, kentucky residents"

# ✅ CORRECT - Use natural language text
python manage.py resource_cli update [ID] --eligibility_requirements="Must be 18 years or older, seeking recovery from addiction"

# ✅ CORRECT - Use natural language text
python manage.py resource_cli update [ID] --languages_available="English, Spanish"

# ❌ WRONG - Don't use list syntax
python manage.py resource_cli update [ID] --populations_served="['adults', 'individuals_with_substance_use_disorders']"

# ❌ WRONG - Don't use list syntax
python manage.py resource_cli update [ID] --eligibility_requirements="['18+', 'addiction_recovery']"
```

#### 2.6.2 Geographic Verification Techniques
For location-related fields that may not be explicitly stated:

| Field | Verification Method | Tools/Sources | Confidence Level |
|-------|-------------------|---------------|------------------|
| **County** | • Geographic database lookup<br>• State county maps<br>• USPS address validation | • Geographic lookup services<br>• Kentucky county maps<br>• Address validation APIs | HIGH (95%) |
| **Postal Code** | • Address validation services<br>• USPS database lookup<br>• Geographic mapping tools | • USPS lookup tools<br>• Address validation APIs<br>• Mapping services | HIGH (95%) |
| **Address Validation** | • Google Maps verification<br>• Street view confirmation<br>• Address format validation | • Google Maps<br>• Street View<br>• Address validation tools | HIGH (90-95%) |

#### 2.6.3 Content Analysis for Inference
Use systematic content analysis to extract information:

**Program Description Analysis:**
- **Target Population**: Look for demographic indicators (age, gender, specific groups)
- **Service Scope**: Identify what services are/aren't provided
- **Access Requirements**: Note any mentioned qualifications or restrictions
- **Operational Details**: Extract hours, capacity, or availability information

**Contact Information Analysis:**
- **Primary Contact**: Identify main contact methods
- **Alternative Contacts**: Note secondary contact options
- **Response Times**: Look for mentioned response expectations

**Service Information Analysis:**
- **Program Structure**: Identify program length, phases, or components
- **Specializations**: Note any specific focus areas or expertise
- **Limitations**: Identify any service restrictions or exclusions

#### 2.6.4 Verification Confidence Scoring with Inference

| Confidence Level | Criteria | Verification Methods Used |
|------------------|----------|---------------------------|
| **HIGH (90-100%)** | • Direct verification from primary sources<br>• Logical inference from explicit statements<br>• Geographic facts from authoritative sources | Primary sources + inference |
| **MEDIUM (70-89%)** | • Secondary source verification<br>• Partial inference from available data<br>• Cross-referenced information | Secondary sources + partial inference |
| **LOW (50-69%)** | • Tertiary source verification<br>• Weak inference from limited data<br>• Unverified assumptions | Tertiary sources + weak inference |
| **UNVERIFIED (<50%)** | • No reliable sources found<br>• Cannot infer from available data<br>• Information not applicable | No verification possible |

#### 2.6.5 When to Use Inference vs. Direct Verification

**Use Inference When:**
- ✅ Information is logically implied by available data
- ✅ Multiple sources support the same conclusion
- ✅ Information follows standard patterns or practices
- ✅ Geographic or administrative facts are involved

**Avoid Inference When:**
- ❌ Information contradicts available evidence
- ❌ Multiple sources provide conflicting information
- ❌ Information requires subjective interpretation
- ❌ Information involves legal or policy requirements

**Documentation Requirements for Inference:**
```
Inference Used: [FIELD_NAME]
Basis for Inference: [EXPLICIT_EVIDENCE_OR_PATTERN]
Confidence Level: [HIGH/MEDIUM/LOW]
Alternative Interpretations: [OTHER_POSSIBLE_MEANINGS]
Verification Notes: [WHY_INFERENCE_IS_APPROPRIATE]
```

---

### **Step 3: Source Verification Hierarchy**

#### 3.1 Primary Sources (Most Reliable - 90-100% confidence)
1. **Official Organization Website** - Direct from the source via MCP Playwright browser access
2. **MCP Web Search Results** - Current web search results for real-time information
3. **Government Databases** - .gov domains, official records
4. **Direct Phone Contact** - Speaking with staff
5. **Official Social Media** - Verified organization accounts

#### 3.2 Secondary Sources (Cross-Reference - 70-89% confidence)
1. **Google Business Listings** - Public business information
2. **Local Government Sites** - City/county official information
3. **Professional Directories** - Industry-specific listings
4. **News Articles** - Recent coverage of the organization

#### 3.3 Tertiary Sources (Supporting - 50-69% confidence)
1. **Third-Party Directories** - Community resource listings
2. **Social Media Mentions** - Community discussions
3. **Review Sites** - User-generated content
4. **Archive.org** - Historical website versions

---

### **Step 4: Verification Documentation Template**
#### **Step 4.1: Adding Verification Notes via CLI - CRITICAL FORMATTING GUIDANCE**

#### 4.1 Field Verification Log
For each field, document using this format:

**⚠️ IMPORTANT: Different Documentation for Test vs. Real Resources**
- **Test Resources**: Document data quality improvements and training value
- **Real Resources**: Document source verification and accuracy validation
- **Verification Notes**: Always clarify resource type (test vs. real)
- **MCP Tool Usage**: Document which MCP tools were used for verification (Web Search, Playwright)

```
Field: [FIELD_NAME]
Current Value: [CURRENT_VALUE]
Verification Method: [METHOD_USED]
Sources Consulted: [LIST_OF_SOURCES]
Verification Date: [DATE]
Verification Result: [VERIFIED/CORRECTED/NOT_FOUND]
New Value (if changed): [NEW_VALUE]
Confidence Level: [HIGH/MEDIUM/LOW]
Notes: [ADDITIONAL_INFORMATION]
```

#### 4.2 Source Documentation
```
Source 1: [URL/Contact Method]
- What was verified: [Specific information]
- Verification date: [Date]
- Reliability score: [1-10]

Source 2: [URL/Contact Method]
- What was verified: [Specific information]
- Verification date: [Date]
- Reliability score: [1-10]
```

#### 4.3 Comprehensive Verification Session Template
Use this template for the Verification Notes section (accepts Markdown format):

```markdown
## Verification Session - [DATE]

### Session Overview
- **Resource ID**: [ID]
- **Resource Name**: [NAME]
- **Verification Date**: [DATE]
- **Verifier**: [NAME/ROLE]
- **Verification Method**: [METHOD_USED]
- **Overall Confidence**: [HIGH/MEDIUM/LOW] (percentage range)

### Sources Consulted

#### 1. [SOURCE_NAME] ([PRIMARY/SECONDARY/TERTIARY] - [CONFIDENCE]%)
- **Verification Date**: [DATE]
- **Fields Verified**: [LIST_OF_FIELDS]
- **Reliability Score**: [X/10]
- **Notes**: [RELEVANT_DETAILS]

#### 2. [SOURCE_NAME] ([PRIMARY/SECONDARY/TERTIARY] - [CONFIDENCE]%)
- **Verification Date**: [DATE]
- **Fields Verified**: [LIST_OF_FIELDS]
- **Reliability Score**: [X/10]
- **Notes**: [RELEVANT_DETAILS]

### Field Verification Results

#### ✅ VERIFIED FIELDS ([X/Y] - [PERCENTAGE]%)
- **[FIELD_NAME]**: [CURRENT_VALUE] - ✅ [VERIFICATION_SUMMARY]
- **[FIELD_NAME]**: [CURRENT_VALUE] - ✅ [VERIFICATION_SUMMARY]

#### 🔍 INFERENCE-VERIFIED FIELDS ([X/Y] - [PERCENTAGE]%)
- **[FIELD_NAME]**: [CURRENT_VALUE] - 🔍 [INFERENCE_SUMMARY]
  - **Basis for Inference**: [EXPLICIT_EVIDENCE_OR_PATTERN]
  - **Confidence Level**: [HIGH/MEDIUM/LOW]
  - **Alternative Interpretations**: [OTHER_POSSIBLE_MEANINGS]

#### ❌ FIELDS REQUIRING CORRECTION ([X/Y] - [PERCENTAGE]%)
- **[FIELD_NAME]**: [CURRENT_VALUE] → [SHOULD_BE]
  - **Issue**: [DESCRIPTION_OF_PROBLEM]
  - **Evidence**: [PROOF_FROM_SOURCES]
  - **Impact**: [USER_IMPACT]
  - **Priority**: [HIGH/MEDIUM/LOW]

#### 🔄 CATEGORY VERIFICATION (NEW)
- **Current Category**: [CURRENT_CATEGORY]
- **Verified Category**: [VERIFIED_CATEGORY]
- **Category Change Required**: [YES/NO]
- **Rationale**: [EXPLANATION_OF_CATEGORY_CHANGE]
- **CLI Command**: `python manage.py resource_cli update [RESOURCE_ID] --category="[NEW_CATEGORY]"`

#### 📝 APPROPRIATELY EMPTY FIELDS
- **[FIELD_NAMES]**: Empty ([REASON_FOR_EMPTINESS])

### Verification Confidence Scoring
- **HIGH (90-100%)**: [X] fields (direct verification + high-confidence inference)
- **MEDIUM (70-89%)**: [X] fields (secondary sources + medium-confidence inference)
- **LOW (50-69%)**: [X] fields (tertiary sources + weak inference)
- **UNVERIFIED (<50%)**: [X] fields (no verification possible)
- **INFERENCE USED**: [X] fields (logical deduction from available data)

### Quality Assessment
- **Data Accuracy**: [X]% ([X/Y] fields correct)
- **Source Reliability**: [X]% ([PRIMARY/SECONDARY/TERTIARY] sources)
- **Verification Coverage**: [X]% ([X/Y] populated fields verified)
- **Documentation Quality**: [EXCELLENT/GOOD/FAIR/POOR]

### Recommendations
1. **[PRIORITY] Action Required**: [SPECIFIC_ACTION]
2. **Category Update Required**: [YES/NO] - [EXPLANATION_IF_YES]
3. **Verification Frequency**: [RECOMMENDED_CYCLE]
4. **Status**: [RECOMMENDED_STATUS_CHANGE]
5. **Source Documentation**: [ASSESSMENT_OF_SOURCES]

### Next Verification Due
- **Recommended Date**: [DATE] ([X] days from verification)
- **Priority**: [HIGH/MEDIUM/LOW] ([REASONING])
- **Focus Areas**: [SPECIFIC_AREAS_TO_CHECK]

### Verification Session Notes
[SUMMARY_OF_VERIFICATION_SESSION_AND_KEY_FINDINGS]

**Category Changes Made** (if applicable):
- **Previous Category**: [OLD_CATEGORY]
- **New Category**: [NEW_CATEGORY]
- **CLI Command Used**: `python manage.py resource_cli update [RESOURCE_ID] --category="[NEW_CATEGORY]"`
- **Rationale**: [EXPLANATION_OF_WHY_CATEGORY_WAS_CHANGED]

---
*Verification completed by [VERIFIER_NAME] using [METHODOLOGY]. All sources consulted are [ACCESSIBILITY_LEVEL] and [AUTHORITY_LEVEL].*
```

**Note**: This template should be used in the Verification Notes field for each resource. It provides a complete audit trail and ensures consistent documentation across all verification sessions.

---

### **Step 4.1: Adding Verification Notes via CLI - CRITICAL FORMATTING GUIDANCE**

#### **🚨 IMPORTANT: MCP Tool Usage Documentation**
**Always Document MCP Tools Used:**
- **MCP Web Search**: Document search queries and results used for verification
- **MCP Playwright Browser**: Document website URLs accessed and content extracted
- **Tool Selection Rationale**: Explain why specific MCP tools were chosen over basic alternatives

#### **🚨 IMPORTANT: How to Avoid Markdown Escaping Issues**

**The Problem We Just Fixed:**
The verification notes were displaying with raw escape characters (`\n`, `\\n`, escaped asterisks) instead of proper formatting. This happened because the markdown content was pre-escaped before reaching the CLI.

**Root Cause:**
- ❌ **Pre-escaped content**: Markdown copied from tools that added escape characters
- ❌ **Double escaping**: Content processed through multiple tools
- ❌ **Shell escaping**: Shell commands adding extra escape characters
- ❌ **JSON escaping**: Using JSON format with pre-escaped content

#### **✅ CORRECT WAYS to Add Verification Notes**

**Method 1: Direct CLI with Clean Markdown (RECOMMENDED)**
```bash
# ✅ CORRECT - Use clean, unescaped markdown directly
python manage.py resource_cli update [RESOURCE_ID] --notes="## Verification Session - 2025-09-02

### Session Overview
- **Resource ID**: 293
- **Resource Name**: CHI Saint Joseph London Nurturing Children Program

### Sources Consulted
1. Official website (PRIMARY)
2. Google Business listing (SECONDARY)

### Field Verification Results
- **Phone**: ✅ Verified via website
- **Email**: ✅ Verified via website"
```

**Method 2: JSON Format with Clean Markdown**
```bash
# ✅ CORRECT - Use clean markdown in JSON (no escaping)
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "status": "needs_review",
    "notes": "## Verification Session\n\n### Overview\n- **Status**: Verified\n- **Confidence**: HIGH"
}'
```

**Method 3: Copy-Paste from Markdown Editor**
```bash
# ✅ CORRECT - Copy clean markdown from a proper editor
# 1. Write verification notes in a markdown editor (VS Code, Typora, etc.)
# 2. Copy the raw markdown (not HTML or escaped version)
# 3. Paste directly into CLI command
python manage.py resource_cli update [RESOURCE_ID] --notes="[PASTE_CLEAN_MARKDOWN_HERE]"
```

#### **❌ WRONG WAYS That Cause Escaping Issues**

**Method 1: Pre-escaped Content**
```bash
# ❌ WRONG - Content already has escape characters
python manage.py resource_cli update [RESOURCE_ID] --notes="## Session\n\n- **Field**: Value\\n- **Status**: Done"
```

**Method 2: Double-escaped JSON**
```bash
# ❌ WRONG - JSON with escaped content
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "notes": "## Session\\n\\n- **Field**: Value\\n- **Status**: Done"
}'
```

**Method 3: Shell-processed Content**
```bash
# ❌ WRONG - Shell commands adding escapes
python manage.py resource_cli update [RESOURCE_ID] --notes="$(echo '## Session\n\n- **Field**: Value')"
```

#### **🔍 How to Identify Escaped Content**

**Signs of Escaped Content:**
- `\n` instead of actual line breaks
- `\\n` (double-escaped) instead of single line breaks
- `**Field**` instead of `**Field**` (asterisks escaped)
- `\t` instead of actual tabs
- Content appears as one unreadable block

**Signs of Clean Content:**
- Actual line breaks between sections
- Proper markdown headers (`##`, `###`)
- Bold text appears as `**Bold**` (not escaped)
- Lists and formatting work correctly
- Content is readable and properly formatted

#### **🛠️ Troubleshooting Escaped Content**

**If You See Escaped Content:**
1. **Identify the source**: Where did the content come from?
2. **Check for tools**: Was it processed through multiple tools?
3. **Verify format**: Is it raw markdown or HTML/escaped?
4. **Re-add cleanly**: Use one of the correct methods above

**Prevention Checklist:**
- [ ] **Use raw markdown**: Not HTML, not escaped, not processed
- [ ] **Copy from markdown editor**: VS Code, Typora, or similar
- [ ] **Avoid shell processing**: Don't pipe through echo, sed, etc.
- [ ] **Test small samples**: Try with a simple note first
- [ ] **Verify display**: Check the web page after adding notes

#### **📝 Best Practices for Verification Notes**

1. **Write in Markdown Editor First**
   - Use VS Code, Typora, or any markdown editor
   - Ensure proper formatting and line breaks
   - Test the markdown rendering in the editor

2. **Copy Raw Markdown**
   - Copy the raw markdown text (not HTML)
   - Don't copy from web pages or processed sources
   - Avoid copying from tools that add escape characters

3. **Use Direct CLI Method**
   - Prefer `--notes="[CONTENT]"` over JSON for simple updates
   - Use JSON only when updating multiple fields
   - Keep JSON content simple and unescaped

4. **Test After Adding**
   - Always check the web page after adding notes
   - Verify formatting appears correctly
   - Look for any escape characters or formatting issues

5. **Document Your Process**
   - Note which method worked for you
   - Document any issues encountered
   - Share successful approaches with team

**Example of Good Workflow:**
```bash
# 1. Write verification notes in VS Code (markdown mode)
# 2. Copy the raw markdown content
# 3. Add via CLI
python manage.py resource_cli update 293 --notes="[PASTE_CLEAN_MARKDOWN]"

# 4. Verify the result
python manage.py resource_cli show 293

# 5. Check web page display
# Navigate to http://0.0.0.0:8000/resources/293/
```

---

### **Step 5: Update Process**

#### 5.0 PRE-UPDATE VERIFICATION VALIDATION - MANDATORY

**⚠️ CRITICAL: Complete this validation BEFORE making any updates**

#### **5.0.1 Verification Session Validation**
- [ ] **Fresh MCP Web Search completed** for ALL fields being updated
- [ ] **MCP Playwright browser access used** for direct website verification
- [ ] **Multiple sources consulted** for each field (minimum 2-3 sources)
- [ ] **Current information verified** (not historical or outdated)
- [ ] **Verification template completed** with comprehensive documentation
- [ ] **Confidence scores assigned** to all verification findings
- [ ] **Source reliability assessed** for all sources used
- [ ] **MCP tool usage documented** in verification notes

#### **5.0.2 Update Justification Validation**
- [ ] **Each change justified** with specific source evidence
- [ ] **Verification method documented** for each field
- [ ] **Source URLs/timestamps recorded** for audit trail
- [ ] **Confidence level documented** for each field
- [ ] **Alternative interpretations considered** and documented

#### **5.0.3 Quality Assurance Validation**
- [ ] **No assumptions made** without source verification
- [ ] **No existing data trusted** without re-verification
- [ ] **No updates based on inference alone** without source support
- [ ] **All critical fields verified** against primary sources
- [ ] **Service areas properly verified** using systematic process

#### **5.0.4 Status Management Validation - CRITICAL**
- [ ] **Verification completed** with all corrections applied
- [ ] **Resource moved to needs_review status** after verification
- [ ] **No resources left in published status** after verification
- [ ] **Status workflow followed**: Any status → needs_review (after verification)
- [ ] **Human review required** before moving to published status

**⚠️ IMPORTANT: After verification, ALL resources must be in "needs_review" status for human validation**

**ONLY PROCEED TO UPDATES AFTER COMPLETING ALL VALIDATION ITEMS ABOVE**

#### **5.0.4 CLI Command Validation - NEW**
- [ ] **Field names verified** (use underscores, not hyphens)
- [ ] **Command syntax checked** using `--help` if unsure
- [ ] **Service area names verified** using `list-areas` command
- [ ] **Update commands tested** with small changes first
- [ ] **JSON format validated** for bulk updates

**COMMON CLI MISTAKES TO AVOID:**
- ❌ Using hyphens instead of underscores: `--hours-of-operation` (wrong)
- ✅ Using underscores: `--hours_of_operation` (correct)
- ❌ Assuming service area names without checking `list-areas`
- ✅ Always verify exact names with `list-areas --search="[NAME]"`
- ❌ Skipping `--help` when unsure about command syntax
- ✅ Use `python manage.py resource_cli update --help` for field names

---

#### 5.1 Create Change Summary
Before making any changes, create a comprehensive summary using the Verification Session Template (Section 4.3). This template provides a standardized format for documenting all verification findings.

#### 5.2 Update Verification Date Fields
When verification is completed, update the verification tracking fields:

```bash
# Update verification date and verifier (when moving to published status)
python manage.py resource_cli update [RESOURCE_ID] --last-verified-at="$(date -u +'%Y-%m-%d %H:%M:%S')" --last-verified-by="[VERIFIER_NAME]"

# Or use JSON format for multiple fields
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "last_verified_at": "[TIMESTAMP]",
    "last_verified_by": "[VERIFIER_NAME]",
    "status": "published"
}'

# IMPORTANT: Field names for verification tracking
# --last_verified_at (not --last-verified-at)
# --last_verified_by (not --last-verified-by)
# --verification_frequency_days (not --verification-frequency-days)
```

#### 5.3 Update Resource Category (NEW)
The CLI now supports updating resource categories directly, which is essential for verification when the current category is incorrect:

```bash
# Update category by name
python manage.py resource_cli update [RESOURCE_ID] --category="Education"

# Update category by ID
python manage.py resource_cli update [RESOURCE_ID] --category="11"

# Update category along with other fields
python manage.py resource_cli update [RESOURCE_ID] --category="Mental Health" --status="needs_review"

# Update category using JSON format
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "category": "Education",
    "status": "needs_review"
}'
```

**Category Update Best Practices:**
- **Always verify the correct category** by reviewing the organization's actual services
- **Use category names** for human readability (e.g., "Education" vs "11")
- **Cross-reference with category definitions** to ensure proper classification
- **Document category changes** in verification notes with rationale
- **Common category corrections**: Housing → Education, General → Specific Service Type

#### **5.2.1 Verification Field Troubleshooting**

**Problem**: "Resource.last_verified_by must be a User instance"
**Root Cause**: The `last_verified_by` field expects a User object, not a string
**Solutions**:
1. **Omit the field**: Let the system use the current authenticated user
2. **Use existing user**: Reference an existing user in the system
3. **Document the limitation**: Note that AI assistants cannot set this field

**Recommended Approach**:
```bash
# ✅ CORRECT - Omit last_verified_by, let system handle it
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "last_verified_at": "2025-09-02T00:42:00Z",
    "status": "needs_review"
}'

# ✅ CORRECT - Use current timestamp
python manage.py resource_cli update [RESOURCE_ID] --last_verified_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# ✅ CORRECT - Update category along with other fields
python manage.py resource_cli update [RESOURCE_ID] --category="Education" --status="needs_review"

# ❌ WRONG - This will fail
python manage.py resource_cli update [RESOURCE_ID] --last_verified_by="AI Assistant"
```

**Problem**: DateTimeField received naive datetime warning
**Root Cause**: Timestamp without timezone information
**Solutions**:
1. **Use ISO 8601 format with timezone**: `2025-09-02T00:42:00Z`
2. **Let system handle current time**: Omit the field or use `$(date -u +'%Y-%m-%dT%H:%M:%SZ')`
3. **Use system timestamp**: Let Django handle the current time automatically

**Recommended Timestamp Formats**:
```bash
# ✅ CORRECT - ISO 8601 with timezone
python manage.py resource_cli update [RESOURCE_ID] --last_verified_at="2025-09-02T00:42:00Z"

# ✅ CORRECT - Current UTC time
python manage.py resource_cli update [RESOURCE_ID] --last_verified_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# ✅ CORRECT - Let system handle it
python manage.py resource_cli update [RESOURCE_ID] --status="needs_review"
# last_verified_at will be set automatically

# ❌ WRONG - Naive datetime
python manage.py resource_cli update [RESOURCE_ID] --last_verified_at="2025-09-02 00:42:00"
```

#### **5.2.2 Verification Field Best Practices**

**For AI Assistants**:
1. **Focus on content verification**: Don't worry about `last_verified_by`
2. **Use proper timestamps**: ISO 8601 format with timezone
3. **Document limitations**: Note what fields couldn't be set and why
4. **Let system handle defaults**: Omit fields that have system defaults

**For Human Verifiers**:
1. **Set both fields**: `last_verified_at` and `last_verified_by`
2. **Use proper credentials**: Ensure you're authenticated as the correct user
3. **Verify field updates**: Check that verification fields were set correctly
4. **Document any issues**: Note any problems with verification field updates

**Verification Field Checklist**:
- [ ] `last_verified_at` set to current timestamp
- [ ] `last_verified_by` set to current user (or omitted for AI)
- [ ] `verification_frequency_days` appropriate for service type
- [ ] `category` verified and corrected if incorrect (NEW)
- [ ] All verification fields properly documented in notes

**Verification Date Fields:**
- **`last_verified_at`**: Timestamp when verification was completed
- **`last_verified_by`**: Name/ID of person or AI that completed verification
- **`verification_frequency_days`**: How often re-verification is needed (default: 180 days)
- **`updated_at`**: Automatically updated when any field changes (not verification-specific)

**When to Update Verification Dates:**
- ✅ **VERIFICATION COMPLETED**: Set `last_verified_at` and `last_verified_by` when verification is finished
- ✅ **VERIFICATION IN PROGRESS**: Update `last_verified_at` when verification is finished but status remains "needs_review"
- ❌ **DRAFT RESOURCES**: Don't set verification dates until verification is actually completed
- ❌ **PARTIAL VERIFICATION**: Don't set verification dates until all required fields are verified

**⚠️ CRITICAL STATUS WORKFLOW:**
- **After verification**: ALL resources must be in "needs_review" status
- **Human validation required**: Before moving any resource to "published" status
- **Published status**: Only for resources that have been verified AND human-validated
- **Verification ≠ Publication**: Verification is a technical process, publication requires human approval

**Key Sections to Include:**
- **Session Overview**: Basic resource and verification information
- **Sources Consulted**: All sources used with reliability scores
- **Field Verification Results**: Detailed breakdown of verified vs. corrected fields
- **Quality Assessment**: Overall data accuracy and verification coverage
- **Recommendations**: Specific actions required and next steps

**Example Summary Structure:**
```markdown
## VERIFICATION CHANGES FOR [RESOURCE_NAME] (ID: [X])

### Contact Information Updates
- Phone: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]
- Email: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]

### Location Updates
- Address: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]
- City: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]

### Service Updates
- Hours: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]
- Eligibility: [OLD] → [NEW] | Source: [VERIFICATION_METHOD]

### Sources Consulted
1. [SOURCE_1]: [WHAT_VERIFIED]
2. [SOURCE_2]: [WHAT_VERIFIED]
3. [SOURCE_3]: [WHAT_VERIFIED]

### Verification Confidence
Overall confidence: [HIGH/MEDIUM/LOW]
Fields requiring re-verification: [LIST_FIELDS]
```

**Note**: For complete verification documentation, use the comprehensive template in Section 4.3. The summary above is a condensed version for quick reference during updates.

#### 5.2 Implement Changes via CLI
```bash
# Update individual fields
python manage.py resource_cli update [RESOURCE_ID] --phone="[NEW_PHONE]" --source="[VERIFICATION_SOURCE]"

# Update multiple fields
python manage.py resource_cli update [RESOURCE_ID] --json='{"phone":"[NEW_PHONE]","hours_of_operation":"[NEW_HOURS]","source":"[VERIFICATION_SOURCE]"}'

# Update status if needed
python manage.py resource_cli update [RESOURCE_ID] --status=needs_review

# Update verification notes
python manage.py resource_cli update [RESOURCE_ID] --notes="[VERIFICATION_NOTES]"
# ⚠️ IMPORTANT: See Section 4.1 for critical guidance on avoiding markdown escaping issues
```

---

### **Step 6: Quality Assurance**

#### 6.1 Verification Checklist
- [ ] All contact fields verified with primary sources using MCP tools
- [ ] Location information confirmed with mapping services
- [ ] Service details verified with official materials via MCP Playwright
- [ ] Multiple sources consulted for each field (MCP Web Search + Playwright)
- [ ] Changes documented with sources and MCP tool usage
- [ ] Resource status updated appropriately
- [ ] **Service types verified and appropriately assigned (NEW)**
- [ ] **Verification notes updated using comprehensive template (Section 4.3)**
- [ ] All changes tested and verified
- [ ] **Verification session documented with complete audit trail**
- [ ] **MCP tool usage documented** for future reference

#### 6.2 Confidence Scoring
- **HIGH (90-100%)**: Verified with official website + direct contact
- **MEDIUM (70-89%)**: Verified with official website + secondary source
- **LOW (50-69%)**: Verified with secondary sources only
- **UNVERIFIED (<50%)**: No reliable sources found

#### 6.3 Validation Testing
```bash
# Test that the updated resource passes validation
python manage.py shell -c "
from directory.models import Resource; 
r = Resource.objects.get(id=[RESOURCE_ID]); 
r.clean(); 
print('✅ Resource passes validation');
"

# Verify changes were applied correctly
python manage.py resource_cli show [RESOURCE_ID]
```

---

### **Step 7: Common Verification Scenarios**

#### 7.1 Government Organizations
- **Primary**: Official .gov website via MCP Playwright browser access
- **Secondary**: MCP Web Search for current government information
- **Tertiary**: State/local government directories
- **Verification**: Phone contact with government office
- **Special Notes**: Check for recent policy changes or service updates
- **MCP Tools**: Use Playwright for .gov website access, Web Search for current policies

#### 7.2 Non-Profit Organizations
- **Primary**: Official organization website via MCP Playwright browser access
- **Secondary**: MCP Web Search for current organization information
- **Tertiary**: IRS 990 forms, GuideStar
- **Verification**: Phone contact with staff
- **Special Notes**: Check for funding changes affecting services
- **MCP Tools**: Use Playwright for website access, Web Search for current news and updates

#### 7.3 Healthcare Providers
- **Primary**: Official website via MCP Playwright, state licensing boards
- **Secondary**: MCP Web Search for current healthcare information
- **Tertiary**: Insurance provider directories
- **Verification**: Phone contact with office
- **Special Notes**: Verify insurance acceptance and current providers
- **MCP Tools**: Use Playwright for website access, Web Search for current licensing and provider information

#### 7.4 Religious Organizations
- **Primary**: Official church/organization website via MCP Playwright
- **Secondary**: MCP Web Search for current organization information
- **Tertiary**: Denomination directories
- **Verification**: Phone contact with office
- **Special Notes**: Check for seasonal service changes
- **MCP Tools**: Use Playwright for website access, Web Search for current events and service schedules

#### 7.5 Emergency Services
- **Primary**: Official emergency protocols via MCP Playwright
- **Secondary**: MCP Web Search for current emergency information
- **Tertiary**: Government emergency directories
- **Verification**: Direct contact with emergency coordinator
- **Special Notes**: Verify 24/7 availability and response protocols
- **MCP Tools**: Use Playwright for protocol access, Web Search for current emergency procedures

---

### **Step 8: Maintenance Schedule**

#### 8.1 Verification Frequency
- **Emergency Services**: Every 3 months
- **Healthcare Services**: Every 6 months
- **General Services**: Every 12 months
- **Government Services**: Every 6 months
- **New Resources**: Within 30 days of creation

#### 8.2 Priority Indicators
- **HIGH**: Services with frequent changes, emergency services, new organizations
- **MEDIUM**: Standard services, established organizations, stable programs
- **LOW**: Stable services, well-established organizations, infrequent changes

#### 8.3 Automated Reminders
```bash
# Check resources due for verification
python manage.py shell -c "
from directory.models import Resource;
from datetime import datetime, timedelta;
from django.utils import timezone;

# Find resources verified more than 6 months ago
cutoff_date = timezone.now() - timedelta(days=180);
old_verifications = Resource.objects.filter(
    last_verified_at__lt=cutoff_date,
    status='published'
).order_by('last_verified_at');

print(f'Resources needing verification: {old_verifications.count()}');
[print(f'ID: {r.id}, Name: {r.name}, Last Verified: {r.last_verified_at}') for r in old_verifications[:10]];
"
```

#### 8.4 Verification Status Queries
Use these queries to check verification status across the database:

```bash
# Check verification date status by resource status
python manage.py shell -c "
from directory.models import Resource;
from django.utils import timezone;
from datetime import timedelta;

# Published resources never verified
never_verified = Resource.objects.filter(status='published', last_verified_at__isnull=True);
print(f'Published resources never verified: {never_verified.count()}');

# Resources due for verification (180+ days)
cutoff_180 = timezone.now() - timedelta(days=180);
due_180 = Resource.objects.filter(
    status='published', 
    last_verified_at__lt=cutoff_180
);
print(f'Resources due for verification (180+ days): {due_180.count()}');

# Resources due soon (90+ days)
cutoff_90 = timezone.now() - timedelta(days=90);
due_90 = Resource.objects.filter(
    status='published', 
    last_verified_at__lt=cutoff_90
);
print(f'Resources due soon (90+ days): {due_90.count()}');
"

# Check specific verification fields
python manage.py shell -c "
from directory.models import Resource;

# Resources with verification dates
verified = Resource.objects.filter(last_verified_at__isnull=False);
print(f'Resources with verification dates: {verified.count()}');

# Resources without verification dates
unverified = Resource.objects.filter(last_verified_at__isnull=True);
print(f'Resources without verification dates: {unverified.count()}');

# Check verification frequency distribution
frequencies = Resource.objects.values_list('verification_frequency_days', flat=True).distinct();
print(f'Verification frequencies used: {list(frequencies)}');
"

#### 8.5 Nationwide Service Maintenance
**🚨 CRITICAL**: Regularly audit and update nationwide services to ensure proper coverage area assignment:

```bash
# Find nationwide services that need coverage area updates
python manage.py shell -c "
from directory.models import Resource;
nationwide_keywords = ['nationwide', 'national', 'all states', 'united states', 'usa'];
nationwide_resources = Resource.objects.filter(
    description__icontains='nationwide'
).union(
    Resource.objects.filter(description__icontains='national')
).union(
    Resource.objects.filter(description__icontains='all states')
).union(
    Resource.objects.filter(description__icontains='united states')
);
print(f'Potential nationwide services found: {nationwide_resources.count()}');
[nprint(f'ID: {r.id}, Name: {r.name}, Status: {r.status}') for r in nationwide_resources[:10]];
"

# Check resources without any coverage areas (may be nationwide)
python manage.py shell -c "
from directory.models import Resource;
no_coverage = Resource.objects.filter(coverage_areas__isnull=True);
print(f'Resources without coverage areas: {no_coverage.count()}');
[nprint(f'ID: {r.id}, Name: {r.name}, Description: {r.description[:100]}...') for r in no_coverage[:10]];
"

# Update nationwide services with proper coverage areas
python manage.py resource_cli update [RESOURCE_ID] --add-areas=\"United States (All States and Territories)\"
```

**Nationwide Service Audit Checklist:**
- [ ] **Identify nationwide services** using description keywords and manual review
- [ ] **Verify nationwide scope** by checking official websites and materials
- [ ] **Assign nationwide coverage area** "United States (All States and Territories)"
- [ ] **Remove inappropriate local areas** that limit nationwide discoverability
- [ ] **Test discoverability** by searching from different geographic locations
- [ ] **Document changes** in verification notes with rationale
```

---

## 🛠️ CLI Commands for Verification Workflow

### **Quick Reference - Common Verification Operations**

#### **Essential Commands for Every Verification Session**
```bash
# 1. Find resource to verify
python manage.py resource_cli list --limit=5

# 2. Get resource details
python manage.py resource_cli show [RESOURCE_ID]

# 3. Check available service areas
python manage.py resource_cli list-areas --search="[AREA_NAME]"

# 4. Update resource with verification results
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "status": "needs_review",
    "last_verified_at": "2025-09-02T00:42:00Z"
}'

# 5. Add service areas
python manage.py resource_cli update [RESOURCE_ID] --add-areas="[AREA_1],[AREA_2]"

# 6. Update category if incorrect (NEW)
python manage.py resource_cli update [RESOURCE_ID] --category="Education"

# 7. Verify final state
python manage.py resource_cli show [RESOURCE_ID]
```

#### **Service Area Management Quick Reference**
```bash
# Check what areas exist
python manage.py resource_cli list-areas --search="Kentucky"

# ✅ RECOMMENDED: Add areas by ID (avoids duplicate name issues)
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"

# Add single area by name
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky"

# Add multiple areas by name (beware duplicates)
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky,West Virginia"

# Replace all areas
python manage.py resource_cli update [RESOURCE_ID] --set-areas="Kentucky,West Virginia"

# Clear all areas
python manage.py resource_cli update [RESOURCE_ID] --clear-areas

# Check current areas
python manage.py resource_cli show [RESOURCE_ID]
```

**✅ NEW: Area ID Method - Best Practice**
```bash
# Find area IDs first
python manage.py resource_cli list-areas --search="Tennessee"

# Use IDs for precise control
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476,35499"

# Mix IDs and names
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476,Kentucky,West Virginia"
```

#### **Verification Field Quick Reference**
```bash
# Set verification timestamp (AI-friendly)
python manage.py resource_cli update [RESOURCE_ID] --last_verified_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Update status to needs_review
python manage.py resource_cli update [RESOURCE_ID] --status=needs_review

# Update verification notes
python manage.py resource_cli update [RESOURCE_ID] --notes="[VERIFICATION_NOTES]"

# Bulk update with JSON
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "status": "needs_review",
    "last_verified_at": "2025-09-02T00:42:00Z",
    "notes": "Verification completed..."
}'
# ⚠️ WARNING: JSON format can cause markdown escaping issues - see Section 4.1 for guidance
```

### Resource Discovery
```bash
# Find resources needing verification
python manage.py resource_cli list --status=needs_review

# Find resources by verification date
python manage.py resource_cli list --limit=50

# Search for specific service types
python manage.py resource_cli search "mental health" --status=published
```

### Data Extraction
```bash
# Get complete resource details
python manage.py resource_cli show [RESOURCE_ID]

# Export resource data for analysis
python manage.py resource_cli show [RESOURCE_ID] --format=json
```

### Updates and Modifications
```bash
# Update verification status
python manage.py resource_cli update [RESOURCE_ID] --status=published

# Update verification source
python manage.py resource_cli update [RESOURCE_ID] --source="Verified via official website and phone contact on [DATE]"

# Update verification notes (use comprehensive template from Section 4.3)
python manage.py resource_cli update [RESOURCE_ID] --notes="[VERIFICATION_NOTES]"
# ⚠️ IMPORTANT: See Section 4.1 for critical guidance on avoiding markdown escaping issues

# NEW: Update resource category
python manage.py resource_cli update [RESOURCE_ID] --category="Education"
python manage.py resource_cli update [RESOURCE_ID] --category="Mental Health"

# Bulk update multiple fields
python manage.py resource_cli update [RESOURCE_ID] --json='{
    "phone": "[NEW_PHONE]",
    "hours_of_operation": "[NEW_HOURS]",
    "source": "[VERIFICATION_SOURCE]",
    "notes": "[VERIFICATION_NOTES]",
    "category": "Education"
}'
# ⚠️ WARNING: JSON format can cause markdown escaping issues - see Section 4.1 for guidance
```

### Service Area Management
```bash
# List available service areas
python manage.py resource_cli list-areas

# Search for specific service areas
python manage.py resource_cli list-areas --search="Kentucky"
python manage.py resource_cli list-areas --search="Whitley"

# Add service areas to resource
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky,Whitley County"

# Remove service areas from resource
python manage.py resource_cli update [RESOURCE_ID] --remove-areas="Whitley County"

# Replace all service areas
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky" --remove-areas="Whitley County"

# Verify service area assignment
python manage.py resource_cli show [RESOURCE_ID]
# Look for "coverage_areas" section in output

# TROUBLESHOOTING: If service area not found
# 1. Check exact spelling: python manage.py resource_cli list-areas --search="[EXACT_NAME]"
# 2. Look for state context in results (state_fips field)
# 3. Use exact name as it appears in list-areas output
# 4. Common issue: "Fayette County" vs "Fayette County, KY" - use exact match
```

#### **🚨 Nationwide Service Area Management**
```bash
# Find nationwide coverage area
python manage.py resource_cli list-areas --search="United States"

# Add nationwide coverage to any resource
python manage.py resource_cli update [RESOURCE_ID] --add-areas="United States (All States and Territories)"

# Remove local areas and add nationwide coverage
python manage.py resource_cli update [RESOURCE_ID] --remove-areas="Kentucky" --add-areas="United States (All States and Territories)"

# Verify nationwide coverage assignment
python manage.py resource_cli show [RESOURCE_ID]
# Should show "United States (All States and Territories)" in coverage_areas
```

**Nationwide Coverage Area Details:**
- **Name**: "United States (All States and Territories)"
- **ID**: 43273
- **Type**: POLYGON
- **Purpose**: Represents services available nationwide

**Important**: When updating verification notes, use the comprehensive template provided in Section 4.3 to ensure consistent documentation and complete audit trails.

---

### Service Type Management
```bash
# List available service types
python manage.py resource_cli list-services

# Search for specific service types
python manage.py resource_cli list-services --search="Education"
python manage.py resource_cli list-services --search="Mental Health"

# Add service types to resource
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Education,Child Care"

# Remove service types from resource
python manage.py resource_cli update [RESOURCE_ID] --remove-service-types="Child Care"

# Replace all service types
python manage.py resource_cli update [RESOURCE_ID] --set-service-types="Education,Health Education"

# Clear all service types
python manage.py resource_cli update [RESOURCE_ID] --clear-service-types

# Verify service type assignment
python manage.py resource_cli show [RESOURCE_ID]
# Look for "service_types" section in output
```

---

## 🆕 **NEW: Area ID Management System**

### **Overview**
The CLI now supports adding service areas by their numeric ID, providing precise control over geographic area assignment and eliminating issues with duplicate area names.

### **Benefits of Area ID Method**
- **✅ Precise Control**: Target exact geographic areas (STATE vs CITY vs COUNTY)
- **✅ Avoid Duplicates**: Bypass issues with multiple areas having the same name
- **✅ Reliable Assignment**: Guaranteed to add the specific area you want
- **✅ Audit Trail**: Clear record of which exact areas were assigned
- **✅ Mixed Usage**: Can combine IDs and names in the same command

### **How to Use Area IDs**

#### **Step 1: Find the Area ID**
```bash
# Search for the area you want
python manage.py resource_cli list-areas --search="Tennessee"

# Look for the specific area type and state in results
# Example: Tennessee (STATE) vs Tennessee (CITY)
```

#### **Step 2: Use the ID to Add the Area**
```bash
# Add single area by ID
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476"

# Add multiple areas by ID
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"

# Mix IDs and names
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476,Kentucky,West Virginia"
```

### **Common Area IDs for Appalachian Region**
```bash
# Kentucky (STATE) - ID: 35480
# Tennessee (STATE) - ID: 35476  
# Virginia (STATE) - ID: 35499
# West Virginia (STATE) - ID: 35447

# Example: Add all four Appalachian states
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"
```

### **When to Use Area IDs vs Names**

#### **Use Area IDs When**:
- ✅ Multiple areas have the same name (e.g., "Tennessee")
- ✅ You need to target a specific area type (STATE vs CITY vs COUNTY)
- ✅ You want precise control over area assignment
- ✅ You're working with areas that commonly have duplicates

#### **Use Names When**:
- ✅ Area names are unique in the system
- ✅ You're working with well-known, unambiguous areas
- ✅ You want human-readable commands
- ✅ You're doing quick, simple area assignments

### **Troubleshooting Area ID Issues**

#### **Common Problems and Solutions**
```bash
# Problem: "Invalid service areas ignored: [ID]"
# Solution: Verify the ID exists
python manage.py resource_cli list-areas --search="[AREA_NAME]"

# Problem: Wrong area type assigned
# Solution: Check the area details before using ID
python manage.py resource_cli list-areas --search="[AREA_NAME]"
# Look for "kind": "STATE" vs "kind": "CITY"

# Problem: Area not found by ID
# Solution: Use list-areas to find current IDs
python manage.py resource_cli list-areas --search="[AREA_NAME]"
```

### **Best Practices for Area ID Usage**

1. **Always verify IDs first**: Use `list-areas --search` to find the correct ID
2. **Document ID usage**: Include area IDs in verification notes for future reference
3. **Use consistent patterns**: Stick to either all IDs or all names when possible
4. **Test assignments**: Verify area assignments using `show` command after updates
5. **Keep ID reference**: Maintain a list of commonly used area IDs for your region

### **Example Workflow with Area IDs**

```bash
# 1. Find the areas you need
python manage.py resource_cli list-areas --search="Tennessee"
python manage.py resource_cli list-areas --search="Virginia"

# 2. Note the IDs for STATE areas (not CITY areas)
# Tennessee (STATE): 35476
# Virginia (STATE): 35499

# 3. Add the areas using IDs
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35476,35499"

# 4. Verify the assignment
python manage.py resource_cli show [RESOURCE_ID]

# 5. Document in verification notes
# "Added Tennessee (STATE) and Virginia (STATE) using area IDs 35476 and 35499"
```

---

## 🆕 **NEW: Service Type Management System**

### **Overview**
The CLI now supports managing service types for resources, allowing you to specify what specific services each resource provides. This enhances resource discoverability and helps users find resources that offer the exact services they need.

### **Available Service Type Commands**
```bash
# List ALL available service types (RECOMMENDED)
python manage.py resource_cli list-services

# Show details for a specific service type
python manage.py resource_cli show-service [SERVICE_ID]

# Create a new service type
python manage.py resource_cli create-service --json='{"name":"New Service","description":"Service description"}'

# Update an existing service type
python manage.py resource_cli update-service [SERVICE_ID] --description="Updated description"
```

**⚠️ IMPORTANT: Service Type Selection Strategy**
- **✅ RECOMMENDED**: List ALL services first to see complete picture
- **❌ AVOID**: Targeted searches that may miss relevant services
- **Rationale**: Limited number of services available, better to see full scope
- **Process**: Review all services, then select 2-4 most appropriate ones

### **Managing Service Types on Resources**

#### **Adding Service Types to Resources**
```bash
# Add single service type
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Education"

# Add multiple service types
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Education,Child Care,Health Education"

# Add service types by ID
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="9,10,29"
```

#### **Removing Service Types from Resources**
```bash
# Remove specific service type
python manage.py resource_cli update [RESOURCE_ID] --remove-service-types="Child Care"

# Remove multiple service types
python manage.py resource_cli update [RESOURCE_ID] --remove-service-types="Education,Child Care"
```

#### **Replacing All Service Types**
```bash
# Replace all service types with new ones
python manage.py resource_cli update [RESOURCE_ID] --set-service-types="Education,Health Education"

# Clear all service types
python manage.py resource_cli update [RESOURCE_ID] --clear-service-types
```

### **Common Service Types for Different Resource Categories**

#### **Education Resources**
- **Education** (ID: 9) - Educational programs and support
- **Child Care** (ID: 10) - Child care and family support services
- **Health Education** (ID: 29) - Health education services

#### **Mental Health Resources**
- **Mental Health Counseling** (ID: 20) - Mental health and counseling services
- **Mental Health Support** (ID: 30) - Mental health support services
- **Counseling** (ID: 2) - Mental health and addiction counseling services

#### **Healthcare Resources**
- **Healthcare** (ID: 6) - Medical and healthcare services
- **Medical Care** (ID: 22) - Healthcare and medical services
- **Health** (ID: 31) - General health services

#### **Emergency Services**
- **Emergency Services** (ID: 14) - Emergency and crisis intervention services
- **Emergency Shelter** (ID: 18) - Emergency and temporary housing
- **24/7 emergency shelter** (ID: 33) - 24/7 emergency shelter services

### **Service Type Assignment Best Practices**

1. **List ALL services first**: Use `python manage.py resource_cli list-services` to see complete scope
2. **Choose relevant service types**: Select services that accurately describe what the resource provides
3. **Use multiple service types**: Most resources provide multiple services, so assign 2-4 relevant types
4. **Verify service type names**: Use exact names as they appear in `list-services` output
5. **Consider user needs**: Think about what services users would search for when looking for this resource
6. **Document assignments**: Include service type assignments in verification notes

**🚨 CRITICAL: Avoid targeted searches for service types**
- **Why**: Limited number of services available (typically 30-50 total)
- **Better approach**: Review all services to understand full scope
- **Result**: More accurate service type assignments and better discoverability

### **Example Service Type Assignment**

```bash
# For a mental health resource that provides counseling and support
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Mental Health Counseling,Mental Health Support,Counseling"

# For an educational resource focused on children
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Education,Child Care,Health Education"

# For an emergency shelter resource
python manage.py resource_cli update [RESOURCE_ID] --add-service-types="Emergency Shelter,24/7 emergency shelter"
```

### **Verifying Service Type Assignment**

```bash
# Check current service types
python manage.py resource_cli show [RESOURCE_ID]

# Look for "service_types" section in output
# Should show all assigned service types with IDs and descriptions
```

### **Troubleshooting Service Type Issues**

#### **Common Problems and Solutions**
```bash
# Problem: "Service type not found"
# Solution: Check exact spelling with list-services
python manage.py resource_cli list-services --search="[SERVICE_NAME]"

# Problem: Multiple service types with similar names
# Solution: Use the exact name from list-services output
python manage.py resource_cli list-services --search="[PARTIAL_NAME]"

# Problem: Service types not appearing after assignment
# Solution: Verify assignment with show command
python manage.py resource_cli show [RESOURCE_ID]
```

---

## 🤖 AI-Assisted Verification Guidelines

### **MCP Tool Usage Best Practices**

#### **🚨 CRITICAL: Always Use MCP Tools for Verification**
**Preferred Tools (in order of preference):**
1. **MCP Web Search**: For current web search results and information gathering
2. **MCP Playwright Browser**: For direct website access, JavaScript rendering, and content extraction
3. **MCP Sequential Thinking**: For complex verification planning and analysis

**❌ NEVER Use These Basic Tools When MCP Tools Are Available:**
- `curl` or `wget` commands
- Basic HTML parsing with `grep`
- Manual web scraping with command-line tools
- Simple text-based content extraction

**✅ ALWAYS Use MCP Tools Because:**
- **Professional Grade**: Designed specifically for web automation and verification
- **JavaScript Support**: Full rendering of modern websites
- **Structured Access**: Better content extraction and analysis
- **Real-time Results**: Current information from live sources
- **Audit Trail**: Better documentation of verification sources

### **AI Verification CRITICAL REQUIREMENTS**

### **MCP Tool Usage Requirements**
**⚠️ CRITICAL: Use MCP Tools for Verification**
- **MCP Web Search**: Use for current web search results and information gathering
- **MCP Playwright Browser**: Use for direct website access, JavaScript rendering, and content extraction
- **Avoid Basic Tools**: Don't use curl, wget, or basic HTML parsing when MCP tools are available
- **Professional Verification**: MCP tools provide professional-grade verification capabilities

### **NEW: Test Resource Verification Guidelines**

#### **Test Resource vs. Real Resource Verification**
**Test Resources** (like the one we just worked with):
- **Purpose**: Training, demonstration, testing CLI functionality
- **Verification Focus**: Data quality, completeness, realistic examples
- **Source Requirements**: No external source verification needed
- **Documentation**: Clear identification as test resource
- **Status**: Usually kept as "needs_review" or "draft"

**Real Resources**:
- **Purpose**: Actual community services for public use
- **Verification Focus**: Source accuracy, current information, contact validation
- **Source Requirements**: Multiple source verification mandatory
- **Documentation**: Comprehensive source documentation required
- **Status**: Progress through workflow to "published"

#### **Test Resource Verification Process**
1. **Identify Resource Type**: Determine if test or real resource
2. **Data Quality Assessment**: Check for realistic, complete information
3. **Field Completeness**: Ensure all appropriate fields are populated
4. **Realistic Examples**: Use real locations, realistic contact formats
5. **Clear Documentation**: Mark as test resource in notes and source
6. **Training Value**: Ensure resource demonstrates proper data structure

#### **When Working with Test Resources**
- ✅ **Appropriate**: Creating realistic examples, demonstrating CLI usage
- ✅ **Appropriate**: Using real geographic data (cities, counties, states)
- ✅ **Appropriate**: Following proper field naming conventions
- ❌ **Inappropriate**: Attempting external source verification
- ❌ **Inappropriate**: Publishing test resources to public database
- ❌ **Inappropriate**: Using completely fictional data (use realistic examples)

**🚨 MANDATORY FOR AI ASSISTANTS:**
- **NEVER skip web searches** - every verification session requires fresh searches using MCP Web Search
- **NEVER trust existing notes** - always verify current information
- **NEVER make assumptions** - every field must have source evidence
- **ALWAYS use MCP Playwright** - for direct website access and content extraction
- **ALWAYS document sources** - URLs, timestamps, and reliability scores
- **ALWAYS use multiple sources** - minimum 2-3 sources per field
- **ALWAYS use MCP tools** - prefer MCP Web Search and Playwright over basic command-line tools

**⚠️ AI VERIFICATION IS NOT DATA ENTRY - IT IS FACT-CHECKING**

#### **MCP Tool Documentation Requirements**
**Every verification session must document:**
- **MCP Web Search Queries**: What search terms were used and what results were found
- **MCP Playwright URLs**: Which websites were accessed and what content was extracted
- **Tool Selection Rationale**: Why MCP tools were chosen over basic alternatives
- **Verification Coverage**: How MCP tools provided comprehensive verification
- **Source Reliability**: How MCP tools enhanced source verification quality

---

### **AI Verification Capabilities**
AI tools can significantly enhance the verification process by:

#### **Strengths**
- **MCP Web Search Integration**: Access current web search results for real-time information
- **MCP Playwright Browser Automation**: Direct website access with full JavaScript rendering and content extraction
- **Content Analysis**: Systematically extract information from rendered web pages
- **Pattern Recognition**: Identify logical connections and infer missing information
- **Geographic Lookup**: Access mapping services and address validation tools
- **Multi-Source Cross-Reference**: Compare information across multiple platforms
- **Consistent Documentation**: Generate standardized verification reports

#### **Limitations**
- **Cannot Make Phone Calls**: Cannot verify phone numbers through direct calling
- **Limited Human Judgment**: May miss nuanced context or cultural considerations
- **No Physical Verification**: Cannot visit locations or verify physical presence
- **Limited Access to Private Systems**: Cannot access internal databases or systems

### **AI Verification Best Practices**

#### **1. Source Prioritization**
- **Primary Sources First**: Always start with official websites and verified social media
- **Use MCP Tools**: Leverage MCP Web Search and Playwright browser tools for comprehensive verification
- **Avoid Basic Command-Line Tools**: Don't use curl, wget, or basic HTML parsing when MCP tools are available
- **Cross-Reference Multiple Sources**: Use at least 2-3 sources for each field
- **Verify Source Authenticity**: Ensure sources are official and current

#### **2. Inference Guidelines**
- **Use Explicit Evidence**: Base inferences on clear statements, not assumptions
- **Document Inference Basis**: Always note why inference was used
- **Confidence Scoring**: Assign appropriate confidence levels to inferred information
- **Alternative Interpretations**: Consider other possible meanings

#### **3. Content Analysis Techniques**
- **Systematic Reading**: Read through all available content systematically
- **Keyword Search**: Look for specific terms related to each field
- **Context Analysis**: Consider surrounding context when interpreting information
- **Pattern Recognition**: Identify standard practices and common formats

#### **4. Quality Assurance**
- **Human Review**: Have human verifiers review AI-generated reports
- **Source Documentation**: Document all sources used for verification
- **Confidence Assessment**: Be honest about confidence levels
- **Limitation Disclosure**: Clearly state what could not be verified

### **AI Verification Workflow**

#### **Phase 1: Initial Data Collection**
1. **MCP Web Search**: Start with current web search results for the organization
2. **MCP Playwright Browser Access**: Navigate directly to official websites for comprehensive verification
3. **Website Analysis**: Access and analyze official website content with full JavaScript rendering
4. **Social Media Review**: Check verified social media accounts
5. **Content Extraction**: Systematically extract relevant information from rendered pages
6. **Source Documentation**: Document all sources consulted with URLs and timestamps

#### **Phase 2: Inference and Analysis**
1. **Logical Analysis**: Identify information that can be logically inferred
2. **Pattern Recognition**: Apply standard practices and common patterns
3. **Cross-Reference**: Compare information across multiple sources
4. **Confidence Scoring**: Assign confidence levels to all findings

#### **Phase 3: Documentation and Reporting**
1. **Comprehensive Report**: Generate detailed verification report
2. **Source Attribution**: Document all sources and inference methods
3. **Confidence Assessment**: Provide clear confidence levels
4. **Limitation Disclosure**: State what could not be verified

### **AI Verification Success Metrics**

#### **Coverage Metrics**
- **Field Verification Rate**: Target 95%+ fields verified (direct + inference)
- **Source Diversity**: Minimum 2 sources per field
- **MCP Tool Usage**: Prioritize MCP Web Search and Playwright tools over basic command-line tools
- **Inference Usage**: Track percentage of fields verified through inference

#### **Quality Metrics**
- **Accuracy Rate**: Measure against human verification results
- **Confidence Distribution**: Target 80%+ fields with HIGH confidence
- **Source Reliability**: Prioritize primary source usage

#### **Efficiency Metrics**
- **Verification Time**: Target 15-30 minutes per resource
- **Source Utilization**: Maximize primary source usage
- **Documentation Completeness**: 100% of verifications documented

### **Human-AI Collaboration**

#### **AI Role**
- **Data Collection**: Gather information from multiple sources using MCP Web Search and Playwright tools
- **Content Analysis**: Extract and organize relevant information from rendered web pages
- **Inference Generation**: Identify logical connections and patterns
- **Report Generation**: Create comprehensive verification reports

#### **Human Role**
- **Quality Review**: Review AI-generated reports for accuracy
- **Context Interpretation**: Provide cultural and contextual insights
- **Phone Verification**: Make direct contact when needed
- **Final Validation**: Approve verification results and recommendations

#### **Collaboration Workflow**
1. **AI Initial Verification**: Complete comprehensive verification using MCP Web Search and Playwright tools
2. **Human Review**: Human verifier reviews AI report and findings
3. **Human Verification**: Human verifier completes any tasks AI cannot do (phone calls, physical visits)
4. **Joint Assessment**: AI and human collaborate on final recommendations
5. **Documentation**: Both parties contribute to final verification report

---

## 🚨 Common Issues and Solutions

### Authentication Errors
- **Problem**: "Authentication required for write operations"
- **Solution**: Ensure you're running the command in an authenticated environment

### Resource Not Found
- **Problem**: "Resource with ID [X] not found"
- **Solution**: Verify the resource ID exists using `python manage.py resource_cli list`

### Field Name Errors
- **Problem**: "unrecognized arguments: --hours-of-operation"
- **Solution**: Use underscores, not hyphens: `--hours_of_operation`
- **Prevention**: Always check field names with `python manage.py resource_cli update --help`

### Service Area Assignment Issues
- **Problem**: "Invalid service areas ignored: [AREA_NAME]"
- **Solution**: 
  1. Check exact spelling: `python manage.py resource_cli list-areas --search="[EXACT_NAME]"`
  2. Look for state context in results (state_fips field)
  3. Use exact name as it appears in list-areas output
  4. Common issue: "Fayette County" vs "Fayette County, KY" - use exact match

### Command Syntax Confusion
- **Problem**: Incorrect field names or command structure
- **Solution**: 
  1. Use `--help` for any command you're unsure about
  2. Check field names in help output
  3. Test with small changes first
  4. Use JSON format for complex updates

### Invalid Status Transitions
- **Problem**: Cannot update status from `draft` to `published`
- **Solution**: Use intermediate status: `draft` → `needs_review` → `published`

### Service Area Issues
- **Problem**: "Service area 'Unknown Area' not found"
- **Solution**: Use `python manage.py resource_cli list-areas` to see available areas

### **🚨 Advanced Service Area Troubleshooting**

#### **Duplicate Area Names Issue**
**Problem**: Multiple geographic areas have the same name (e.g., "Tennessee")
**Symptoms**: 
- "Invalid service areas ignored: [AREA_NAME]"
- "No valid service areas found in: [AREA_NAME]"
- Areas appear to add but then disappear

**Root Cause**: The system contains multiple areas with identical names but different:
- Geographic types (STATE vs COUNTY vs CITY)
- State contexts (different state_fips codes)
- Geographic boundaries

**Diagnosis Steps**:
```bash
# 1. Search for the problematic area
python manage.py resource_cli list-areas --search="Tennessee"

# 2. Look for multiple results with same name
# 3. Check state_fips codes to identify different areas
# 4. Note the area IDs for the correct areas
```

**Example Output Analysis**:
```json
{
  "id": 35476,
  "name": "Tennessee",
  "kind": "STATE",
  "state_fips": "47"  // This is Tennessee state
},
{
  "id": 38108,
  "name": "Tennessee", 
  "kind": "CITY",
  "state_fips": "17"  // This is a city in Illinois
}
```

**Solutions**:
1. **✅ RECOMMENDED: Use area IDs** for precise control and to avoid duplicates
2. **Add areas individually** to identify which ones fail
3. **Check state context** to ensure correct area selection
4. **Work with system limitations** and document the issue

**✅ NEW: Area ID Solution (Recommended)**:
```bash
# Use specific area IDs to avoid duplicate name issues
python manage.py resource_cli update [RESOURCE_ID] --add-areas="35480,35476,35499,35447"

# This adds:
# - Kentucky (STATE) - ID: 35480
# - Tennessee (STATE) - ID: 35476  
# - Virginia (STATE) - ID: 35499
# - West Virginia (STATE) - ID: 35447
```

**Previous Workaround (Still Works)**:
```bash
# Add areas one at a time to identify conflicts
python manage.py resource_cli update [RESOURCE_ID] --add-areas="Kentucky"
python manage.py resource_cli update [RESOURCE_ID] --add-areas="West Virginia"

# If Tennessee fails, document the limitation
# Current coverage: Kentucky + West Virginia
# Note: Tennessee and Virginia could not be added due to duplicate names
```

#### **Service Area Assignment Best Practices**

**Before Assignment**:
```bash
# Always check available areas first
python manage.py resource_cli list-areas --search="[AREA_NAME]"

# Look for:
# - Exact name matches
# - Multiple results with same name
# - State context (state_fips)
# - Area type (STATE, COUNTY, CITY)
```

**During Assignment**:
```bash
# Start with individual additions
python manage.py resource_cli update [RESOURCE_ID] --add-areas="[AREA_1]"
python manage.py resource_cli update [RESOURCE_ID] --add-areas="[AREA_2]"

# Use set-areas for bulk replacement
python manage.py resource_cli update [RESOURCE_ID] --set-areas="[AREA_1],[AREA_2]"

# Clear and re-add if needed
python manage.py resource_cli update [RESOURCE_ID] --clear-areas
python manage.py resource_cli update [RESOURCE_ID] --add-areas="[AREA_1],[AREA_2]"
```

**After Assignment**:
```bash
# Verify assignment worked
python manage.py resource_cli show [RESOURCE_ID]

# Look for "coverage_areas" section
# Should show all assigned areas with IDs and types
```

#### **Common Service Area Patterns**

| Service Type | Typical Service Areas | Assignment Strategy |
|--------------|----------------------|---------------------|
| **Local Services** | Single county/city | Add specific area directly |
| **Regional Services** | Multiple counties | Add areas one by one |
| **State Services** | State level | Use state area (e.g., "Kentucky") |
| **Multi-state Services** | Multiple states | Add states individually, handle duplicates |
| **Nationwide Services** | "United States (All States and Territories)" | Use nationwide coverage area |

#### **When to Escalate Service Area Issues**

**Escalate if**:
- Multiple areas with same name cannot be resolved
- System consistently fails to add valid areas
- Error messages are unclear or unhelpful
- Service area limitations significantly impact resource discoverability

**Documentation Requirements**:
- Document which areas could not be added
- Note the specific error messages
- Explain the impact on resource discoverability
- Suggest workarounds for users

### JSON Parsing Errors
- **Problem**: "Invalid JSON input"
- **Solution**: Validate JSON syntax and ensure proper escaping of quotes

---

## ⚠️ Common Verification Mistakes and Reminders

### **Critical Fields Often Overlooked**
1. **Service Areas**: 
   - **MISTAKE**: Assuming service areas = physical location
   - **REMEDY**: Always verify where services are actually offered
   - **CHECK**: Look for geographic restrictions, transportation info, partnerships

2. **Description Field**:
   - **MISTAKE**: Not verifying target populations (men vs. women vs. all)
   - **REMEDY**: Carefully compare description with official materials
   - **CHECK**: Mission statements, program descriptions, eligibility criteria

3. **Eligibility Requirements**:
   - **MISTAKE**: Leaving empty when information is available
   - **REMEDY**: Use inference from program descriptions when appropriate
   - **CHECK**: Program focus, target demographics, service restrictions

4. **Resource Category** (NEW):
   - **MISTAKE**: Not verifying if current category matches actual services
   - **REMEDY**: Always review organization's services and compare with category definitions
   - **CHECK**: Service descriptions, program focus, mission statements, category definitions

### **Verification Process Reminders**
- **ALWAYS check service areas** - they determine resource discoverability
- **NEVER assume current data is correct** - verify every field systematically
- **ALWAYS document inference usage** - explain why logical deduction was used
- **NEVER skip geographic fields** - county, postal code, and service areas are critical
- **ALWAYS verify target populations** - this affects who can access services
- **ALWAYS verify resource category** - incorrect categories limit discoverability and user access

### **Quality Control Checklist**
- [ ] Service areas verified and appropriate for service type
- [ ] Service areas added to resource using CLI commands
- [ ] **Service types verified and appropriately assigned (NEW)**
- [ ] Description matches official materials exactly
- [ ] All geographic fields (county, postal code) populated
- [ ] **Resource category verified and corrected if incorrect (NEW)**
- [ ] Inference-based verification documented with confidence levels
- [ ] Service area scope matches organization's stated service model
- [ ] Service area assignment verified using `show` command
- [ ] **Service type assignment verified using `show` command (NEW)**
- [ ] Verification date fields updated when verification completed
- [ ] `last_verified_at` set to current timestamp
- [ ] `last_verified_by` set to verifier name/ID
- [ ] `verification_frequency_days` appropriate for service type

---

## 🔍 Best Practices

### For Data Entry
1. **Start with Draft Status**: Create resources as drafts first
2. **Use Interactive Mode**: Use interactive creation for new resources
3. **Validate Service Areas**: Check available areas before assignment
4. **Complete Required Fields**: Ensure name and category are provided

### For CLI Commands
1. **Always Use Help**: `--help` for any command you're unsure about
2. **Field Name Convention**: Use underscores, not hyphens
3. **Test Small Changes**: Make small updates before large ones
4. **Verify Service Areas**: Use `list-areas` to check exact names
5. **Verify Service Types**: Use `list-services` to check exact names (NEW)
6. **Use JSON for Bulk**: Complex updates are easier with JSON format

### For Verification
1. **Check Current Status**: Use `show` command to see current state
2. **Follow Status Workflow**: Respect the draft → needs_review → published flow
3. **Use MCP Tools**: Always use MCP Web Search and Playwright for verification
4. **Use JSON for Bulk Updates**: Use JSON input for multiple field changes
5. **Maintain Audit Trail**: Updates are automatically tracked
6. **Document All Sources**: Keep detailed records of verification methods and MCP tool usage
7. **Verify Multiple Sources**: Don't rely on single source verification
8. **Document MCP Usage**: Record which MCP tools were used for each verification step

### For Search and Discovery
1. **Use Specific Terms**: Be specific in search queries
2. **Combine Filters**: Use multiple filters for precise results
3. **Check Pagination**: Use limit/offset for large result sets
4. **Verify Results**: Use `show` command to verify resource details

---

## 📚 Related Documentation

- **CLI Documentation**: `docs/CLI_Documentation.md`
- **Models**: `directory/models/core/resource.py`
- **API Views**: `directory/views/api/resource_views.py`
- **CLI Utilities**: `directory/management/commands/cli_utils.py`
- **Project README**: `README.md`
- **Verification Templates**: `docs/verification/verification_template.md`

---

## 🆘 Getting Help

### Command Help
```bash
python manage.py resource_cli --help
python manage.py resource_cli <command> --help
```

### **NEW: Common Stumbling Points & Solutions**

#### **1. Field Name Confusion**
**Problem**: Using hyphens instead of underscores
```bash
# ❌ WRONG - Will cause "unrecognized arguments" error
python manage.py resource_cli update 123 --hours-of-operation="9 AM - 5 PM"

# ✅ CORRECT - Use underscores
python manage.py resource_cli update 123 --hours_of_operation="9 AM - 5 PM"
```

**Solution**: Always check field names with `--help` command

#### **2. Service Area Assignment Issues**
**Problem**: Service area names not found
```bash
# ❌ WRONG - May fail if exact name doesn't match
python manage.py resource_cli update 123 --add-areas="Fayette County"

# ✅ CORRECT - Check exact names first
python manage.py resource_cli list-areas --search="Fayette"
python manage.py resource_cli update 123 --add-areas="Fayette County"
```

**Solution**: Always verify exact names with `list-areas --search`

#### **3. Command Syntax Uncertainty**
**Problem**: Unsure about command structure
```bash
# ❌ WRONG - Guessing command syntax
python manage.py resource_cli update 123 --unknown-field="value"

# ✅ CORRECT - Check help when unsure
python manage.py resource_cli update --help
```

**Solution**: Use `--help` for any command you're not 100% sure about

#### **4. Bulk Update Complexity**
**Problem**: Updating many fields individually
```bash
# ❌ WRONG - Multiple individual commands
python manage.py resource_cli update 123 --name="New Name"
python manage.py resource_cli update 123 --phone="555-1234"
python manage.py resource_cli update 123 --email="test@example.com"

# ✅ CORRECT - Single JSON update
python manage.py resource_cli update 123 --json='{
    "name": "New Name",
    "phone": "555-1234",
    "email": "test@example.com"
}'
```

**Solution**: Use JSON format for multiple field updates

#### **5. Service Area Duplication Issues**
**Problem**: Multiple areas with same name (e.g., "Tennessee")
```bash
# ❌ WRONG - May fail due to duplicate names
python manage.py resource_cli update 123 --add-areas="Tennessee,Virginia"

# ✅ CORRECT - Check for duplicates first
python manage.py resource_cli list-areas --search="Tennessee"
# Look for multiple results with different state_fips
# Add areas one at a time to identify conflicts
python manage.py resource_cli update 123 --add-areas="Tennessee"
python manage.py resource_cli update 123 --add-areas="Virginia"
```

**Solution**: Always check for duplicate area names and add areas individually

#### **6. Verification Field Requirements**
**Problem**: last_verified_by field requires User instance
```bash
# ❌ WRONG - String input fails
python manage.py resource_cli update 123 --json='{"last_verified_by":"AI Assistant"}'

# ✅ CORRECT - Use available user or omit field
python manage.py resource_cli update 123 --json='{"last_verified_at":"2025-09-02 00:00:00"}'
# last_verified_by will be set to current user automatically
```

**Solution**: Omit last_verified_by field or use existing user credentials

#### **7. Timestamp Format Issues**
**Problem**: Naive datetime warnings
```bash
# ❌ WRONG - May cause timezone warnings
python manage.py resource_cli update 123 --last_verified_at="2025-09-02 00:00:00"

# ✅ CORRECT - Use proper timezone format
python manage.py resource_cli update 123 --last_verified_at="2025-09-02T00:00:00Z"
# Or use current timestamp
python manage.py resource_cli update 123 --last_verified_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
```

**Solution**: Use ISO 8601 format with timezone or let system handle current time

#### **2. Service Area Assignment Issues**
**Problem**: Service area names not found
```bash
# ❌ WRONG - May fail if exact name doesn't match
python manage.py resource_cli update 123 --add-areas="Fayette County"

# ✅ CORRECT - Check exact names first
python manage.py resource_cli list-areas --search="Fayette"
python manage.py resource_cli update 123 --add-areas="Fayette County"
```

**Solution**: Always verify exact names with `list-areas --search`

#### **3. Command Syntax Uncertainty**
**Problem**: Unsure about command structure
```bash
# ❌ WRONG - Guessing command syntax
python manage.py resource_cli update 123 --unknown-field="value"

# ✅ CORRECT - Check help when unsure
python manage.py resource_cli update --help
```

**Solution**: Use `--help` for any command you're not 100% sure about

#### **4. Bulk Update Complexity**
**Problem**: Updating many fields individually
```bash
# ❌ WRONG - Multiple individual commands
python manage.py resource_cli update 123 --name="New Name"
python manage.py resource_cli update 123 --phone="555-1234"
python manage.py resource_cli update 123 --email="test@example.com"

# ✅ CORRECT - Single JSON update
python manage.py resource_cli update 123 --json='{
    "name": "New Name",
    "phone": "555-1234",
    "email": "test@example.com"
}'
```

**Solution**: Use JSON format for multiple field updates

### Examples
```bash
# See all available examples
python manage.py resource_cli --help

# See examples for specific command
python manage.py resource_cli create --help
```

### Error Messages
- All errors include descriptive messages
- Check the error message for specific guidance
- Use `--help` for command-specific options

---

## 📊 Success Metrics

### Verification Quality
- **Field Verification Rate**: Target 95%+ of fields verified (direct + inference)
- **Source Diversity**: Minimum 2 sources per field
- **Confidence Scores**: Target 80%+ fields with HIGH confidence
- **Update Accuracy**: 100% of changes properly documented
- **Inference Usage**: Track percentage of fields verified through logical inference

### Process Efficiency
- **Verification Time**: Target 15-30 minutes per resource
- **Source Utilization**: Prioritize primary sources
- **Documentation Completeness**: 100% of verifications documented
- **Status Management**: Proper workflow progression

---

**Last Updated**: January 2025  
**Version**: 1.5.0  
**Maintained by**: Resource Directory Team  
**Process Type**: Manual Human Verification + AI-Assisted Verification  
**Estimated Time per Resource**: 15-30 minutes

**🆕 NEW IN VERSION 1.5.0**: 
- **Service Type Management System** - CLI now supports managing service types for resources using `--add-service-types`, `--remove-service-types`, `--set-service-types`, and `--clear-service-types` flags
- **Service Type Discovery** - New `list-services` and `show-service` commands for exploring available service types
- **Enhanced Resource Categorization** - Resources can now have multiple specific service types assigned for better discoverability

**🆕 NEW IN VERSION 1.4.0**: 
- **Category Management System** - CLI now supports updating resource categories directly using `--category` flag
- **Area ID Management System** - CLI supports adding service areas by numeric ID for precise control and to avoid duplicate name issues

---

## 🔍 **VERIFICATION SESSION VALIDATION CHECKLIST**

**⚠️ COMPLETE THIS CHECKLIST BEFORE CONSIDERING ANY VERIFICATION SESSION COMPLETE**

### **Session Completion Validation**
- [ ] **Fresh MCP Web Search conducted** for ALL fields (not just reading existing notes)
- [ ] **MCP Playwright browser access used** for direct website verification
- [ ] **MCP tools prioritized** over basic command-line tools (curl, wget, grep)
- [ ] **Multiple sources consulted** for each field (minimum 2-3 sources)
- [ ] **Current information verified** (not historical or outdated data)
- [ ] **Verification template completed** with comprehensive documentation
- [ ] **Source URLs and timestamps recorded** for audit trail
- [ ] **MCP tool usage documented** in verification notes
- [ ] **Confidence scores assigned** to all verification findings
- [ ] **No assumptions made** without source verification
- [ ] **No existing data trusted** without re-verification
- [ ] **Service areas properly verified** using systematic process
- [ ] **Nationwide services assigned appropriate nationwide coverage area** (if applicable)
- [ ] **All critical fields verified** against primary sources

### **Documentation Validation**
- [ ] **Verification session notes** completed using Section 4.3 template
- [ ] **Source documentation** includes URLs, timestamps, and reliability scores
- [ ] **MCP tool usage documented** with specific tools used and rationale
- [ ] **Field verification results** documented with confidence levels
- [ ] **Inference usage documented** with basis and confidence levels
- [ ] **Quality assessment completed** with accuracy percentages
- [ ] **Recommendations documented** with specific action items

### **Status Management Validation - FINAL CHECK**
- [ ] **Resource moved to "needs_review" status** after verification
- [ ] **Verification fields updated** (last_verified_at, last_verified_by)
- [ ] **All corrections applied** and documented
- [ ] **Resource ready for human review** and validation
- [ ] **No resources left in "published" status** after verification

**⚠️ CRITICAL: Verification is NOT complete until resource is in "needs_review" status**

**ONLY MARK VERIFICATION COMPLETE AFTER ALL VALIDATION ITEMS ARE CHECKED**

---

**⚠️ REMEMBER: VERIFICATION IS FACT-CHECKING, NOT DATA ENTRY. EVERY SESSION REQUIRES FRESH SOURCE VERIFICATION.**

---

## 📋 **VERIFICATION WORKFLOW SUMMARY**

### **Status Workflow (CRITICAL)**
1. **Resource Selection**: Find resource in any status (draft, needs_review, published)
2. **Verification Process**: Complete comprehensive field-by-field verification
3. **Status Update**: Move resource to "needs_review" status after verification
4. **Human Review**: Human verifier reviews AI verification and approves
5. **Publication**: Only after human validation can resource move to "published" status

### **Key Rules to Remember**
- **After verification**: ALL resources must be in "needs_review" status
- **Verification ≠ Publication**: Verification is technical, publication requires human approval
- **Published resources**: Should never need verification (they should already be verified)
- **Human oversight**: Required for final publication decision
- **First verification run**: May encounter inconsistent records - verify all and move to needs_review

### **🚨 Nationwide Service Rules**
- **Nationwide services MUST use nationwide coverage area**: "United States (All States and Territories)" (ID: 43273)
- **Never assign only local areas to nationwide services**: This limits discoverability
- **Verify nationwide scope**: Check official sources to confirm nationwide availability
- **Test discoverability**: Ensure nationwide services appear in searches from any state

### **Verification Completion Checklist**
- [ ] All fields verified against multiple sources using MCP tools
- [ ] MCP Web Search and Playwright tools used for comprehensive verification
- [ ] Comprehensive documentation completed with MCP tool usage
- [ ] Resource moved to "needs_review" status
- [ ] Verification fields updated
- [ ] Ready for human review and validation

**⚠️ VERIFICATION IS NOT COMPLETE UNTIL RESOURCE IS IN "NEEDS_REVIEW" STATUS**
