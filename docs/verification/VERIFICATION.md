# Resource Verification Process Guide

## Overview
This document outlines the systematic process for verifying and updating resource records in the Homeless Resource Directory. The process ensures data accuracy, completeness, and provides an audit trail for all changes.

## Prerequisites

**⚠️ IMPORTANT: Virtual Environment Required**

Before starting the verification process, you MUST activate the virtual environment:

```bash
# From project root directory
source venv/bin/activate
```

All verification commands require the virtual environment to be active for proper Django database access and dependency management.

## Process Workflow

The verification process follows these 10 steps:

1. **Environment Setup** - Activate virtual environment
2. **Resource Selection** - Find the next resource to verify
3. **Data Extraction** - Extract complete resource information
4. **Verification Research** - Research using multiple sources
5. **Field-by-Field Analysis** - Analyze each field for clarity and completeness
6. **Data Analysis & Recommendations** - Determine verification status
7. **Change Proposal** - Create comprehensive update proposal using standardized template
8. **Approval Process** - Present proposal for review
9. **Implementation** - Update the resource record
10. **Documentation** - Update verification notes using standardized template

### Step 1: Environment Setup
**Activate the virtual environment:**
```bash
# From project root directory
source venv/bin/activate
```

### Step 2: Resource Selection
**Methods to find a resource:**
1. **By ID**: Use Django shell to find specific resource
   ```bash
   # With venv activated
   python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print(f'Found: {resource.name}')"
   ```

2. **By Name**: Search for resources by name
   ```bash
   # With venv activated
   python manage.py shell -c "from directory.models import Resource; resources = Resource.objects.filter(name__icontains='SEARCH_TERM'); [print(f'ID: {r.id}, Name: {r.name}') for r in resources]"
   ```

3. **Random Selection**: Pick a random resource for verification
   ```bash
   # With venv activated
   python manage.py shell -c "from directory.models import Resource; import random; published_resources = list(Resource.objects.filter(status='published')); resource = random.choice(published_resources) if published_resources else None; print(f'Selected: ID {resource.id} - {resource.name}') if resource else print('No resources found')"
   ```

### Step 3: Data Extraction
Extract complete resource information for analysis:

```bash
# With venv activated
python manage.py shell -c "from directory.models import Resource; import json; resource = Resource.objects.get(id=RESOURCE_ID); data = {'id': resource.id, 'name': resource.name, 'category': resource.category.name if resource.category else None, 'description': resource.description, 'phone': resource.phone, 'email': resource.email, 'website': resource.website, 'address1': resource.address1, 'address2': resource.address2, 'city': resource.city, 'state': resource.state, 'county': resource.county, 'postal_code': resource.postal_code, 'hours_of_operation': resource.hours_of_operation, 'eligibility_requirements': resource.eligibility_requirements, 'populations_served': resource.populations_served, 'cost_information': resource.cost_information, 'languages_available': resource.languages_available, 'source': resource.source, 'notes': resource.notes}; print(json.dumps(data, indent=2))"
```

### Step 4: Verification Research
For each field, conduct verification using multiple sources:

#### 3.1 Primary Research Sources
1. **Official Website**: Visit organization's website
2. **Google Search**: Search for organization name + location
3. **Government Databases**: Check state/local government listings
4. **Phone Verification**: Call the organization directly
5. **Social Media**: Check organization's social media presence

#### 3.2 Field-Specific Verification

**Contact Information:**
- [ ] Phone number: Call to verify (Note: Phone numbers are stored as digits-only but displayed with formatting)
- [ ] Email: Check website contact page
- [ ] Website: Test link functionality
- [ ] Address: Verify with Google Maps/geocoding

**Service Information:**
- [ ] Description: Compare with official materials
- [ ] Hours: Check website or call
- [ ] Eligibility: Review official requirements
- [ ] Populations served: Verify target demographics
- [ ] Cost: Get current pricing information
- [ ] Languages: Confirm available languages

**Categorization:**
- [ ] Review current category assignment
- [ ] Verify it matches primary service
- [ ] Suggest better category if needed

### Step 5: Field-by-Field Analysis for Clarity and Expansion
Before determining verification status, analyze each field for clarity, completeness, and user-friendliness:

#### 4.1 Contact Information Analysis
- **Phone Number**: Verify accuracy (Note: Phone numbers are automatically formatted for display in templates)
- **Email**: Verify if missing email should be added
- **Website**: Test functionality and note any issues
- **Address**: Verify formatting and completeness

#### 4.2 Service Information Analysis
- **Description**: Check for accuracy, clarity, and completeness
- **Hours**: Verify if hours are clearly stated and accurate
- **Eligibility**: Check if requirements are clearly explained
- **Populations**: Verify if target populations are specific enough
- **Cost**: Ensure cost information is clear and complete
- **Languages**: Check if language availability is clearly stated

#### 4.3 Missing Information Check
- **Additional Contact Methods**: Look for office phones, fax numbers, etc.
- **Online Services**: Check for online reporting, applications, or forms
- **Additional Resources**: Look for related services or referral information
- **Emergency Information**: Check for emergency contact procedures

#### 4.4 Clarity Improvements
For each field, consider:
- **Readability**: Is the information easy to understand?
- **Completeness**: Does it provide all necessary details?
- **Accuracy**: Does it match current service offerings?
- **User-Friendliness**: Is it helpful for someone seeking services?

### Step 6: Data Analysis & Recommendations
For each field, determine:

1. **✅ VERIFIED**: Information is accurate and current
2. **❌ INCORRECT**: Information needs correction
3. **❓ MISSING**: Information is not available
4. **🔄 OUTDATED**: Information needs updating
5. **📝 NEEDS CLARIFICATION**: Information is accurate but could be clearer
6. **➕ NEEDS EXPANSION**: Information is accurate but incomplete

**⚠️ IMPORTANT**: Any fields marked as "📝 NEEDS CLARIFICATION" MUST be addressed as specific questions in the approval process (Step 8.2). Do not proceed with implementation until clarification questions are resolved.

### Step 7: Change Proposal
Create a comprehensive proposal including:

#### 6.1 Field Updates
- **Email**: [Current] → [Proposed]
- **Hours**: [Current] → [Proposed]
- **Eligibility**: [Current] → [Proposed]
- **Populations**: [Current] → [Proposed]
- **Cost**: [Current] → [Proposed]
- **Languages**: [Current] → [Proposed]
- **Description**: [Current] → [Proposed]
- **Category**: [Current] → [Proposed]

#### 6.2 Clarification Questions
**⚠️ CRITICAL**: If any fields were marked as "📝 NEEDS CLARIFICATION" in Step 6, prepare specific questions for the approval process. These questions should:
- Be specific and actionable
- Include your recommendation with reasoning
- Allow stakeholders to make informed decisions
- Prevent implementation of unclear or potentially incorrect information

#### 6.3 Verification Summary
Document all verification findings using the standardized template:

**Template File**: `verification_template.md`

The verification summary should follow the comprehensive template structure that includes:

- **Executive Summary**: Overall status and key changes
- **Verified Information**: All verified fields with sources
- **Changes Made**: Detailed field updates with reasons
- **Verification Methodology**: Primary and secondary sources
- **Key Findings**: Confirmed, needs clarification, and corrected information
- **Next Verification Recommendations**: Priority actions and focus areas
- **Verification Metrics**: Data quality scores and confidence levels
- **Sources & Citations**: Complete source documentation

**Template Usage**:
```bash
# Use template with verification script
python update_resource_verification.py --id RESOURCE_ID --template verification_template.md

# Or manually fill out the template and include in verification notes
```

### Step 8: Approval Process ⚠️ **CRITICAL STEP**
**⚠️ IMPORTANT: You MUST present the complete proposal for approval BEFORE making any changes.**

Present the complete proposal to stakeholders for review:

1. **Current State**: Show existing data
2. **Proposed Changes**: Detail all recommended updates
3. **Verification Evidence**: Provide sources and methodology
4. **Impact Assessment**: Explain how changes improve data quality
5. **Clarification Questions**: Address any "Needs Clarification" items as specific questions
6. **Approval Request**: Get explicit sign-off before implementation

#### 7.1 Change Summary Format
Create a clear summary of all proposed changes:

```
## PROPOSED CHANGES SUMMARY

### Contact Information
- Phone: [Current] → [Proposed] | Reason: [Explanation]
- Email: [Current] → [Proposed] | Reason: [Explanation]
- Website: [Current] → [Proposed] | Reason: [Explanation]

### Location Information
- Address: [Current] → [Proposed] | Reason: [Explanation]
- Postal Code: [Current] → [Proposed] | Reason: [Explanation]

### Service Information
- Hours: [Current] → [Proposed] | Reason: [Explanation]
- Eligibility: [Current] → [Proposed] | Reason: [Explanation]
- Populations: [Current] → [Proposed] | Reason: [Explanation]
- Cost: [Current] → [Proposed] | Reason: [Explanation]
- Languages: [Current] → [Proposed] | Reason: [Explanation]

### Description
- [Current] → [Proposed] | Reason: [Explanation]

### Verification Notes
- Will be updated with comprehensive verification summary
```

#### 7.2 Clarification Questions Section
**⚠️ CRITICAL: Address all "Needs Clarification" items as specific questions:**

If any fields were marked as "📝 NEEDS CLARIFICATION" during Step 6, include a dedicated section:

```
## ❓ CLARIFICATION QUESTIONS

### Category Assignment
- **Current Category**: [Current Category]
- **Question**: Should this resource be categorized as [Category A] or [Category B] given its multiple service offerings?
- **Recommendation**: [Your recommendation with reasoning]

### Eligibility Requirements
- **Current**: [Current eligibility info]
- **Question**: Should we include specific eligibility criteria for [Program X] or keep it general?
- **Recommendation**: [Your recommendation with reasoning]

### Additional Information
- **Question**: Should we add [specific information] to the description?
- **Recommendation**: [Your recommendation with reasoning]
```

#### 7.3 Approval Request
**ALWAYS ask for explicit approval before proceeding:**

"Please review the proposed changes above and address any clarification questions. Do you approve these updates to Resource ID [X] - [Resource Name]? 

✅ **APPROVED** - Proceed with implementation
❌ **REJECTED** - Revise proposal
⏸️ **ON HOLD** - Need more information
❓ **NEEDS CLARIFICATION** - Please answer the questions above

**Response required before proceeding with Step 9.**"

### Step 9: Implementation
Once approved, update the resource record:

#### 8.1 Use the Verification Update Script
**Recommended Method**: Use the automated verification script for safe, consistent updates.

```bash
# Update with individual field changes
python docs/verification/update_resource_verification.py --id RESOURCE_ID --phone "(800) 123-4567" --email "contact@example.com"

# Update with JSON config file (recommended for comprehensive updates)
python docs/verification/update_resource_verification.py --id RESOURCE_ID --config verification_data.json

# Preview changes before applying
python docs/verification/update_resource_verification.py --id RESOURCE_ID --config verification_data.json --preview
```

**Manual Method**: Create custom update script (use only when automated script doesn't meet needs)
```python
#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, TaxonomyCategory

def update_resource():
    try:
        resource = Resource.objects.get(id=RESOURCE_ID)
        
        # Update fields with verified information
        resource.email = 'verified_email@example.com'
        resource.hours_of_operation = 'verified_hours'
        resource.eligibility_requirements = 'verified_eligibility'
        resource.populations_served = 'verified_populations'
        resource.cost_information = 'verified_cost'
        resource.languages_available = 'verified_languages'
        resource.description = 'verified_description'
        
        # Update category if needed
        if NEW_CATEGORY_ID:
            new_category = TaxonomyCategory.objects.get(id=NEW_CATEGORY_ID)
            resource.category = new_category
        
        # Update verification notes
        resource.notes = '''[VERIFICATION_SUMMARY_HERE]'''
        
        resource.save()
        print("✅ Resource updated successfully!")
        
    except Resource.DoesNotExist:
        print("❌ Resource not found!")
    except Exception as e:
        print(f"❌ Error updating resource: {e}")

if __name__ == '__main__':
    update_resource()
```

#### 8.2 Execute Update
```bash
# From project root
source venv/bin/activate
python docs/verification/update_resource_verification.py --id RESOURCE_ID --config verification_data.json

# Or for manual script
python update_resource_script.py
```

#### 8.3 Verify Update
```bash
source venv/bin/activate
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print('Update verification:'); print(f'Email: {resource.email}'); print(f'Hours: {resource.hours_of_operation[:50]}...'); print(f'Category: {resource.category.name if resource.category else \"None\"}')"
```

### Step 10: Documentation
Update the verification notes with:

1. **Implementation Date**: When changes were made
2. **Approver**: Who approved the changes
3. **Next Review Date**: When to re-verify (typically 6 months)
4. **Change Summary**: Brief overview of what was updated

## Quality Standards

### Verification Requirements
- **Minimum 2 sources** for each piece of information
- **Primary source** should be official organization materials
- **Secondary source** should be independent verification
- **Document all sources** in verification notes

### Data Quality Criteria
- **Accuracy**: Information matches official sources
- **Completeness**: All relevant fields are filled
- **Currency**: Information is up-to-date
- **Consistency**: Information is internally consistent
- **Accessibility**: Information is clear and usable

### Phone Number Formatting Standards
**Important**: Phone numbers are automatically formatted for display in the system.

#### Storage Format
- **Database Storage**: Phone numbers are stored as digits-only (e.g., "8776966775")
- **Automatic Normalization**: The system automatically strips all non-digit characters during save
- **Validation**: Phone numbers must contain only digits (0-9)

#### Display Format
- **Automatic Formatting**: Phone numbers are automatically formatted for display in templates
- **Format Rules**:
  - 10 digits: `(XXX) XXX-XXXX` (e.g., "5551234567" displays as "(555) 123-4567")
  - 11 digits starting with 1: `(XXX) XXX-XXXX` (e.g., "15551234567" displays as "(555) 123-4567")
  - Other formats: Displayed as stored
- **Template Integration**: All templates automatically apply formatting via `{{ phone|format_phone }}`

#### Verification Guidelines
- **Verify Accuracy**: Focus on verifying the phone number is correct, not formatting
- **Storage Format**: When updating, you can use any format - the system will normalize it
- **Display Testing**: Verify that phone numbers display correctly in the public interface
- **Tel Links**: Phone numbers automatically generate clickable `tel:` links for mobile devices

#### Examples
```
Input: "(877) 696-6775" → Storage: "8776966775" → Display: "(877) 696-6775"
Input: "877-696-6775" → Storage: "8776966775" → Display: "(877) 696-6775"
Input: "8776966775" → Storage: "8776966775" → Display: "(877) 696-6775"
```

### Categorization Guidelines
- **Primary service** determines category
- **Secondary services** may warrant additional categories
- **Avoid generic categories** when specific ones exist
- **Consider user search patterns** when categorizing

## Tools and Resources

### Research Tools
- **Web Search**: Google, Bing, DuckDuckGo
- **Government Databases**: State/local government websites
- **Social Media**: Facebook, Twitter, LinkedIn
- **Phone Verification**: Direct calls to organizations
- **Maps**: Google Maps, Apple Maps for address verification

### Database Tools
- **Django Shell**: For data extraction and updates
- **Management Commands**: For bulk operations
- **Admin Interface**: For manual updates when needed

### Documentation Tools
- **Markdown**: For verification notes
- **JSON**: For data export/import
- **Spreadsheets**: For tracking verification progress

## Example: Oxford House Verification

### Initial State
- **Category**: Child Care (incorrect)
- **Email**: Missing
- **Hours**: Missing
- **Eligibility**: Missing
- **Cost**: Missing
- **Languages**: Missing

### Verification Process
1. **Website Research**: oxfordhouseky.org
2. **National Site**: oxfordhouse.org/faq
3. **Government Database**: dbhdid.ky.gov
4. **Cross-Reference**: Multiple sources

### Final State
- **Category**: Housing (correct)
- **Email**: info@oxfordhouseky.org
- **Hours**: 24/7 residential facilities
- **Eligibility**: Complete requirements
- **Cost**: EES system explained
- **Languages**: English primary
- **Verification Notes**: Complete audit trail

## Example: Clarification Questions Process

### Scenario: Multi-Service Organization
When verifying an organization that provides multiple services (like CHFS), you may encounter fields that need clarification:

### Clarification Questions Example
```
## ❓ CLARIFICATION QUESTIONS

### Category Assignment
- **Current Category**: Food Assistance
- **Question**: Should this resource be categorized as "Government Services" or "Social Services" given that it provides SNAP, Medicaid, child protection, family assistance, and energy assistance?
- **Recommendation**: Recommend "Government Services" as it's a state government agency providing multiple essential services

### Eligibility Requirements
- **Current**: [Empty]
- **Question**: Should we include specific eligibility criteria for each program (SNAP, Medicaid, etc.) or keep it general since requirements vary by program?
- **Recommendation**: Keep it general with a note to contact specific program hotlines, as eligibility varies significantly between programs

### Additional Contact Information
- **Question**: Should we add the various program-specific hotline numbers to the notes section?
- **Recommendation**: Yes, add them to provide users with direct access to specific services
```

### Resolution Process
1. **Present Questions**: Include clarification questions in the approval request
2. **Get Answers**: Wait for stakeholder responses
3. **Update Proposal**: Modify the proposal based on answers
4. **Re-approve**: Get final approval before implementation

## Maintenance Schedule

### Regular Reviews
- **Monthly**: Review verification queue
- **Quarterly**: Re-verify high-priority resources
- **Annually**: Complete system review

### Priority Levels
- **High**: Emergency services, shelters, hotlines
- **Medium**: Healthcare, housing, food assistance
- **Low**: Other services, administrative

### Success Metrics
- **Data Completeness**: % of fields filled
- **Verification Coverage**: % of resources verified
- **Accuracy Rate**: % of verified information confirmed correct
- **Update Frequency**: Average time between verifications

---

**Document Version**: 1.2
**Last Updated**: January 2025
**Next Review**: July 2025
