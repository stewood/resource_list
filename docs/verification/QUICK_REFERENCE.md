# Verification Process Quick Reference

## 🚀 Quick Start Workflow

### 0. Activate Virtual Environment ⚠️ **REQUIRED**
```bash
# From project root directory
source venv/bin/activate
```

### 1. Find Next Resource to Verify
```bash
# From project root (with venv activated)
python docs/verification/find_next_verification.py
```

### 2. Extract Current Resource Data
```bash
# Replace RESOURCE_ID with actual ID
source venv/bin/activate
python manage.py shell -c "from directory.models import Resource; import json; resource = Resource.objects.get(id=RESOURCE_ID); data = {'id': resource.id, 'name': resource.name, 'category': resource.category.name if resource.category else None, 'description': resource.description, 'phone': resource.phone, 'email': resource.email, 'website': resource.website, 'address1': resource.address1, 'address2': resource.address2, 'city': resource.city, 'state': resource.state, 'county': resource.county, 'postal_code': resource.postal_code, 'hours_of_operation': resource.hours_of_operation, 'eligibility_requirements': resource.eligibility_requirements, 'populations_served': resource.populations_served, 'cost_information': resource.cost_information, 'languages_available': resource.languages_available, 'source': resource.source, 'notes': resource.notes}; print(json.dumps(data, indent=2))"
```

### 3. Research and Verify Information
- **Primary Sources**: Official website, phone calls, government databases
- **Secondary Sources**: Cross-references, social media, additional research
- **Field Analysis**: Check each field for clarity, completeness, and accuracy

### 4. Create Change Summary and Request Approval ⚠️ **CRITICAL STEP**
**⚠️ IMPORTANT: You MUST summarize changes and get approval BEFORE applying them.**

Create a clear summary of all proposed changes:

```
## PROPOSED CHANGES SUMMARY - [Resource Name] (ID: [X])

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

### ❓ CLARIFICATION QUESTIONS (if any)
- **Question**: [Specific question about unclear information]
- **Recommendation**: [Your recommendation with reasoning]
- **Question**: [Another specific question if needed]
- **Recommendation**: [Your recommendation with reasoning]
```

**Request Approval:**
"Please review the proposed changes above and address any clarification questions. Do you approve these updates?

✅ **APPROVED** - Proceed with implementation
❌ **REJECTED** - Revise proposal
⏸️ **ON HOLD** - Need more information
❓ **NEEDS CLARIFICATION** - Please answer the questions above

**Response required before proceeding.**"

### 5. Create Verification Config File
Create a JSON file with verified information (ONLY after approval):
```json
{
  "phone": "(800) 123-4567",
  "email": "contact@example.com",
  "website": "https://example.com",
  "address1": "123 Main St",
  "city": "City",
  "state": "ST",
  "county": "County",
  "postal_code": "12345",
  "hours_of_operation": "Monday-Friday 9:00 AM - 5:00 PM",
  "eligibility_requirements": "Requirements here",
  "populations_served": "Target populations",
  "cost_information": "Cost details",
  "languages_available": "Available languages",
  "description": "Updated description",
  "verification_notes": "# Verification Summary - [Organization Name] (Resource ID: [ID])\n\n## Verification Date: [Date]\n**Verified By**: Homeless AI System\n**Next Review**: [Date + 6 months]\n\n---\n\n## 🎯 EXECUTIVE SUMMARY\n**Overall Status**: ✅ VERIFIED\n**Priority Level**: 🟢 LOW\n**Key Changes**: [Brief summary]\n\n---\n\n## ✅ VERIFIED INFORMATION\n### Contact Information\n- **Phone**: [Current] → [Verified] | **Source**: [Source]\n- **Email**: [Current] → [Verified] | **Source**: [Source]\n- **Website**: [Current] → [Verified] | **Source**: [Source]\n\n### Location Information\n- **Address**: [Current] → [Verified] | **Source**: [Source]\n- **City/State/County**: [Current] → [Verified] | **Source**: [Source]\n\n### Service Information\n- **Hours**: [Current] → [Verified] | **Source**: [Source]\n- **Eligibility**: [Current] → [Verified] | **Source**: [Source]\n- **Populations**: [Current] → [Verified] | **Source**: [Source]\n- **Cost**: [Current] → [Verified] | **Source**: [Source]\n- **Languages**: [Current] → [Verified] | **Source**: [Source]\n\n---\n\n## 🔄 CHANGES MADE\n### Field Updates\n- **Phone**: [Old] → [New] | **Reason**: [Reason]\n- **Hours**: [Old] → [New] | **Reason**: [Reason]\n- **Description**: [Old] → [New] | **Reason**: [Reason]\n\n### New Information Added\n- **Office Phone**: [New] | **Source**: [Source]\n- **Additional Services**: [New] | **Source**: [Source]\n\n---\n\n## 📝 VERIFICATION METHODOLOGY\n### Primary Sources\n1. **Official Website**: [URL] - [What was verified]\n2. **Phone Verification**: [Number called] - [What was confirmed]\n3. **Government Database**: [Database name] - [What was verified]\n\n### Secondary Sources\n1. **Cross-Reference**: [Source] - [What was confirmed]\n2. **Additional Research**: [Source] - [What was found]\n\n### Verification Process\n- [x] Website functionality tested\n- [x] Phone number called and verified\n- [x] Email address tested\n- [x] Address verified with mapping service\n- [x] Service details cross-referenced\n- [x] Multiple sources consulted\n\n---\n\n## 🔍 KEY FINDINGS\n### ✅ Confirmed Accurate\n- [Finding 1 with source]\n- [Finding 2 with source]\n\n### ⚠️ Needs Clarification\n- [Finding 1 with explanation]\n- [Finding 2 with explanation]\n\n### ❌ Corrected Information\n- [Correction 1 with reason]\n- [Correction 2 with reason]\n\n---\n\n## 🔄 NEXT VERIFICATION RECOMMENDATIONS\n### Priority Actions\n1. **High Priority**: [Action needed]\n2. **Medium Priority**: [Action needed]\n3. **Low Priority**: [Action needed]\n\n### Future Verification Focus\n- [Area 1 to focus on]\n- [Area 2 to focus on]\n\n### Missing Information to Pursue\n- [Information 1]\n- [Information 2]\n\n---\n\n## 📊 VERIFICATION METRICS\n- **Fields Verified**: [X] of [Y] fields\n- **Sources Consulted**: [Number] sources\n- **Changes Made**: [Number] field updates\n- **Data Quality Score**: [X]% complete\n- **Verification Confidence**: [High/Medium/Low]\n\n---\n\n## 🔗 SOURCES & CITATIONS\n### Primary Sources\n- [Source 1]: [URL/Contact Info]\n- [Source 2]: [URL/Contact Info]\n\n### Supporting Documentation\n- [Document 1]: [URL/Reference]\n- [Document 2]: [URL/Reference]\n\n---\n\n**Template Version**: 1.0\n**Last Updated**: [Date]\n\n--- TEMPLATE-BASED VERIFICATION [Date] ---\nThis verification was conducted using the standardized verification template.\nAll verification findings have been documented above with specific sources and details."
}
```

### 6. Update Resource with Verified Information
```bash
# Preview changes first (with venv activated)
python docs/verification/update_resource_verification.py --id RESOURCE_ID --config verification_data.json --preview

# Apply changes (with venv activated)
python docs/verification/update_resource_verification.py --id RESOURCE_ID --config verification_data.json
```

### 7. Verify Update Was Successful
```bash
source venv/bin/activate
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print(f'Resource: {resource.name}'); print(f'Last Verified: {resource.last_verified_at}'); print(f'Next Due: {resource.next_verification_date}'); print(f'Notes Length: {len(resource.notes) if resource.notes else 0} characters')"
```

## 📋 Verification Checklist

### Contact Information
- [ ] Phone number verified (Note: Phone numbers are automatically formatted for display)
- [ ] Email address tested and functional
- [ ] Website tested and accessible
- [ ] Address verified with mapping service

### Service Information
- [ ] Hours of operation current and clear
- [ ] Eligibility requirements complete and accurate
- [ ] Populations served specific and comprehensive
- [ ] Cost information clear and complete
- [ ] Languages available documented

### Quality Standards
- [ ] Minimum 2 sources consulted for each field
- [ ] Primary source is official organization material
- [ ] Secondary source provides independent verification
- [ ] All sources documented in verification notes

### Phone Number Formatting
- [ ] Phone number accuracy verified (formatting is automatic)
- [ ] Phone number displays correctly in templates
- [ ] Tel links work properly for mobile devices

### Documentation
- [ ] Verification template filled out completely
- [ ] All changes documented with reasons
- [ ] Sources and citations included
- [ ] Next verification recommendations noted

## 🔧 Common Commands

### Show Verification Queue
```bash
# With venv activated
python docs/verification/update_resource_verification.py --queue
```

### Apply Empty Template
```bash
# With venv activated
python docs/verification/update_resource_verification.py --id RESOURCE_ID --template verification_template.md
```

### Update Individual Fields
```bash
# With venv activated
python docs/verification/update_resource_verification.py --id RESOURCE_ID --phone "(800) 123-4567" --email "contact@example.com"
```

### Check Resource Status
```bash
# With venv activated
python manage.py shell -c "from directory.models import Resource; resource = Resource.objects.get(id=RESOURCE_ID); print(f'Name: {resource.name}'); print(f'Status: {resource.status}'); print(f'Last Verified: {resource.last_verified_at}'); print(f'Needs Verification: {resource.needs_verification}')"
```

## 📊 Quality Metrics

### Success Criteria
- **Data Completeness**: 90%+ of fields filled
- **Verification Coverage**: 100% of published resources verified
- **Accuracy Rate**: 95%+ of verified information confirmed correct
- **Update Frequency**: Average 6 months between verifications

### Priority Levels
- **🔴 HIGH**: Emergency services, shelters, hotlines
- **🟡 MEDIUM**: Healthcare, housing, food assistance  
- **🟢 LOW**: Other services, administrative

## 🆘 Troubleshooting

### Common Issues
1. **Script not found**: Run from project root directory
2. **Virtual environment not activated**: Run `source venv/bin/activate` first
3. **Database connection error**: Ensure virtual environment is activated
4. **ModuleNotFoundError**: Ensure virtual environment is activated and Django is installed
5. **Template not loading**: Check file path and permissions
6. **Verification notes not updating**: Ensure `verification_notes` field in JSON config

### Getting Help
1. Check the full documentation in `VERIFICATION.md`
2. Review example implementations in the documentation
3. Check the verification log for recent activity
4. Contact the data management team for complex issues

---

**Quick Reference Version**: 1.1  
**Last Updated**: January 2025  
**For Complete Process**: See `VERIFICATION.md`
