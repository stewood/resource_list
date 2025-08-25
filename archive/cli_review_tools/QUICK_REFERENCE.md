# Quick Reference Card

## 🚀 Most Common Commands

### Find a Resource to Work On
```bash
python auto_update_random.py --show-only
```

### Update a Resource with Data File
```bash
python auto_update_random.py --data-file update_data.json --transition needs_review
```

### Update Specific Resource by ID
```bash
python update_resource_auto.py 123 --data-file update_data.json --transition needs_review
```

### Review Multiple Drafts
```bash
python review_multiple_drafts.py -c 5
```

### Interactive Workflow
```bash
python workflow.py
```

## 📋 3-Step Process

### Step 1: Identify
```bash
python auto_update_random.py --show-only
```

### Step 2: Research
- Search organization online
- Verify contact information
- Check hours and services
- Create JSON data file

### Step 3: Update
```bash
python auto_update_random.py --data-file verified_data.json --transition needs_review
```

## 📝 JSON Data Template

```json
{
  "name": "Organization Name",
  "description": "Description of services...",
  "source": "Verified from official website",
  "phone": "(555) 123-4567",
  "website": "https://www.organization.org",
  "city": "City Name",
  "state": "KY",
  "hours_of_operation": "Monday-Friday 9:00 AM-5:00 PM",
  "notes": "VERIFIED: All information confirmed on 2024-01-15"
}
```

## ✅ Required Fields for "Needs Review"

- ✅ City
- ✅ State  
- ✅ Description (min 20 chars)
- ✅ Source

## 🔍 Search Tips

- Start with official website
- Use: "[Org Name] [City, State] phone address hours"
- Verify phone numbers work
- Check website URLs
- Cross-reference multiple sources

## 📞 Contact Format Standards

- **Phone**: (555) 123-4567
- **Toll-Free**: 1-800-123-4567
- **Website**: https://www.organization.org
- **Hours**: "Monday-Friday 9:00 AM-5:00 PM"

---

**For complete documentation, see [PROCESS_GUIDE.md](PROCESS_GUIDE.md)**
