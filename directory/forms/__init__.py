"""
Directory Forms Package - Resource Directory Form Classes

This package contains all the Django form classes for the resource directory application,
organized into logical modules for better maintainability and code organization.

Forms are organized as follows:
    - resource_forms.py: ResourceForm for resource creation and editing
    - filter_forms.py: ResourceFilterForm for filtering and searching resources

This __init__.py file maintains backward compatibility by importing all forms
at the package level, so existing code can continue to use:
    from directory.forms import ResourceForm, ResourceFilterForm

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    # Backward compatible imports (recommended for existing code)
    from directory.forms import ResourceForm, ResourceFilterForm

    # Direct module imports (for new code)
    from directory.forms.resource_forms import ResourceForm
    from directory.forms.filter_forms import ResourceFilterForm
"""

# Import all forms for backward compatibility
from .filter_forms import ResourceFilterForm
from .resource_forms import ResourceForm

# Define __all__ for explicit exports
__all__ = [
    "ResourceForm",
    "ResourceFilterForm",
]
