"""
Django management command to find duplicate resources.

This command identifies potential duplicates using multiple criteria:
- Exact name matches
- Similar names (fuzzy matching)
- Same phone numbers
- Same addresses
- Same websites
- Same email addresses

Usage:
    python manage.py find_duplicates
    python manage.py find_duplicates --confidence=high
    python manage.py find_duplicates --show-details
    python manage.py find_duplicates --export-csv
"""

import csv
from typing import Any, Dict, List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from directory.models import Resource
from directory.utils import DuplicateDetector


class Command(BaseCommand):
    help = 'Find duplicate resources in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confidence',
            choices=['high', 'medium', 'low', 'all'],
            default='all',
            help='Confidence level for duplicate detection (default: all)'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed information about each duplicate'
        )
        parser.add_argument(
            '--export-csv',
            action='store_true',
            help='Export duplicate information to CSV file'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.8,
            help='Similarity threshold for fuzzy matching (default: 0.8)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting duplicate detection...')
        )
        
        detector = DuplicateDetector()
        results = detector.get_duplicate_summary()
        
        # Print summary
        self.print_summary(results['summary'])
        
        # Print detailed results based on confidence level
        confidence = options['confidence']
        show_details = options['show_details']
        
        if confidence in ['high', 'all']:
            self.print_exact_duplicates(results['exact_name_duplicates'], show_details)
            self.print_contact_duplicates(results['contact_duplicates'], show_details)
        
        if confidence in ['medium', 'all']:
            self.print_phone_duplicates(results['phone_duplicates'], show_details)
            self.print_website_duplicates(results['website_duplicates'], show_details)
            self.print_email_duplicates(results['email_duplicates'], show_details)
        
        if confidence in ['low', 'all']:
            self.print_fuzzy_duplicates(results['fuzzy_duplicates'], show_details)
            self.print_address_duplicates(results['address_duplicates'], show_details)
        
        # Export to CSV if requested
        if options['export_csv']:
            self.export_to_csv(results, options['threshold'])

    def print_summary(self, summary: Dict[str, int]):
        """Print summary of duplicate findings."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 DUPLICATE DETECTION SUMMARY'))
        self.stdout.write('='*60)
        
        total_duplicates = (
            summary['exact_name_groups'] + 
            summary['phone_groups'] + 
            summary['website_groups'] + 
            summary['email_groups'] + 
            summary['address_groups'] + 
            summary['fuzzy_pairs'] + 
            summary['contact_pairs']
        )
        
        self.stdout.write(f"🔍 Total duplicate groups/pairs found: {total_duplicates}")
        self.stdout.write(f"📝 Exact name duplicates: {summary['exact_name_groups']} groups")
        self.stdout.write(f"📞 Phone duplicates: {summary['phone_groups']} groups")
        self.stdout.write(f"🌐 Website duplicates: {summary['website_groups']} groups")
        self.stdout.write(f"📧 Email duplicates: {summary['email_groups']} groups")
        self.stdout.write(f"📍 Address duplicates: {summary['address_groups']} groups")
        self.stdout.write(f"🔍 Fuzzy name duplicates: {summary['fuzzy_pairs']} pairs")
        self.stdout.write(f"📞 Contact duplicates: {summary['contact_pairs']} pairs")

    def print_exact_duplicates(self, duplicates: Dict[str, List[Resource]], show_details: bool):
        """Print exact name duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🔴 HIGH CONFIDENCE: Exact Name Duplicates'))
        self.stdout.write('-'*60)
        
        for name, resources in duplicates.items():
            self.stdout.write(f"\n📝 Name: {name}")
            self.stdout.write(f"   Found {len(resources)} resources:")
            
            for resource in resources:
                self.stdout.write(f"   - ID: {resource.id} | Status: {resource.status} | Created: {resource.created_at.date()}")
                if show_details:
                    self.stdout.write(f"     Phone: {resource.phone or 'N/A'}")
                    self.stdout.write(f"     Email: {resource.email or 'N/A'}")
                    self.stdout.write(f"     Address: {resource.address1 or 'N/A'}, {resource.city or 'N/A'}, {resource.state or 'N/A'}")

    def print_contact_duplicates(self, duplicates: List[Tuple[Resource, Resource, str]], show_details: bool):
        """Print contact duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🔴 HIGH CONFIDENCE: Contact Information Duplicates'))
        self.stdout.write('-'*60)
        
        for resource1, resource2, contact_type in duplicates:
            self.stdout.write(f"\n📞 {contact_type.upper()} Duplicate:")
            self.stdout.write(f"   Resource 1: {resource1.name} (ID: {resource1.id})")
            self.stdout.write(f"   Resource 2: {resource2.name} (ID: {resource2.id})")
            
            if show_details:
                if contact_type == 'phone':
                    self.stdout.write(f"   Shared Phone: {resource1.phone}")
                elif contact_type == 'email':
                    self.stdout.write(f"   Shared Email: {resource1.email}")
                elif contact_type == 'website':
                    self.stdout.write(f"   Shared Website: {resource1.website}")

    def print_phone_duplicates(self, duplicates: Dict[str, List[Resource]], show_details: bool):
        """Print phone duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🟡 MEDIUM CONFIDENCE: Phone Number Duplicates'))
        self.stdout.write('-'*60)
        
        for phone, resources in duplicates.items():
            self.stdout.write(f"\n📞 Phone: {phone}")
            self.stdout.write(f"   Found {len(resources)} resources:")
            
            for resource in resources:
                self.stdout.write(f"   - {resource.name} (ID: {resource.id})")
                if show_details:
                    self.stdout.write(f"     Status: {resource.status} | Created: {resource.created_at.date()}")

    def print_website_duplicates(self, duplicates: Dict[str, List[Resource]], show_details: bool):
        """Print website duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🟡 MEDIUM CONFIDENCE: Website Duplicates'))
        self.stdout.write('-'*60)
        
        for website, resources in duplicates.items():
            self.stdout.write(f"\n🌐 Website: {website}")
            self.stdout.write(f"   Found {len(resources)} resources:")
            
            for resource in resources:
                self.stdout.write(f"   - {resource.name} (ID: {resource.id})")
                if show_details:
                    self.stdout.write(f"     Status: {resource.status} | Created: {resource.created_at.date()}")

    def print_email_duplicates(self, duplicates: Dict[str, List[Resource]], show_details: bool):
        """Print email duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🟡 MEDIUM CONFIDENCE: Email Duplicates'))
        self.stdout.write('-'*60)
        
        for email, resources in duplicates.items():
            self.stdout.write(f"\n📧 Email: {email}")
            self.stdout.write(f"   Found {len(resources)} resources:")
            
            for resource in resources:
                self.stdout.write(f"   - {resource.name} (ID: {resource.id})")
                if show_details:
                    self.stdout.write(f"     Status: {resource.status} | Created: {resource.created_at.date()}")

    def print_fuzzy_duplicates(self, duplicates: List[Tuple[Resource, Resource, float]], show_details: bool):
        """Print fuzzy name duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🟢 LOW CONFIDENCE: Fuzzy Name Duplicates'))
        self.stdout.write('-'*60)
        
        for resource1, resource2, similarity in duplicates:
            self.stdout.write(f"\n🔍 Similarity: {similarity:.2f}")
            self.stdout.write(f"   Resource 1: {resource1.name} (ID: {resource1.id})")
            self.stdout.write(f"   Resource 2: {resource2.name} (ID: {resource2.id})")
            
            if show_details:
                self.stdout.write(f"   Phone 1: {resource1.phone or 'N/A'}")
                self.stdout.write(f"   Phone 2: {resource2.phone or 'N/A'}")

    def print_address_duplicates(self, duplicates: Dict[str, List[Resource]], show_details: bool):
        """Print address duplicates."""
        if not duplicates:
            return
        
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(self.style.WARNING('🟢 LOW CONFIDENCE: Address Duplicates'))
        self.stdout.write('-'*60)
        
        for address, resources in duplicates.items():
            self.stdout.write(f"\n📍 Address: {address}")
            self.stdout.write(f"   Found {len(resources)} resources:")
            
            for resource in resources:
                self.stdout.write(f"   - {resource.name} (ID: {resource.id})")
                if show_details:
                    self.stdout.write(f"     Status: {resource.status} | Created: {resource.created_at.date()}")

    def export_to_csv(self, results: Dict[str, Any], threshold: float):
        """Export duplicate information to CSV file."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'duplicates_report_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Duplicate Type', 'Confidence', 'Resource 1 ID', 'Resource 1 Name', 
                'Resource 1 Phone', 'Resource 1 Email', 'Resource 1 Website',
                'Resource 2 ID', 'Resource 2 Name', 'Resource 2 Phone', 
                'Resource 2 Email', 'Resource 2 Website', 'Similarity/Match Info'
            ])
            
            # Export exact name duplicates
            for name, resources in results['exact_name_duplicates'].items():
                for i in range(len(resources)):
                    for j in range(i+1, len(resources)):
                        writer.writerow([
                            'Exact Name', 'High', 
                            resources[i].id, resources[i].name, resources[i].phone, 
                            resources[i].email, resources[i].website,
                            resources[j].id, resources[j].name, resources[j].phone, 
                            resources[j].email, resources[j].website,
                            f"Exact name match: {name}"
                        ])
            
            # Export contact duplicates
            for resource1, resource2, contact_type in results['contact_duplicates']:
                writer.writerow([
                    'Contact Info', 'High',
                    resource1.id, resource1.name, resource1.phone, 
                    resource1.email, resource1.website,
                    resource2.id, resource2.name, resource2.phone, 
                    resource2.email, resource2.website,
                    f"Same {contact_type}"
                ])
            
            # Export fuzzy duplicates
            for resource1, resource2, similarity in results['fuzzy_duplicates']:
                if similarity >= threshold:
                    writer.writerow([
                        'Fuzzy Name', 'Low',
                        resource1.id, resource1.name, resource1.phone, 
                        resource1.email, resource1.website,
                        resource2.id, resource2.name, resource2.phone, 
                        resource2.email, resource2.website,
                        f"Similarity: {similarity:.2f}"
                    ])
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📄 Duplicate report exported to: {filename}')
        )
