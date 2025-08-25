# Resource Update Process Guide

This document outlines the standardized process for updating resources in the Homeless Resource Directory, including search guidelines and update rules.

## 🎯 Overview

The resource update process follows a 3-step workflow:
1. **Identify** a draft resource to update
2. **Research** the organization to find verified information
3. **Update** the resource with verified data

## 📋 Step 1: Identify Record

### Command
```bash
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

#### 2. **Search Queries to Use**
```
"[Organization Name] [City, State] phone address hours"
"[Organization Name] contact information"
"[Organization Name] official website"
"[Organization Name] services hours of operation"
"[Organization Name] eligibility requirements"
```

#### 3. **Information to Verify**
- **Contact Information**: Phone, email, website
- **Location**: Full address, city, state, zip code
- **Hours**: Days and times of operation
- **Services**: What they actually provide
- **Eligibility**: Who can use their services
- **Cost**: Free, sliding scale, insurance accepted
- **Languages**: Languages spoken/available

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

## 📝 Step 3: Update Rules

### Required Fields for "Needs Review" Status

A resource must have these fields completed to move to "needs review" status:

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

### Category and Service Type Guidelines

#### **Categories**
- **Housing**: Emergency shelter, transitional housing, permanent housing
- **Food Assistance**: Food pantries, meal programs, SNAP assistance
- **Medical Care**: Health clinics, dental care, mental health services
- **Employment**: Job training, resume help, job placement
- **Legal Services**: Legal aid, court assistance, advocacy
- **Transportation**: Bus passes, rides, vehicle assistance
- **Hotlines**: Crisis hotlines, information hotlines
- **Other**: Services that don't fit other categories

#### **Service Types**
- **Emergency Services**: Available 24/7 or immediate response
- **Case Management**: Ongoing support and coordination
- **Referral Services**: Connecting to other resources
- **Direct Services**: Providing the service directly
- **Information**: Providing information and resources

## 🔧 Update Process

### 1. Create Update Data File

Create a JSON file with the verified information:

```json
{
  "name": "Updated Organization Name",
  "description": "Comprehensive description of services provided...",
  "source": "Verified from official website and phone call",
  "phone": "(555) 123-4567",
  "email": "contact@organization.org",
  "website": "https://www.organization.org",
  "address1": "123 Main Street",
  "city": "City Name",
  "state": "KY",
  "postal_code": "12345",
  "hours_of_operation": "Monday-Friday 9:00 AM-5:00 PM",
  "is_24_hour_service": false,
  "is_emergency_service": false,
  "eligibility_requirements": "Open to all residents of [County]",
  "populations_served": "Adults, families, children",
  "cost_information": "Free services available",
  "languages_available": "English, Spanish",
  "notes": "VERIFIED INFORMATION: All contact information verified on 2024-01-15. Organization provides [specific services]. Phone number confirmed working. Website verified current."
}
```

### 2. Run Update Command

```bash
# Update the resource
python auto_update_random.py --data-file update_data.json --transition needs_review
```

### 3. Verify Update

Check that:
- ✅ All required fields are filled
- ✅ Information is accurate and current
- ✅ Status changed to "needs review"
- ✅ Admin URL works and shows updated information

## 📊 Quality Checklist

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
- [ ] Notes include verification details
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

---

**Last Updated**: January 2024
**Version**: 1.0
**Maintained By**: Resource Directory Team
