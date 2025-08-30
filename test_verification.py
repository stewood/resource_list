#!/usr/bin/env python3
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

# Get admin user
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

if admin_user:
    print(f'Using admin user: {admin_user.username}')
    
    # Create API client and login
    client = Client()
    client.force_login(admin_user)
    
    # Call the AI auto verification API
    response = client.post('/api/resources/62/ai-auto-verify/')
    
    print(f'Status Code: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print('Success!')
        print(f'Changes applied: {data.get("changes_applied", 0)}')
        print(f'New status: {data.get("new_status", "unknown")}')
        print(f'Report length: {len(data.get("verification_report", ""))}')
        print('\nFirst 500 chars of report:')
        print(data.get('verification_report', '')[:500])
    else:
        print(f'Error: {response.content.decode()}')
else:
    print('No admin user found')
