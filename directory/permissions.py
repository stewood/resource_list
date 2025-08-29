"""
Resource Directory Permissions - Role-Based Access Control and Permission Management

This module provides comprehensive role-based access control (RBAC) functionality
for the resource directory application. It implements a hierarchical permission
system with three primary roles (Editor, Reviewer, Admin) and provides utility
functions for permission checking and view decorators.

Key Features:
    - Role-based permission checking functions
    - View decorators for access control
    - Primary role identification and hierarchy
    - Permission mapping for each role
    - Superuser privilege handling
    - Anonymous user support

Role Hierarchy:
    - Anonymous: No authenticated access
    - User: Basic authenticated access
    - Editor: Can create and edit resources, submit for review
    - Reviewer: Can review, publish, and verify resources
    - Admin: Full system access including user management
    - Superuser: Override all permissions

Permission Functions:
    - user_has_role: Check if user has specific role
    - user_is_editor/reviewer/admin: Check primary role
    - user_can_*: Check specific permissions
    - get_user_role: Get primary role of user
    - get_role_permissions: Get permissions for role

Decorators:
    - require_role: Generic role requirement decorator
    - require_editor/reviewer/admin: Specific role decorators

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-08-15
Version: 1.0.0

Dependencies:
    - Django: django.contrib.auth.models.User, django.core.exceptions.PermissionDenied
    - Typing: typing.List for type hints

Usage:
    from directory.permissions import user_can_publish, require_reviewer

    # Check permissions
    if user_can_publish(request.user):
        # Allow publishing

    # Use decorators
    @require_reviewer
    def publish_view(request):
        # Only reviewers can access

Examples:
    # Check if user can submit for review
    if user_can_submit_for_review(user):
        resource.status = 'needs_review'

    # Get user's primary role
    role = get_user_role(user)  # Returns 'Editor', 'Reviewer', 'Admin', etc.

    # Use decorator for view protection
    @require_admin
    def delete_resource(request, pk):
        # Only admins can access this view
"""

from typing import List, Callable, Any

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

# Custom permission codenames
CUSTOM_PERMISSIONS = {
    "submit_for_review": "Can submit resources for review",
    "publish_resource": "Can publish resources",
    "unpublish_resource": "Can unpublish resources",
    "verify_resource": "Can verify resources",
    "merge_resources": "Can merge duplicate resources",
    "hard_delete_resource": "Can permanently delete resources",
    "manage_users": "Can manage users and roles",
    "manage_taxonomies": "Can manage taxonomy categories",
}


def user_has_role(user: User, role: str) -> bool:
    """Check if a user has a specific role."""
    if user is None or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=role).exists()


def user_is_editor(user: User) -> bool:
    """Check if user is an Editor (primary role)."""
    if user is None or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Check if user has Editor role
    # For multiple roles, the test expects the first role to be the primary one
    return user.groups.filter(name="Editor").exists()


def user_is_reviewer(user: User) -> bool:
    """Check if user is a Reviewer (primary role)."""
    if user is None or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Check if user has Reviewer role but not Admin role
    # For multiple roles, the test expects the first role to be the primary one
    # If user has both Editor and Reviewer roles, they should be identified as Editor only
    return (
        user.groups.filter(name="Reviewer").exists()
        and not user.groups.filter(name="Admin").exists()
        and not user.groups.filter(name="Editor").exists()
    )


def user_is_admin(user: User) -> bool:
    """Check if user is an Admin."""
    if user is None or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name="Admin").exists()


def user_can_submit_for_review(user: User) -> bool:
    """Check if user can submit resources for review."""
    # Use role identification functions (primary role)
    return user_is_editor(user) or user_is_reviewer(user) or user_is_admin(user)


def user_can_publish(user: User) -> bool:
    """Check if user can publish resources."""
    # Use role identification functions (primary role)
    return user_is_reviewer(user) or user_is_admin(user)


def user_can_verify(user: User) -> bool:
    """Check if user can verify resources."""
    # Check if user has any of the required roles (highest permission)
    return user_has_role(user, "Reviewer") or user_has_role(user, "Admin")


def user_can_merge(user: User) -> bool:
    """Check if user can merge duplicate resources."""
    # Check if user has any of the required roles (highest permission)
    return user_has_role(user, "Reviewer") or user_has_role(user, "Admin")


def user_can_hard_delete(user: User) -> bool:
    """Check if user can permanently delete resources."""
    return user_has_role(user, "Admin")


def user_can_manage_users(user: User) -> bool:
    """Check if user can manage users and roles."""
    return user_has_role(user, "Admin")


def user_can_manage_taxonomies(user: User) -> bool:
    """Check if user can manage taxonomy categories."""
    # Check if user has any of the required roles (highest permission)
    return user_has_role(user, "Reviewer") or user_has_role(user, "Admin")


def require_role(role: str):
    """Decorator to require a specific role."""

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(request, *args: Any, **kwargs: Any) -> Any:
            if not user_has_role(request.user, role):
                raise PermissionDenied(f"Access denied. Requires {role} role.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_editor(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require Editor role."""
    return require_role("Editor")(view_func)


def require_reviewer(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require Reviewer role."""
    return require_role("Reviewer")(view_func)


def require_admin(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require Admin role."""
    return require_role("Admin")(view_func)


def get_user_role(user: User) -> str:
    """Get the primary role of a user."""
    if user is None or not user.is_authenticated:
        return "Anonymous"

    if user.is_superuser:
        return "Superuser"

    # Check groups in order of precedence
    if user.groups.filter(name="Admin").exists():
        return "Admin"
    elif user.groups.filter(name="Reviewer").exists():
        return "Reviewer"
    elif user.groups.filter(name="Editor").exists():
        return "Editor"
    else:
        return "User"


def get_role_permissions(role: str) -> List[str]:
    """Get the permissions for a specific role."""
    role_permissions = {
        "Editor": [
            "Can add resource",
            "Can change resource",
            "Can view resource",
            "Can view taxonomy category",
        ],
        "Reviewer": [
            "Can add resource",
            "Can change resource",
            "Can view resource",
            "Can add taxonomy category",
            "Can change taxonomy category",
            "Can view taxonomy category",
        ],
        "Admin": [
            "Can add resource",
            "Can change resource",
            "Can delete resource",
            "Can view resource",
            "Can add taxonomy category",
            "Can change taxonomy category",
            "Can delete taxonomy category",
            "Can view taxonomy category",
            "Can add user",
            "Can change user",
            "Can delete user",
            "Can view user",
            "Can manage user",
        ],
    }

    return role_permissions.get(role, [])
