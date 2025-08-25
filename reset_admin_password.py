#!/usr/bin/env python3
"""
Reset admin password script
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.development_settings')
django.setup()

from django.contrib.auth.models import User

# Reset admin password
try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin')
    admin.save()
    print("✅ Admin password reset successfully!")
    print("Username: admin")
    print("Password: admin")
except User.DoesNotExist:
    print("❌ Admin user not found. Creating new admin user...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Admin user created successfully!")
    print("Username: admin")
    print("Password: admin")
except Exception as e:
    print(f"❌ Error: {e}")
