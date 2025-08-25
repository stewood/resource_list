#!/usr/bin/env python3
"""
Resource Verification Update Script

⚠️  PREREQUISITE: VIRTUAL ENVIRONMENT REQUIRED ⚠️
Before running this script, activate the virtual environment:
    source venv/bin/activate

⚠️  CRITICAL: APPROVAL REQUIRED BEFORE USE ⚠️

This script provides a non-interactive way to update resource records during verification.
It includes safety features, verification tracking, and comprehensive field updates.

IMPORTANT: You MUST present changes for approval before using this script.
See VERIFICATION.md Step 8 for the approval process.

Usage:
    python update_resource_verification.py --id RESOURCE_ID --phone "(800) 123-4567" --email "test@example.com"
    python update_resource_verification.py --id RESOURCE_ID --config verification_data.json
    python update_resource_verification.py --queue
    python update_resource_verification.py --preview --id RESOURCE_ID --config verification_data.json

Author: Resource Directory Team
Created: 2025-01-15
"""

import os
import sys
import argparse
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import django

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource, TaxonomyCategory
from django.contrib.auth.models import User
from django.utils import timezone


class ResourceVerificationUpdater:
    """Non-interactive resource verification and update tool."""
    
    def __init__(self):
        self.resource = None
        self.changes = {}
        self.verification_notes = ""
        self.verification_frequency_days = 180  # Default 6 months
        self.preview_mode = False
        self.using_template = False
        
    def format_phone(self, phone: str) -> str:
        """Format phone number for readability."""
        if not phone:
            return ""
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return as-is if can't format
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email:
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_url(self, url: str) -> bool:
        """Basic URL validation."""
        if not url:
            return True
        pattern = r'^https?://.+'
        return bool(re.match(pattern, url))
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Resource]:
        """Get resource by ID."""
        try:
            return Resource.objects.get(id=resource_id, is_deleted=False, is_archived=False)
        except Resource.DoesNotExist:
            return None
    
    def show_verification_queue(self):
        """Show resources that need verification."""
        print("🔍 RESOURCES NEEDING VERIFICATION")
        print("=" * 50)
        
        # Find never verified resources
        never_verified = Resource.objects.filter(
            last_verified_at__isnull=True,
            status='published',
            is_deleted=False,
            is_archived=False
        ).order_by('id')[:10]
        
        if never_verified:
            print("\n📋 Never Verified (High Priority):")
            for resource in never_verified:
                print(f"  ID: {resource.id} - {resource.name}")
        
        # Find expired verifications
        now = timezone.now()
        expired_resources = []
        verified_resources = Resource.objects.filter(
            last_verified_at__isnull=False,
            status='published',
            is_deleted=False,
            is_archived=False
        )
        
        for resource in verified_resources:
            if resource.needs_verification:
                expired_resources.append(resource)
        
        if expired_resources:
            print("\n⏰ Expired Verification:")
            for resource in expired_resources[:10]:
                days_overdue = (now - resource.next_verification_date).days
                print(f"  ID: {resource.id} - {resource.name} ({days_overdue} days overdue)")
        
        if not never_verified and not expired_resources:
            print("✅ No resources need verification at this time!")
    
    def display_current_resource(self):
        """Display current resource information."""
        if not self.resource:
            return
        
        print("\n" + "=" * 80)
        print(f"CURRENT RESOURCE: {self.resource.name.upper()}")
        print("=" * 80)
        
        print(f"ID: {self.resource.id}")
        print(f"Status: {self.resource.status}")
        print(f"Category: {self.resource.category.name if self.resource.category else 'None'}")
        
        print("\n📞 CONTACT INFORMATION:")
        # Format phone for display
        phone_display = self.resource.phone
        if phone_display:
            phone_display = self.format_phone(phone_display)
        print(f"  Phone: {phone_display or 'Not provided'}")
        print(f"  Email: {self.resource.email or 'Not provided'}")
        print(f"  Website: {self.resource.website or 'Not provided'}")
        
        print("\n📍 LOCATION:")
        print(f"  Address: {self.resource.address1 or 'Not provided'}")
        if self.resource.address2:
            print(f"           {self.resource.address2}")
        print(f"  City: {self.resource.city or 'Not provided'}")
        print(f"  State: {self.resource.state or 'Not provided'}")
        print(f"  County: {self.resource.county or 'Not provided'}")
        print(f"  Postal Code: {self.resource.postal_code or 'Not provided'}")
        
        print("\n🛠️ SERVICE DETAILS:")
        print(f"  Hours: {self.resource.hours_of_operation or 'Not provided'}")
        print(f"  Eligibility: {self.resource.eligibility_requirements or 'Not provided'}")
        print(f"  Populations: {self.resource.populations_served or 'Not provided'}")
        print(f"  Cost: {self.resource.cost_information or 'Not provided'}")
        print(f"  Languages: {self.resource.languages_available or 'Not provided'}")
        
        print("\n✅ VERIFICATION STATUS:")
        if self.resource.last_verified_at:
            print(f"  Last Verified: {self.resource.last_verified_at.strftime('%B %d, %Y')}")
            print(f"  Verified By: {self.resource.last_verified_by.get_full_name() if self.resource.last_verified_by else 'Unknown'}")
            if self.resource.next_verification_date:
                print(f"  Next Due: {self.resource.next_verification_date.strftime('%B %d, %Y')}")
        else:
            print("  Last Verified: Never verified")
        
        print("=" * 80)
    
    def validate_field_value(self, field_name: str, value: str, field_type: str = "text") -> tuple[bool, str]:
        """Validate field value and return (is_valid, formatted_value)."""
        if not value:
            return True, ""
        
        # Validation
        if field_type == "phone":
            formatted = self.format_phone(value)
            return True, formatted
        elif field_type == "email" and not self.validate_email(value):
            return False, value
        elif field_type == "url" and not self.validate_url(value):
            return False, value
        
        return True, value
    
    def set_field_value(self, field_name: str, value: str, field_type: str = "text") -> bool:
        """Set a field value with validation."""
        if value is None:
            return True  # Skip if no value provided
        
        is_valid, formatted_value = self.validate_field_value(field_name, value, field_type)
        
        if not is_valid:
            print(f"❌ Invalid {field_name}: {value}")
            return False
        
        self.changes[field_name] = formatted_value
        return True
    
    def load_config_from_file(self, config_file: str) -> bool:
        """Load verification data from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load field updates
            field_mappings = {
                'phone': ('phone', 'phone'),
                'email': ('email', 'email'),
                'website': ('website', 'url'),
                'address1': ('address1', 'text'),
                'address2': ('address2', 'text'),
                'city': ('city', 'text'),
                'state': ('state', 'text'),
                'county': ('county', 'text'),
                'postal_code': ('postal_code', 'text'),
                'hours_of_operation': ('hours_of_operation', 'text'),
                'eligibility_requirements': ('eligibility_requirements', 'text'),
                'populations_served': ('populations_served', 'text'),
                'cost_information': ('cost_information', 'text'),
                'languages_available': ('languages_available', 'text'),
                'description': ('description', 'text'),
            }
            
            for config_key, (field_name, field_type) in field_mappings.items():
                if config_key in config:
                    if not self.set_field_value(field_name, config[config_key], field_type):
                        return False
            
            # Load verification notes
            if 'verification_notes' in config:
                self.verification_notes = config['verification_notes']
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            return False
    
    def set_verification_notes(self, notes: str):
        """Set verification notes."""
        self.verification_notes = notes
    
    def load_template(self, template_file: str) -> str:
        """Load verification template and return template content."""
        try:
            template_path = os.path.join(os.path.dirname(__file__), template_file)
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Template file not found: {template_file}")
            return ""
        except Exception as e:
            print(f"❌ Error loading template: {e}")
            return ""
    
    def generate_template_notes(self, template_content: str) -> str:
        """Generate verification notes from template."""
        if not template_content:
            return self.verification_notes
        
        # Replace template placeholders with actual data
        now = timezone.now()
        next_review = now + timedelta(days=self.verification_frequency_days)
        
        # Basic replacements
        template_content = template_content.replace("[Date]", now.strftime("%B %d, %Y"))
        template_content = template_content.replace("[Date + 6 months]", next_review.strftime("%B %d, %Y"))
        
        # Add a note about using the template
        template_note = f"\n\n--- TEMPLATE-BASED VERIFICATION {now.strftime('%Y-%m-%d %H:%M')} ---\n"
        template_note += "This verification was conducted using the standardized verification template.\n"
        template_note += "Please fill out the template sections above with specific verification findings.\n"
        
        return template_content + template_note
    
    def show_changes_summary(self):
        """Show summary of all changes."""
        has_field_changes = bool(self.changes)
        has_notes_changes = bool(self.verification_notes)
        
        if not has_field_changes and not has_notes_changes:
            print("\n✅ No changes to make!")
            return True
        
        print("\n📋 CHANGES SUMMARY")
        print("=" * 50)
        
        # Show field changes
        if has_field_changes:
            for field, new_value in self.changes.items():
                current_value = getattr(self.resource, field, "")
                print(f"\n{field.upper().replace('_', ' ')}:")
                print(f"  From: {current_value or 'Not provided'}")
                print(f"  To:   {new_value or 'Not provided'}")
        
        # Show verification notes changes
        if has_notes_changes:
            current_notes = self.resource.notes or ""
            print(f"\nVERIFICATION NOTES:")
            print(f"  Current: {len(current_notes)} characters")
            print(f"  New:     {len(self.verification_notes)} characters")
            if len(self.verification_notes) > 200:
                print(f"  Preview: {self.verification_notes[:200]}...")
            else:
                print(f"  Preview: {self.verification_notes}")
        
        if self.preview_mode:
            print("\n🔍 PREVIEW MODE - No changes will be saved")
            return False
        
        return True
    
    def save_changes(self):
        """Save changes to the database."""
        try:
            # Apply field changes
            for field, value in self.changes.items():
                setattr(self.resource, field, value)
            
            # Update verification tracking
            now = timezone.now()
            self.resource.last_verified_at = now
            
            # Try to get current user (you may need to adjust this based on your auth setup)
            try:
                current_user = User.objects.get(username='homeless_ai')  # Homeless AI system account
                self.resource.last_verified_by = current_user
            except User.DoesNotExist:
                try:
                    # Fallback to Stephen Woodard
                    current_user = User.objects.get(username='stewood')
                    self.resource.last_verified_by = current_user
                except User.DoesNotExist:
                    try:
                        # Fallback to csv_importer user
                        current_user = User.objects.get(username='csv_importer')
                        self.resource.last_verified_by = current_user
                    except User.DoesNotExist:
                        try:
                            # Fallback to admin user
                            current_user = User.objects.get(username='admin')
                            self.resource.last_verified_by = current_user
                        except User.DoesNotExist:
                            pass  # Leave as None if no user found
            
            # Update verification notes
            if self.verification_notes:
                # If using template, replace all verification notes
                # If not using template, append to existing notes
                if hasattr(self, 'using_template') and self.using_template:
                    self.resource.notes = self.verification_notes
                else:
                    current_notes = self.resource.notes or ""
                    verification_summary = f"\n\n--- VERIFICATION UPDATE {now.strftime('%Y-%m-%d %H:%M')} ---\n{self.verification_notes}"
                    self.resource.notes = current_notes + verification_summary
            
            # Next verification date is calculated automatically by the property
            
            self.resource.save()
            
            print("\n✅ Resource updated successfully!")
            print(f"   Next verification due: {self.resource.next_verification_date.strftime('%B %d, %Y')}")
            
            # Log changes
            self.log_changes()
            
        except Exception as e:
            print(f"\n❌ Error saving changes: {e}")
            return False
        
        return True
    
    def log_changes(self):
        """Log changes to verification log file."""
        log_file = os.path.join(os.path.dirname(__file__), "verification_log.txt")
        
        log_entry = f"""
=== VERIFICATION UPDATE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===
Resource ID: {self.resource.id}
Resource Name: {self.resource.name}
Changes Made: {len(self.changes)} fields updated
Fields Updated: {', '.join(self.changes.keys()) if self.changes else 'None'}
Verification Notes: {len(self.verification_notes)} characters
Next Verification: {self.resource.next_verification_date.strftime('%Y-%m-%d') if self.resource.next_verification_date else 'Not set'}
"""
        
        try:
            with open(log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def run(self, resource_id: int, **kwargs):
        """Main execution method."""
        print("🔄 RESOURCE VERIFICATION UPDATER")
        print("=" * 50)
        
        # Get resource
        self.resource = self.get_resource_by_id(resource_id)
        if not self.resource:
            print(f"❌ Resource with ID {resource_id} not found!")
            return False
        
        # Set preview mode if requested
        self.preview_mode = kwargs.get('preview', False)
        
        # Display current resource
        self.display_current_resource()
        
        # Load config file if provided
        if 'config_file' in kwargs and kwargs['config_file']:
            if not self.load_config_from_file(kwargs['config_file']):
                return False
            # If config file contains verification notes, treat as template replacement
            if self.verification_notes:
                self.using_template = True
        
        # Set individual fields if provided
        field_mappings = {
            'phone': ('phone', 'phone'),
            'email': ('email', 'email'),
            'website': ('website', 'url'),
            'address1': ('address1', 'text'),
            'address2': ('address2', 'text'),
            'city': ('city', 'text'),
            'state': ('state', 'text'),
            'county': ('county', 'text'),
            'postal_code': ('postal_code', 'text'),
            'hours_of_operation': ('hours_of_operation', 'text'),
            'eligibility_requirements': ('eligibility_requirements', 'text'),
            'populations_served': ('populations_served', 'text'),
            'cost_information': ('cost_information', 'text'),
            'languages_available': ('languages_available', 'text'),
            'description': ('description', 'text'),
        }
        
        for arg_name, (field_name, field_type) in field_mappings.items():
            if arg_name in kwargs and kwargs[arg_name] is not None:
                if not self.set_field_value(field_name, kwargs[arg_name], field_type):
                    return False
        
        # Set verification notes if provided
        if 'verification_notes' in kwargs and kwargs['verification_notes']:
            self.set_verification_notes(kwargs['verification_notes'])
        
        # Handle template if provided
        if 'template_file' in kwargs and kwargs['template_file']:
            template_content = self.load_template(kwargs['template_file'])
            if template_content:
                self.verification_notes = self.generate_template_notes(template_content)
                self.using_template = True
                print(f"📋 Loaded verification template: {kwargs['template_file']}")
        
        # Show summary
        if not self.show_changes_summary():
            return True  # Preview mode or no changes
        
        # Save changes (unless in preview mode)
        if not self.preview_mode:
            return self.save_changes()
        
        return True


def main():
    """Main function."""
    # Show approval warning
    print("⚠️  CRITICAL: APPROVAL REQUIRED BEFORE USE ⚠️")
    print("You MUST present changes for approval before using this script.")
    print("See VERIFICATION.md Step 7 for the approval process.")
    print("=" * 60)
    print()
    
    parser = argparse.ArgumentParser(description="Update resource verification information")
    parser.add_argument('--id', type=int, help='Resource ID to update')
    parser.add_argument('--queue', action='store_true', help='Show verification queue')
    parser.add_argument('--preview', action='store_true', help='Preview changes without saving')
    parser.add_argument('--config', type=str, help='JSON config file with verification data')
    parser.add_argument('--template', type=str, help='Verification template file to use')
    
    # Field arguments
    parser.add_argument('--phone', type=str, help='Phone number')
    parser.add_argument('--email', type=str, help='Email address')
    parser.add_argument('--website', type=str, help='Website URL')
    parser.add_argument('--address1', type=str, help='Address line 1')
    parser.add_argument('--address2', type=str, help='Address line 2')
    parser.add_argument('--city', type=str, help='City')
    parser.add_argument('--state', type=str, help='State')
    parser.add_argument('--county', type=str, help='County')
    parser.add_argument('--postal_code', type=str, help='Postal code')
    parser.add_argument('--hours_of_operation', type=str, help='Hours of operation')
    parser.add_argument('--eligibility_requirements', type=str, help='Eligibility requirements')
    parser.add_argument('--populations_served', type=str, help='Populations served')
    parser.add_argument('--cost_information', type=str, help='Cost information')
    parser.add_argument('--languages_available', type=str, help='Languages available')
    parser.add_argument('--description', type=str, help='Description')
    parser.add_argument('--verification_notes', type=str, help='Verification notes')
    
    args = parser.parse_args()
    
    updater = ResourceVerificationUpdater()
    
    if args.queue:
        updater.show_verification_queue()
        return
    
    if not args.id:
        print("❌ Resource ID is required for updates. Use --id RESOURCE_ID")
        return
    
    # Prepare kwargs for the run method
    kwargs = {
        'preview': args.preview,
        'config_file': args.config,
        'phone': args.phone,
        'email': args.email,
        'website': args.website,
        'address1': args.address1,
        'address2': args.address2,
        'city': args.city,
        'state': args.state,
        'county': args.county,
        'postal_code': args.postal_code,
        'hours_of_operation': args.hours_of_operation,
        'eligibility_requirements': args.eligibility_requirements,
        'populations_served': args.populations_served,
        'cost_information': args.cost_information,
        'languages_available': args.languages_available,
        'description': args.description,
        'verification_notes': args.verification_notes,
        'template_file': args.template,
    }
    
    # Remove None values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    success = updater.run(resource_id=args.id, **kwargs)
    
    if success:
        print("\n🎉 Verification update completed successfully!")
    else:
        print("\n❌ Verification update failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
