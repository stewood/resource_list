from django import template
from django.utils.safestring import mark_safe
import markdown2
import re

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def markdown(value):
    """Convert Markdown text to HTML."""
    if not value:
        return ""
    
    # Configure markdown2 with extensions for better formatting
    html = markdown2.markdown(
        value,
        extras=[
            'fenced-code-blocks',
            'tables',
            'code-friendly',
            'cuddled-lists',
            'header-ids',
            'break-on-newline'
        ]
    )
    return mark_safe(html)

@register.filter
def days_to_months(value):
    """Convert days to months (approximate)."""
    if not value:
        return ""
    try:
        days = float(value)
        months = days / 30.44  # Average days per month
        return f"{months:.1f}"
    except (ValueError, TypeError):
        return ""


@register.filter
def format_phone(phone: str) -> str:
    """Format phone number for display.
    
    Converts digits-only phone numbers to readable format:
    - 10 digits: (XXX) XXX-XXXX
    - 11 digits starting with 1: (XXX) XXX-XXXX
    - Other formats: Return as-is
    """
    if not phone:
        return ""
    
    # Remove all non-digits for processing
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return as-is if can't format
