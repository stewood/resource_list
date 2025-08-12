"""
Management command to set up user groups and permissions for the resource directory.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from directory.models import Resource, TaxonomyCategory


class Command(BaseCommand):
    """Set up user groups and permissions for the resource directory."""
    
    help = 'Create user groups (Editor, Reviewer, Admin) with appropriate permissions'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write('Setting up user groups and permissions...')
        
        # Get content types
        resource_ct = ContentType.objects.get_for_model(Resource)
        category_ct = ContentType.objects.get_for_model(TaxonomyCategory)
        user_ct = ContentType.objects.get_for_model(User)
        
        # Create or get groups
        editor_group, created = Group.objects.get_or_create(name='Editor')
        if created:
            self.stdout.write('✓ Created Editor group')
        else:
            self.stdout.write('✓ Editor group already exists')
        
        reviewer_group, created = Group.objects.get_or_create(name='Reviewer')
        if created:
            self.stdout.write('✓ Created Reviewer group')
        else:
            self.stdout.write('✓ Reviewer group already exists')
        
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write('✓ Created Admin group')
        else:
            self.stdout.write('✓ Admin group already exists')
        
        # Clear existing permissions
        editor_group.permissions.clear()
        reviewer_group.permissions.clear()
        admin_group.permissions.clear()
        
        # Get all permissions
        resource_permissions = Permission.objects.filter(content_type=resource_ct)
        category_permissions = Permission.objects.filter(content_type=category_ct)
        user_permissions = Permission.objects.filter(content_type=user_ct)
        
        # Editor permissions: create/edit resources, submit for review
        editor_permissions = [
            'add_resource',
            'change_resource',
            'view_resource',
            'view_taxonomycategory',
        ]
        
        # Reviewer permissions: verify, publish/unpublish, merge duplicates
        reviewer_permissions = [
            'add_resource',
            'change_resource',
            'view_resource',
            'view_taxonomycategory',
            'add_taxonomycategory',
            'change_taxonomycategory',
        ]
        
        # Admin permissions: manage users, taxonomies, rare hard deletes, system settings
        admin_permissions = [
            'add_resource',
            'change_resource',
            'delete_resource',
            'view_resource',
            'add_taxonomycategory',
            'change_taxonomycategory',
            'delete_taxonomycategory',
            'view_taxonomycategory',
            'add_user',
            'change_user',
            'delete_user',
            'view_user',
        ]
        
        # Assign permissions to groups
        self.stdout.write('\nAssigning permissions to Editor group:')
        self._assign_permissions(editor_group, editor_permissions, resource_ct, category_ct, user_ct)
        
        self.stdout.write('\nAssigning permissions to Reviewer group:')
        self._assign_permissions(reviewer_group, reviewer_permissions, resource_ct, category_ct, user_ct)
        
        self.stdout.write('\nAssigning permissions to Admin group:')
        self._assign_permissions(admin_group, admin_permissions, resource_ct, category_ct, user_ct)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up user groups and permissions')
        )
        
        # Display summary
        self.stdout.write('\nPermission Summary:')
        self.stdout.write(f'Editor: {editor_group.permissions.count()} permissions')
        self.stdout.write(f'Reviewer: {reviewer_group.permissions.count()} permissions')
        self.stdout.write(f'Admin: {admin_group.permissions.count()} permissions')
    
    def _assign_permissions(self, group, permission_names, resource_ct, category_ct, user_ct):
        """Assign permissions to a group."""
        for perm_name in permission_names:
            # Determine which content type this permission belongs to
            if perm_name.startswith('add_') or perm_name.startswith('change_') or perm_name.startswith('delete_') or perm_name.startswith('view_'):
                if 'resource' in perm_name:
                    ct = resource_ct
                    codename = perm_name.replace('resource_', '')
                elif 'taxonomycategory' in perm_name:
                    ct = category_ct
                    codename = perm_name.replace('taxonomycategory_', '')
                elif 'user' in perm_name:
                    ct = user_ct
                    codename = perm_name.replace('user_', '')
                else:
                    continue
            else:
                continue
            
            try:
                permission = Permission.objects.get(
                    content_type=ct,
                    codename=codename
                )
                group.permissions.add(permission)
                self.stdout.write(f'  ✓ Added {perm_name} to {group.name}')
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ✗ Permission {perm_name} not found')
                )
