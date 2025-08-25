#!/usr/bin/env python3
"""
Check Notes Cleanup Script

This script identifies resources that need notes cleanup by examining the current database state
and looking for common issues like repetitive verification blocks, outdated information,
or inconsistent formatting.
"""

import os
import sys
import django
import re
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource
from django.contrib.auth.models import User


def check_notes_issues(notes):
    """Check for common issues in notes field."""
    if not notes:
        return []
    
    issues = []
    
    # Check for repetitive verification blocks
    verification_patterns = [
        r'VERIFIED:.*?(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',
        r'Last verified:.*?(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',
        r'Verified on:.*?(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',
    ]
    
    for pattern in verification_patterns:
        matches = re.findall(pattern, notes, re.IGNORECASE)
        if len(matches) > 1:
            issues.append(f"Multiple verification dates found: {matches}")
    
    # Check for repetitive text blocks
    repetitive_patterns = [
        r'(VERIFIED:.*?)(?=VERIFIED:)',
        r'(Last verified:.*?)(?=Last verified:)',
        r'(Verified on:.*?)(?=Verified on:)',
    ]
    
    for pattern in repetitive_patterns:
        matches = re.findall(pattern, notes, re.IGNORECASE | re.DOTALL)
        if len(matches) > 1:
            issues.append(f"Repetitive verification blocks found: {len(matches)} instances")
    
    # Check for outdated verification dates (older than 1 year)
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, notes)
        for match in matches:
            if len(match) == 3:
                if len(match[0]) == 4:  # YYYY-MM-DD format
                    year, month, day = match
                else:  # MM/DD/YYYY format
                    month, day, year = match
                
                try:
                    year = int(year)
                    if year < 2023:  # Older than 2023
                        issues.append(f"Outdated verification date: {year}")
                except ValueError:
                    pass
    
    # Check for inconsistent formatting
    if notes.count('\n\n\n') > 2:
        issues.append("Excessive line breaks")
    
    if len(notes) > 1000:
        issues.append("Notes too long (over 1000 characters)")
    
    # Check for common problematic patterns
    problematic_patterns = [
        r'VERIFIED:.*?VERIFIED:',  # Double verification
        r'Last verified:.*?Last verified:',  # Double last verified
        r'Verified on:.*?Verified on:',  # Double verified on
        r'This is the main regional office.*?This is the main regional office',  # Repetitive descriptions
        r'Payment is based on ability to pay.*?Payment is based on ability to pay',  # Repetitive payment info
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, notes, re.IGNORECASE | re.DOTALL):
            issues.append(f"Repetitive content found: {pattern[:50]}...")
    
    # Check for very short or very long notes
    if len(notes.strip()) < 10:
        issues.append("Notes too short (less than 10 characters)")
    
    if len(notes) > 2000:
        issues.append("Notes extremely long (over 2000 characters)")
    
    return issues


def find_resources_needing_cleanup():
    """Find resources that need notes cleanup."""
    resources = Resource.objects.filter(is_deleted=False).order_by('id')
    
    resources_needing_cleanup = []
    
    for resource in resources:
        issues = check_notes_issues(resource.notes)
        
        if issues:
            resources_needing_cleanup.append({
                'id': resource.id,
                'name': resource.name,
                'status': resource.status,
                'notes': resource.notes,
                'issues': issues,
                'notes_length': len(resource.notes) if resource.notes else 0
            })
    
    return resources_needing_cleanup


def display_cleanup_candidates(resources):
    """Display resources that need cleanup."""
    if not resources:
        print("✅ No resources found that need notes cleanup!")
        return
    
    print(f"🔍 Found {len(resources)} resources that need notes cleanup:\n")
    
    for i, resource in enumerate(resources, 1):
        print(f"{i}. ID {resource['id']}: {resource['name']}")
        print(f"   Status: {resource['status']}")
        print(f"   Notes Length: {resource['notes_length']} characters")
        print(f"   Issues: {', '.join(resource['issues'])}")
        
        # Show first 200 characters of notes
        notes_preview = resource['notes'][:200] + "..." if len(resource['notes']) > 200 else resource['notes']
        print(f"   Notes Preview: {notes_preview}")
        print()


def show_database_summary():
    """Show a summary of the current database state."""
    total_resources = Resource.objects.filter(is_deleted=False).count()
    archived_resources = Resource.objects.filter(is_archived=True, is_deleted=False).count()
    active_resources = total_resources - archived_resources
    
    # Count by status
    status_counts = {}
    for status in ['draft', 'needs_review', 'published']:
        count = Resource.objects.filter(status=status, is_deleted=False).count()
        status_counts[status] = count
    
    # Count resources with notes
    resources_with_notes = Resource.objects.filter(notes__isnull=False, notes__gt='', is_deleted=False).count()
    
    print(f"📊 Database Summary:")
    print(f"   Total resources: {total_resources}")
    print(f"   Active resources: {active_resources}")
    print(f"   Archived resources: {archived_resources}")
    print(f"   Resources with notes: {resources_with_notes}")
    print(f"   By status:")
    for status, count in status_counts.items():
        print(f"     {status}: {count}")
    print()


def show_sample_notes():
    """Show a sample of resources with notes to understand current state."""
    resources_with_notes = Resource.objects.filter(
        notes__isnull=False, 
        notes__gt='', 
        is_deleted=False
    ).order_by('id')[:10]
    
    print(f"📝 Sample of resources with notes (first 10):")
    for i, resource in enumerate(resources_with_notes, 1):
        notes_preview = resource.notes[:150] + "..." if len(resource.notes) > 150 else resource.notes
        print(f"{i}. ID {resource.id}: {resource.name}")
        print(f"   Status: {resource.status}")
        print(f"   Notes: {notes_preview}")
        print()


def main():
    """Main function."""
    print("🔍 Checking for resources that need notes cleanup...\n")
    
    # Show database summary first
    show_database_summary()
    
    # Show sample of notes
    show_sample_notes()
    
    print("-" * 60)
    
    resources_needing_cleanup = find_resources_needing_cleanup()
    display_cleanup_candidates(resources_needing_cleanup)
    
    if resources_needing_cleanup:
        print(f"\n📊 Summary:")
        print(f"   Total resources checked: {Resource.objects.filter(is_deleted=False).count()}")
        print(f"   Resources needing cleanup: {len(resources_needing_cleanup)}")
        
        # Group by status
        status_counts = {}
        for resource in resources_needing_cleanup:
            status = resource['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"   By status:")
        for status, count in status_counts.items():
            print(f"     {status}: {count}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Review the identified resources")
        print(f"   2. Use update_resource_noninteractive.py to clean up notes")
        print(f"   3. Consider creating a batch update script for similar issues")
    else:
        print(f"\n🎉 All resources appear to have clean notes!")


if __name__ == "__main__":
    main()
