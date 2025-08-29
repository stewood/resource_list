"""
Tests for permission system.
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from directory.permissions import (
    get_role_permissions,
    get_user_role,
    user_can_publish,
    user_can_submit_for_review,
    user_is_admin,
    user_is_editor,
    user_is_reviewer,
)


class PermissionTestCase(TestCase):
    """Test cases for permission system."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.editor = User.objects.create_user(
            username="editor",
            password="testpass123",
            first_name="Test",
            last_name="Editor",
        )

        self.reviewer = User.objects.create_user(
            username="reviewer",
            password="testpass123",
            first_name="Test",
            last_name="Reviewer",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            first_name="Test",
            last_name="Admin",
        )

        # Create groups
        self.editor_group = Group.objects.create(name="Editor")
        self.reviewer_group = Group.objects.create(name="Reviewer")
        self.admin_group = Group.objects.create(name="Admin")

        # Assign users to groups
        self.editor.groups.add(self.editor_group)
        self.reviewer.groups.add(self.reviewer_group)
        self.admin.groups.add(self.admin_group)

    def test_user_role_functions(self):
        """Test user role checking functions."""
        self.assertTrue(user_is_editor(self.editor))
        self.assertTrue(user_is_reviewer(self.reviewer))
        self.assertTrue(user_is_admin(self.admin))

        self.assertFalse(user_is_editor(self.user))
        self.assertFalse(user_is_reviewer(self.user))
        self.assertFalse(user_is_admin(self.user))

    def test_permission_functions(self):
        """Test permission checking functions."""
        # Submit for review permissions
        self.assertTrue(user_can_submit_for_review(self.editor))
        self.assertTrue(user_can_submit_for_review(self.reviewer))
        self.assertTrue(user_can_submit_for_review(self.admin))
        self.assertFalse(user_can_submit_for_review(self.user))

        # Publish permissions
        self.assertFalse(user_can_publish(self.editor))
        self.assertTrue(user_can_publish(self.reviewer))
        self.assertTrue(user_can_publish(self.admin))
        self.assertFalse(user_can_publish(self.user))

    def test_get_user_role(self):
        """Test get_user_role function."""
        self.assertEqual(get_user_role(self.editor), "Editor")
        self.assertEqual(get_user_role(self.reviewer), "Reviewer")
        self.assertEqual(get_user_role(self.admin), "Admin")
        self.assertEqual(get_user_role(self.user), "User")

    def test_get_role_permissions(self):
        """Test get_role_permissions function."""
        editor_perms = get_role_permissions("Editor")
        self.assertIn("Can add resource", editor_perms)
        self.assertIn("Can change resource", editor_perms)

        reviewer_perms = get_role_permissions("Reviewer")
        self.assertIn("Can add taxonomy category", reviewer_perms)

        admin_perms = get_role_permissions("Admin")
        self.assertIn("Can delete resource", admin_perms)
        self.assertIn("Can manage user", admin_perms)

    def test_superuser_permissions(self):
        """Test superuser permissions."""
        # Create superuser
        superuser = User.objects.create_superuser(
            username="superuser", email="super@example.com", password="testpass123"
        )

        # Superuser should have all permissions
        self.assertTrue(user_is_editor(superuser))
        self.assertTrue(user_is_reviewer(superuser))
        self.assertTrue(user_is_admin(superuser))
        self.assertTrue(user_can_submit_for_review(superuser))
        self.assertTrue(user_can_publish(superuser))
        self.assertEqual(get_user_role(superuser), "Superuser")

    def test_anonymous_user_permissions(self):
        """Test anonymous user permissions."""
        from django.contrib.auth.models import AnonymousUser

        anonymous = AnonymousUser()

        # Anonymous users should have no permissions
        self.assertFalse(user_is_editor(anonymous))
        self.assertFalse(user_is_reviewer(anonymous))
        self.assertFalse(user_is_admin(anonymous))
        self.assertFalse(user_can_submit_for_review(anonymous))
        self.assertFalse(user_can_publish(anonymous))
        self.assertEqual(get_user_role(anonymous), "Anonymous")

    def test_multiple_group_membership(self):
        """Test users with multiple group memberships."""
        # Add user to multiple groups
        self.user.groups.add(self.editor_group)
        self.user.groups.add(self.reviewer_group)

        # Should have editor permissions (first group)
        self.assertTrue(user_is_editor(self.user))
        self.assertTrue(user_can_submit_for_review(self.user))

        # Should not have reviewer permissions (role precedence)
        self.assertFalse(user_is_reviewer(self.user))
        self.assertFalse(user_can_publish(self.user))

    def test_role_precedence(self):
        """Test role precedence (Admin > Reviewer > Editor)."""
        # User with all roles should be identified as Admin
        self.admin.groups.add(self.editor_group)
        self.admin.groups.add(self.reviewer_group)

        self.assertEqual(get_user_role(self.admin), "Admin")

        # User with Reviewer and Editor roles should be identified as Reviewer
        self.reviewer.groups.add(self.editor_group)
        self.assertEqual(get_user_role(self.reviewer), "Reviewer")

    def test_empty_role_permissions(self):
        """Test get_role_permissions with invalid role."""
        perms = get_role_permissions("InvalidRole")
        self.assertEqual(perms, [])

    def test_user_without_groups(self):
        """Test user without any group memberships."""
        # User should have no special permissions
        self.assertFalse(user_is_editor(self.user))
        self.assertFalse(user_is_reviewer(self.user))
        self.assertFalse(user_is_admin(self.user))
        self.assertFalse(user_can_submit_for_review(self.user))
        self.assertFalse(user_can_publish(self.user))
        self.assertEqual(get_user_role(self.user), "User")

    def test_permission_consistency(self):
        """Test that permissions are consistent across functions."""
        # Editor permissions
        self.assertTrue(user_is_editor(self.editor))
        self.assertTrue(user_can_submit_for_review(self.editor))
        self.assertFalse(user_can_publish(self.editor))

        # Reviewer permissions
        self.assertTrue(user_is_reviewer(self.reviewer))
        self.assertTrue(user_can_submit_for_review(self.reviewer))
        self.assertTrue(user_can_publish(self.reviewer))

        # Admin permissions
        self.assertTrue(user_is_admin(self.admin))
        self.assertTrue(user_can_submit_for_review(self.admin))
        self.assertTrue(user_can_publish(self.admin))

    def test_group_creation_and_assignment(self):
        """Test group creation and user assignment."""
        # Create new group
        new_group = Group.objects.create(name="NewGroup")

        # Create new user
        new_user = User.objects.create_user(username="newuser", password="testpass123")

        # Assign user to group
        new_user.groups.add(new_group)

        # User should not have special permissions (group not recognized)
        self.assertFalse(user_is_editor(new_user))
        self.assertFalse(user_is_reviewer(new_user))
        self.assertFalse(user_is_admin(new_user))
        self.assertFalse(user_can_submit_for_review(new_user))
        self.assertFalse(user_can_publish(new_user))
        self.assertEqual(get_user_role(new_user), "User")

    def test_permission_functions_with_none_user(self):
        """Test permission functions with None user."""
        # All functions should handle None gracefully
        self.assertFalse(user_is_editor(None))
        self.assertFalse(user_is_reviewer(None))
        self.assertFalse(user_is_admin(None))
        self.assertFalse(user_can_submit_for_review(None))
        self.assertFalse(user_can_publish(None))
        self.assertEqual(get_user_role(None), "Anonymous")
