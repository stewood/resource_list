# AI Resource Verification and Update Process

This document provides a complete step-by-step process for AI assistants to verify and update resource records in the Homeless Resource Directory.

## 🎯 Overview

This process follows a 3-step workflow:
1. **Identify** a draft resource to update
2. **Research** the organization to find verified information
3. **Update** the resource with verified data and move to "needs_review" status

## 📋 Step 1: Identify a Draft Resource

### Command to Find a Resource
```bash
cd /home/stewood/rl/cli_review
python auto_update_random.py --show-only
```

### What to Look For
- **Missing Information**: Resources with incomplete contact details, addresses, or descriptions
- **Outdated Information**: Resources that may have changed contact information
- **Incomplete Data**: Resources missing essential fields like phone, website, or location
- **Poor Quality**: Resources with minimal descriptions or unclear service information

### Priority Indicators
- ❌ Missing phone number
- ❌ Missing website
- ❌ Missing city/state
- ❌ Missing or poor description
- ❌ Missing service types
- ❌ Missing hours of operation

## 🔍 Step 2: Research Guidelines

### Search Strategy

#### 1. **Primary Search Sources**
- **Official Website**: Always start with the organization's official website
- **Google Search**: Use organization name + location + "contact"
- **Government Databases**: For government agencies and official services
- **Social Media**: Check Facebook, Twitter, LinkedIn for current information

#### 2. **Proven Research Techniques** (Based on Field Experience)
- **Start with exact phone number search**: "[Phone Number] [Organization Name] Kentucky" often yields the most relevant results
- **Use specific search terms**: Add "phone address hours" to get contact information quickly
- **Cross-reference multiple sources**: Always verify information from at least 2-3 sources
- **Check for recent updates**: Look for information updated within the last 2 years
- **Use browser bookmarks**: Save frequently visited sites like NCES for schools, government databases
- **Batch similar organizations**: Develop templates for common types (schools, churches, government agencies)

#### 3. **Search Queries to Use**
```
"[Organization Name] [City, State] phone address hours"
"[Organization Name] contact information"
"[Organization Name] official website"
"[Organization Name] services hours of operation"
"[Organization Name] eligibility requirements"
"[Phone Number] [Organization Name] Kentucky"  # Most effective for verification
```

#### 4. **Information to Verify**
- **Contact Information**: Phone, email, website
- **Location**: Full address, city, state, zip code
- **Hours**: Days and times of operation
- **Services**: What they actually provide
- **Eligibility**: Who can use their services
- **Cost**: Free, sliding scale, insurance accepted
- **Languages**: Languages spoken/available

#### 5. **Common Data Quality Issues Found** (Based on Field Experience)
- **Phone number formatting**: Many resources have unformatted numbers (e.g., "6068624639" vs "(606) 862-4639")
- **Missing city/state information**: Several resources lack basic location data
- **Outdated information**: Some phone numbers or addresses are no longer valid
- **Generic descriptions**: Many resources have minimal descriptions that need enhancement
- **Missing website URLs**: Official websites often exist but aren't listed

### Verification Rules

#### ✅ **Must Verify**
- **Phone Numbers**: Call or verify on official website
- **Addresses**: Check against official website or Google Maps
- **Hours**: Confirm current operating hours
- **Services**: Verify what services are actually provided
- **Website URLs**: Ensure they work and are current

#### ⚠️ **Cross-Reference**
- **Multiple Sources**: Check at least 2-3 sources for consistency
- **Government Sources**: Prefer official government websites
- **Recent Information**: Look for information updated within the last 2 years
- **Local Sources**: Prefer local/state sources over national ones

#### ❌ **Avoid**
- **Outdated Information**: Information older than 2 years
- **Third-Party Listings**: Unless they're official government databases
- **Unverified Claims**: Information that can't be confirmed
- **Personal Opinions**: Stick to factual information only

#### 📊 **Efficiency Metrics** (Based on Field Experience)
- **Average time per resource**: 5-10 minutes for most resources
- **Success rate**: ~90% of resources are successfully verifiable
- **Most time-consuming**: Resources with outdated information or multiple similar organizations
- **Quick wins**: Schools, government agencies, and well-established nonprofits

## 📝 Step 3: Update Process

### Required Fields for "Needs Review" Status

A resource must have these fields completed to move to "needs_review" status:

#### **Essential Fields**
- ✅ **City**: Required
- ✅ **State**: Required (2-letter code)
- ✅ **Description**: Minimum 20 characters
- ✅ **Source**: Where the information came from

#### **Recommended Fields**
- 📞 **Phone**: Contact number
- 🌐 **Website**: Official website URL
- 📍 **Address**: Full street address
- ⏰ **Hours**: Operating hours
- 🎯 **Service Types**: What services they provide

### Data Quality Standards

#### **Phone Numbers**
- **Format**: (555) 123-4567 or 555-123-4567
- **Toll-Free**: 1-800-XXX-XXXX format
- **Extension**: Include if provided (555-123-4567 ext. 123)

#### **Addresses**
- **Format**: Street address, City, State ZIP
- **Abbreviations**: Use standard USPS abbreviations
- **PO Boxes**: Include if that's the official address

#### **Hours of Operation**
- **Format**: "Monday-Friday 9:00 AM-5:00 PM"
- **24/7**: "24 hours a day, 7 days a week"
- **Closed Days**: "Closed on weekends"

#### **Descriptions**
- **Length**: Minimum 20 characters, aim for 50-200 characters
- **Content**: What services they provide, who they serve
- **Tone**: Professional, factual, clear

## 🔧 Update Process

### 1. Create Update Data File

Create a JSON file with the verified information. Use this template:

```json
{
  "name": "Organization Name",
  "description": "Comprehensive description of services provided...",
  "source": "Verified from official website and phone call",
  "phone": "(555) 123-4567",
  "email": "contact@organization.org",
  "website": "https://www.organization.org",
  "address1": "123 Main Street",
  "city": "City Name",
  "state": "KY",
  "county": "County Name",
  "postal_code": "12345",
  "hours_of_operation": "Monday-Friday 9:00 AM-5:00 PM",
  "is_emergency_service": false,
  "is_24_hour_service": false,
  "eligibility_requirements": "Who can use services",
  "populations_served": "Target demographics",
  "cost_information": "Financial details",
  "languages_available": "English, Spanish",
  "notes": "VERIFIED INFORMATION: All contact information verified on [DATE]. CITATIONS: [List specific URLs and sources used for verification]. [Additional verification details].",
  "service_type_ids": [1, 2, 3]
}
```

### 2. Notes Field Requirements

The notes field MUST include:
- **Verification date**
- **Specific citations** with URLs
- **Cross-reference information**
- **Verification details**

Example notes format:
```
VERIFIED INFORMATION: All contact information verified on 2024-01-15. CITATIONS: Contact information verified from official website https://www.organization.org/contact. Services and programs verified from main website https://www.organization.org. Phone number (555) 123-4567 confirmed working. Website verified current and accessible. All information cross-referenced with Google search results for consistency.
```

### 3. Run Update Command

```bash
# Update the resource
python update_resource_noninteractive.py [RESOURCE_ID] --data-file [FILENAME].json --transition needs_review
```

### 4. Verify Update

Check that:
- ✅ All required fields are filled
- ✅ Information is accurate and current
- ✅ Status changed to "needs review"
- ✅ Notes include proper citations
- ✅ Admin URL works and shows updated information

## 📊 Available Categories & Service Types

### Categories
- Child Care (ID: 14)
- Education (ID: 11)
- Food (ID: 2)
- Food Assistance (ID: 6)
- Healthcare (ID: 3)
- Hotlines (ID: 5)
- Housing (ID: 7)
- Legal (ID: 10)
- Medical (ID: 9)
- Mental Health (ID: 8)
- Other (ID: 16)
- Shelter (ID: 1)
- Transportation (ID: 12)
- Utilities (ID: 13)
- Veterans (ID: 15)

### Resource Type Research Approaches (Based on Field Experience)

#### **Schools**
- **Check NCES database** for official statistics and contact information
- **Visit district websites** for principal/administrator names and emails
- **Look for enrollment numbers** and student-teacher ratios
- **Verify grade levels served** and special programs offered

#### **Churches**
- **Check for food pantry** or community service programs
- **Look for Facebook pages** for current information and updates
- **Verify if they offer specific services** beyond worship
- **Check for multiple service times** and special programs

#### **Government Agencies**
- **Official .gov websites** are usually most reliable
- **Check for multiple contact methods** (phone, email, website)
- **Verify service areas** and eligibility requirements
- **Look for department heads** and key personnel

#### **Nonprofits**
- **Check for 501(c)(3) status** and mission statements
- **Look for specific programs** and services offered
- **Verify current operational status** and funding sources
- **Check for annual reports** or impact statements

### Service Types
- Child Care (ID: 10)
- Counseling (ID: 2)
- Domestic Violence (ID: 12)
- Education (ID: 9)
- Emergency Services (ID: 14)
- Emergency Shelter (ID: 18)
- Employment (ID: 7)
- Financial Assistance (ID: 15)
- Food Assistance (ID: 4)
- Food Pantry (ID: 17)
- Healthcare (ID: 6)
- Hotline (ID: 1)
- Hotlines (ID: 16)
- Housing (ID: 3)
- Job Training (ID: 24)
- Legal Aid (ID: 23)
- Legal Services (ID: 5)
- Medical Care (ID: 22)
- Mental Health Counseling (ID: 20)
- Substance Abuse (ID: 13)
- Substance Abuse Treatment (ID: 21)
- Transitional Housing (ID: 19)
- Transportation (ID: 8)
- Utility Assistance (ID: 25)
- Veterans Services (ID: 11)

## 🚀 Complete Workflow Example

### Step 1: Find Resource
```bash
cd /home/stewood/rl/cli_review
python auto_update_random.py --show-only
```

### Step 2: Research (Manual Process)
1. Search for organization online
2. Visit official website
3. Verify contact information
4. Check hours and services
5. Cross-reference with multiple sources
6. Document all sources used

### Step 3: Create Update File
Create a JSON file with verified information and proper citations.

### Step 4: Update Resource
```bash
python update_resource_noninteractive.py [ID] --data-file [FILENAME].json --transition needs_review
```

## 📋 Quality Checklist

Before marking a resource as "needs review", verify:

### **Contact Information**
- [ ] Phone number is current and working
- [ ] Website URL is valid and accessible
- [ ] Email address is correct (if provided)
- [ ] Address is complete and accurate

### **Service Information**
- [ ] Description clearly explains what they do
- [ ] Hours of operation are current
- [ ] Eligibility requirements are clear
- [ ] Cost information is accurate
- [ ] Service types match what they actually provide

### **Location Information**
- [ ] City and state are correct
- [ ] Full address is provided (if applicable)
- [ ] County information is accurate
- [ ] Postal code is correct

### **Documentation**
- [ ] Source is documented
- [ ] Verification date is noted
- [ ] Notes include verification details and citations
- [ ] Any limitations or special requirements are noted

## 🚨 Common Issues and Solutions

### **Organization No Longer Exists**
- **Action**: Mark as archived or update status
- **Note**: Document when and why it closed

### **Information Unavailable**
- **Action**: Use best available information
- **Note**: Document what couldn't be verified

### **Multiple Locations**
- **Action**: Create separate entries for each location
- **Note**: Ensure each has unique contact information

### **Seasonal or Limited Hours**
- **Action**: Document current hours and note any seasonal changes
- **Note**: Include information about seasonal availability

### **Language Barriers**
- **Action**: Note available languages
- **Note**: Include information about translation services

### **Invalid/Inactive Resources** (Based on Field Experience)
- **Action**: Mark as inactive when phone numbers don't return search results
- **Note**: Document search attempts made and reason for marking as inactive
- **Example**: "Phone number (606) 438-5929 does not return any search results and appears to be invalid"

### **Outdated Contact Information**
- **Action**: Update with current information when found
- **Note**: Document both old and new information in notes
- **Example**: "Phone number updated from (606) 260-9164 to (606) 330-1677 based on current website"

### **Generic Organization Names**
- **Action**: Research thoroughly to find the specific organization
- **Note**: Document the specific location and services offered
- **Example**: "Whispering Pines" could be a residential property rather than a service organization

## 📞 Contact Information Standards

### **Phone Numbers**
- **Local**: (555) 123-4567
- **Toll-Free**: 1-800-123-4567
- **International**: +1-555-123-4567
- **Extension**: (555) 123-4567 ext. 123

### **Email Addresses**
- **Format**: contact@organization.org
- **Verification**: Check if email is publicly listed

### **Websites**
- **Format**: https://www.organization.org
- **Verification**: Ensure site is accessible and current

## 🎯 Success Metrics

A successful update should result in:
- ✅ Resource moved from "draft" to "needs review"
- ✅ All required fields completed
- ✅ Information verified from reliable sources
- ✅ Clear, professional description
- ✅ Accurate contact and location information
- ✅ Proper categorization and service types
- ✅ Comprehensive notes with citations

## 📚 Resources for Research

### **Government Sources**
- Official government websites (.gov domains)
- State and local government directories
- Department of Health and Human Services
- Department of Housing and Urban Development

### **Non-Profit Directories**
- 211.org
- Charity Navigator
- GuideStar
- Local United Way directories

### **Verification Tools**
- Google Maps for address verification
- Phone number lookup services
- Website accessibility checkers
- Social media presence verification

### **Proven Research Sources** (Based on Field Experience)

#### **For Schools**
- **NCES (National Center for Education Statistics)**: https://nces.ed.gov/ccd/schoolsearch/
- **District websites**: Usually contain staff directories and contact information
- **GreatSchools.org**: For ratings and basic information
- **School Facebook pages**: For current updates and community information

#### **For Government Agencies**
- **Official .gov websites**: Most reliable source
- **County/city government directories**: For local agencies
- **State government databases**: For state-level services
- **Government contact directories**: Often have multiple contact methods

#### **For Nonprofits**
- **Official organization websites**: Primary source
- **Facebook pages**: For current information and community engagement
- **Local news articles**: For recent updates and program information
- **Annual reports**: For detailed service information

#### **For Churches**
- **Official church websites**: For service times and programs
- **Facebook pages**: For current community programs and food pantries
- **Local community directories**: For outreach programs
- **Denominational directories**: For contact verification

## 💡 Pro Tips for Efficiency (Based on Field Experience)

### **Technical Efficiency**
- **Use virtual environment consistently**: Activate it each time to avoid dependency issues
- **Keep browser open between resources**: Avoid repeated navigation to common sites
- **Use non-interactive script**: More efficient than manual updates
- **Save update files with descriptive names**: Makes it easier to track progress

### **Research Efficiency**
- **Don't spend excessive time on unverifiable resources**: If phone numbers don't return results after 2-3 searches, mark as inactive
- **Use "Find in page" feature**: Quickly locate contact information on long web pages
- **Bookmark frequently visited sites**: NCES, government databases, etc.
- **Develop templates for common resource types**: Schools, churches, government agencies

### **Quality Assurance**
- **Always verify phone numbers**: Search for them specifically to ensure they're current
- **Check for multiple locations**: Some organizations have branches that need separate entries
- **Verify business hours**: Often missing from original data but important for users
- **Look for recent updates**: Some organizations may have moved or changed contact info

### **Data Quality Improvements**
- **Standardize phone number formatting**: Convert "6068624639" to "(606) 862-4639"
- **Add missing city/state information**: Essential for location-based searches
- **Enhance descriptions**: Replace generic descriptions with specific services
- **Include website URLs**: Critical for user access to current information

---

**Last Updated**: January 2024
**Version**: 1.1
**Maintained By**: Resource Directory Team
**For AI Assistants**: Follow this process exactly to ensure consistent, high-quality resource updates
**Field Tested**: Process validated through verification of 10+ resources with 90% success rate
