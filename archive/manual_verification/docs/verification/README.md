# Resource Verification Documentation

This folder contains comprehensive documentation for the resource verification process used in the Homeless Resource Directory.

## Contents

### [VERIFICATION.md](./VERIFICATION.md)
**Complete Resource Verification Process Guide**

A comprehensive step-by-step guide for verifying and updating resource records in the Homeless Resource Directory. This document outlines the systematic process that ensures data accuracy, completeness, and provides an audit trail for all changes.

#### Key Sections:
- **Process Workflow** - 9-step systematic approach including field-by-field analysis
- **Approval Process** - **CRITICAL** step requiring explicit approval before changes
- **Quality Standards** - Verification requirements and data quality criteria
- **Tools and Resources** - Research tools and database commands
- **Example Implementation** - Oxford House case study
- **Maintenance Schedule** - Regular review and priority guidelines

#### What You'll Learn:
- How to find resources by ID, name, or random selection
- How to extract complete resource data for analysis
- How to verify information using multiple sources
- How to analyze each field for clarity and completeness
- How to create comprehensive change proposals
- **How to present changes for approval before implementation**
- How to implement updates safely with audit trails
- How to maintain data quality over time
- How to use standardized verification templates for consistent documentation
- How phone number formatting works (automatic display formatting)

#### Target Audience:
- **Data Managers** - Systematic approach to data quality
- **Case Managers** - Understanding verification process
- **Developers** - Technical implementation details
- **Administrators** - Process oversight and maintenance

### [find_next_verification.py](./find_next_verification.py)
**Resource Verification Finder Tool**

An automated utility that finds the next resource requiring verification and displays comprehensive information to streamline the verification process.

### [update_resource_verification.py](./update_resource_verification.py)
**Resource Verification Update Tool**

A non-interactive script for updating resource records during verification. Designed for AI-assisted verification workflows.

#### Features:
- **Non-Interactive Operation** - Accepts all data via command-line arguments or JSON config files
- **Comprehensive Field Updates** - Updates all resource fields with validation
- **Preview Mode** - Review changes before applying them
- **Verification Tracking** - Automatically updates verification timestamps and notes
- **Safety Features** - Validation, logging, and change summaries
- **Multiple Input Methods** - Command-line arguments, JSON config files, or both
- **Template Integration** - Support for standardized verification templates

### [verification_template.md](./verification_template.md)
**Standardized Verification Template**

A comprehensive template for documenting verification findings and ensuring consistent, professional verification reports across all resources.

### [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
**Quick Reference Guide**

A concise reference for experienced users to quickly execute the verification process without reading the full documentation.

### [PHONE_FORMATTING_GUIDE.md](./PHONE_FORMATTING_GUIDE.md)
**Phone Number Formatting Guide**

A comprehensive guide explaining how phone numbers are handled in the verification system, including automatic formatting, storage format, and verification best practices.

#### Usage Examples:
```bash
# Update with individual arguments
python update_resource_verification.py --id 6 --phone "(800) 752-6200" --email "test@example.com"

# Update with JSON config file
python update_resource_verification.py --id 6 --config verification_data.json

# Preview changes without saving
python update_resource_verification.py --id 6 --config verification_data.json --preview

# Show verification queue
python update_resource_verification.py --queue

# Use verification template
python update_resource_verification.py --id 6 --template verification_template.md

# Use filled template with config file
python update_resource_verification.py --id 6 --config filled_template.json
```

#### Target Audience:
- **AI Assistants** - Non-interactive operation for automated verification
- **Data Managers** - Batch verification updates
- **Quality Assurance** - Systematic resource updates

#### System Account:
The script uses the "Homeless AI" system account (`homeless_ai`) for all automated verification updates, providing clear attribution for AI-assisted changes.

#### Template Usage:
- **Empty Template**: Use `--template verification_template.md` to apply the standard template
- **Filled Template**: Use `--config filled_template.json` with verification notes to apply completed template
- **Template Replacement**: When using templates, existing verification notes are replaced (not appended)

#### Features:
- **Smart Prioritization** - Finds resources that need verification based on priority:
  1. Never verified (no last_verified_at)
  2. Expired verification (past verification_frequency_days)
  3. Lowest ID for systematic coverage
- **Complete Information Display** - Shows all resource data in organized sections
- **Verification Checklist** - Provides step-by-step verification guidance
- **Quick Commands** - Offers ready-to-use commands for next steps

#### Usage:
```bash
# From project root (recommended)
python find_next_verification.py

# From verification directory
cd docs/verification
python find_next_verification.py
```

#### Output Includes:
- **Basic Information** - ID, name, status, category, description
- **Contact Information** - Phone, email, website
- **Location Details** - Complete address information
- **Service Details** - Hours, eligibility, populations, cost, languages
- **Verification Status** - Last verified date, next due date, priority level
- **Verification Checklist** - Step-by-step verification guidance
- **Quick Commands** - Ready-to-use commands for data extraction and next steps

#### Target Audience:
- **Verifiers** - Quick access to next resource needing verification
- **Data Managers** - Systematic verification workflow
- **Quality Assurance** - Comprehensive resource information review

## Prerequisites

**⚠️ IMPORTANT: Virtual Environment Required**

Before using any verification tools, you MUST activate the virtual environment:

```bash
# From project root directory
source venv/bin/activate
```

All verification commands require the virtual environment to be active for proper Django database access and dependency management.

## Usage

### For New Users
1. **Activate virtual environment**: `source venv/bin/activate`
2. Start with `VERIFICATION.md` to understand the complete process
3. Use `find_next_verification.py` to find your first resource to verify
4. **⚠️ CRITICAL**: Always present changes for approval before implementing them
5. Use `update_resource_verification.py` to update the resource with verified information
6. Follow the step-by-step workflow for your first verification
7. Use the provided templates and scripts
8. Document your findings using the verification summary format

### For Experienced Users
1. **Activate virtual environment**: `source venv/bin/activate`
2. Use `find_next_verification.py` to quickly find the next resource needing verification
3. **⚠️ CRITICAL**: Always present changes for approval before implementing them
4. Use `update_resource_verification.py` for efficient resource updates
5. Use the quick reference commands in `VERIFICATION.md`
6. Follow the quality standards and verification requirements
7. Implement the maintenance schedule for ongoing quality
8. Contribute improvements to the process documentation

### For Administrators
1. **Activate virtual environment**: `source venv/bin/activate`
2. Use `find_next_verification.py` to monitor verification queue and priorities
3. Review the quality standards and success metrics
4. Implement the maintenance schedule
5. Monitor verification coverage and accuracy rates
6. Update the process based on feedback and results

## ⚠️ CRITICAL: APPROVAL REQUIRED

**BEFORE making any changes to resource records, you MUST:**

1. **Present a clear summary** of all proposed changes
2. **Request explicit approval** from stakeholders
3. **Wait for approval** before proceeding with implementation
4. **Document the approval** in verification notes

**This step is MANDATORY and cannot be skipped.**

See Step 7 in `VERIFICATION.md` for detailed approval process.

---

## Process Overview

The verification process follows these key principles:

1. **Systematic Approach** - Consistent methodology for all resources
2. **Multiple Sources** - Minimum 2 sources for each piece of information
3. **Field-by-Field Analysis** - Analyze each field for clarity and completeness
4. **Audit Trail** - Complete documentation of all changes
5. **Quality Standards** - Clear criteria for data accuracy and completeness
6. **Continuous Improvement** - Regular review and process updates

## Phone Number Formatting

**Important**: Phone numbers in the system use automatic display formatting:

- **Storage**: Phone numbers are stored as digits-only in the database
- **Display**: Phone numbers are automatically formatted for readability in templates
- **Verification**: Focus on verifying phone number accuracy, not formatting
- **Examples**: 
  - Input: "(877) 696-6775" → Storage: "8776966775" → Display: "(877) 696-6775"
  - Input: "877-696-6775" → Storage: "8776966775" → Display: "(877) 696-6775"

See the **Phone Number Formatting Standards** section in `VERIFICATION.md` for complete details.

## Related Documentation

- **Main README.md** - Project overview and setup
- **DATA_QUALITY_PROCESS.md** - General data quality guidelines
- **IMPLEMENTATION_TASKS.md** - Technical implementation details
- **SERVICE_AREA_ASSIGNMENT_WORKFLOW.md** - Geographic data management
- **find_next_verification.py** - Automated resource verification finder tool

## Contributing

When contributing to the verification process:

1. **Follow the established workflow** in `VERIFICATION.md`
2. **Document all changes** using the provided templates
3. **Test the process** with different resource types
4. **Update documentation** when process improvements are made
5. **Share lessons learned** to improve the overall process

## Support

For questions about the verification process:

1. **Review the documentation** in this folder
2. **Check the example implementation** in `VERIFICATION.md`
3. **Follow the troubleshooting steps** in the process guide
4. **Contact the data management team** for complex issues

---

**Last Updated**: August 2025  
**Maintained By**: Data Management Team  
**Next Review**: February 2026
