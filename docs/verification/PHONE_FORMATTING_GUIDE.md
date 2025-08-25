# Phone Number Formatting Guide

## Overview
This guide explains how phone numbers are handled in the Homeless Resource Directory verification system. The system uses automatic display formatting while maintaining consistent storage format.

## How It Works

### Storage Format
- **Database Storage**: All phone numbers are stored as digits-only (e.g., "8776966775")
- **Automatic Normalization**: The Resource model automatically strips all non-digit characters during save
- **Validation**: Phone numbers must contain only digits (0-9)

### Display Format
- **Automatic Formatting**: Phone numbers are automatically formatted for display in all templates
- **Template Filter**: Uses `{{ phone|format_phone }}` filter for consistent formatting
- **Tel Links**: Automatically generates clickable `tel:` links for mobile devices

## Formatting Rules

### Standard US Phone Numbers
- **10 digits**: `(XXX) XXX-XXXX`
  - Example: "5551234567" → "(555) 123-4567"
- **11 digits starting with 1**: `(XXX) XXX-XXXX`
  - Example: "15551234567" → "(555) 123-4567"
- **Other formats**: Displayed as stored

### Examples
```
Input Format          → Storage Format    → Display Format
"(877) 696-6775"     → "8776966775"      → "(877) 696-6775"
"877-696-6775"       → "8776966775"      → "(877) 696-6775"
"877.696.6775"       → "8776966775"      → "(877) 696-6775"
"8776966775"         → "8776966775"      → "(877) 696-6775"
"1-877-696-6775"     → "18776966775"     → "(877) 696-6775"
```

## Verification Process

### What to Verify
- **Accuracy**: Verify the phone number is correct and working
- **Functionality**: Test that the number can be called
- **Display**: Confirm the number displays correctly in templates
- **Tel Links**: Verify clickable links work on mobile devices

### What NOT to Worry About
- **Formatting**: The system handles all formatting automatically
- **Storage Format**: You can input any format - the system normalizes it
- **Consistency**: All phone numbers are displayed consistently

## Implementation Details

### Template Filter
The `format_phone` filter is located in `/directory/templatetags/directory_extras.py`:

```python
@register.filter
def format_phone(phone: str) -> str:
    """Format phone number for display."""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone
```

### Model Normalization
The Resource model automatically normalizes phone numbers in the `save()` method:

```python
if self.phone:
    # Basic phone normalization (remove non-digits)
    self.phone = "".join(filter(str.isdigit, self.phone))
```

## Templates Using Phone Formatting

### Public Templates
- `/templates/directory/public_resource_detail.html`
- `/templates/directory/public_resource_list.html`

### Admin Templates
- `/templates/directory/resource_detail.html`
- `/templates/directory/archive_detail.html`

### Import Templates
- `/templates/importer/import_preview.html`

## Verification Scripts

### Updated Scripts
The following verification scripts now display formatted phone numbers:
- `find_next_verification.py`
- `update_resource_verification.py`

### Example Output
```
Phone: (877) 696-6775  # Instead of: 8776966775
```

## Testing Phone Formatting

### Manual Testing
```bash
# Test the template filter
python manage.py shell -c "from directory.templatetags.directory_extras import format_phone; print(format_phone('8776966775'))"

# Test template rendering
python manage.py shell -c "from django.template import Template, Context; template = Template('{% load directory_extras %}{{ phone|format_phone }}'); context = Context({'phone': '8776966775'}); print(template.render(context))"
```

### Verification Testing
```bash
# Test verification script formatting
python docs/verification/find_next_verification.py
```

## Troubleshooting

### Common Issues
1. **Phone not formatting**: Ensure template loads `directory_extras`
2. **Wrong format displayed**: Check phone number length and format
3. **Tel links not working**: Verify phone number contains only digits

### Debug Commands
```bash
# Check current phone format in database
python manage.py shell -c "from directory.models import Resource; r = Resource.objects.get(id=30); print('Raw phone:', repr(r.phone))"

# Test formatting with different inputs
python manage.py shell -c "from directory.templatetags.directory_extras import format_phone; test_numbers = ['5551234567', '15551234567', '1234567890']; [print(f'{num} -> {format_phone(num)}') for num in test_numbers]"
```

## Best Practices

### For Verifiers
1. **Focus on accuracy**: Verify the phone number is correct
2. **Test functionality**: Call the number to confirm it works
3. **Don't worry about format**: Input any format - system handles it
4. **Check display**: Verify the number displays correctly in templates

### For Developers
1. **Use the filter**: Always use `{{ phone|format_phone }}` in templates
2. **Load templatetags**: Ensure templates load `directory_extras`
3. **Test thoroughly**: Test with various phone number formats
4. **Document changes**: Update this guide when making changes

## Related Documentation
- [VERIFICATION.md](./VERIFICATION.md) - Complete verification process
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Quick verification commands
- [verification_template.md](./verification_template.md) - Verification template

---

**Last Updated**: January 2025  
**Maintained By**: Data Management Team
