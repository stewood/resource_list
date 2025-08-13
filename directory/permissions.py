"""
Custom permissions and permission helpers for the resource directory.
"""

from typing import List

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
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=role).exists()


def user_is_editor(user: User) -> bool:
    """Check if user is an Editor."""
    return user_has_role(user, "Editor")


def user_is_reviewer(user: User) -> bool:
    """Check if user is a Reviewer."""
    return user_has_role(user, "Reviewer")


def user_is_admin(user: User) -> bool:
    """Check if user is an Admin."""
    return user_has_role(user, "Admin")


def user_can_submit_for_review(user: User) -> bool:
    """Check if user can submit resources for review."""
    return user_is_editor(user) or user_is_reviewer(user) or user_is_admin(user)


def user_can_publish(user: User) -> bool:
    """Check if user can publish resources."""
    return user_is_reviewer(user) or user_is_admin(user)


def user_can_verify(user: User) -> bool:
    """Check if user can verify resources."""
    return user_is_reviewer(user) or user_is_admin(user)


def user_can_merge(user: User) -> bool:
    """Check if user can merge duplicate resources."""
    return user_is_reviewer(user) or user_is_admin(user)


def user_can_hard_delete(user: User) -> bool:
    """Check if user can permanently delete resources."""
    return user_is_admin(user)


def user_can_manage_users(user: User) -> bool:
    """Check if user can manage users and roles."""
    return user_is_admin(user)


def user_can_manage_taxonomies(user: User) -> bool:
    """Check if user can manage taxonomy categories."""
    return user_is_reviewer(user) or user_is_admin(user)


def require_role(role: str):
    """Decorator to require a specific role."""

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not user_has_role(request.user, role):
                raise PermissionDenied(f"Access denied. Requires {role} role.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_editor(view_func):
    """Decorator to require Editor role."""
    return require_role("Editor")(view_func)


def require_reviewer(view_func):
    """Decorator to require Reviewer role."""
    return require_role("Reviewer")(view_func)


def require_admin(view_func):
    """Decorator to require Admin role."""
    return require_role("Admin")(view_func)


def get_user_role(user: User) -> str:
    """Get the primary role of a user."""
    if not user.is_authenticated:
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
        ],
    }

    return role_permissions.get(role, [])
