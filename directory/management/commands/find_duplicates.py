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
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from directory.models import Resource


class DuplicateDetector:
    """Detect duplicates in resources using multiple criteria."""

    def __init__(self):
        self.resources = Resource.objects.filter(is_archived=False, is_deleted=False)
        self.duplicates = defaultdict(list)
        self.processed_ids: Set[int] = set()

    def normalize_string(self, text: str) -> str:
        """Normalize string for comparison."""
        if not text:
            return ""
        # Remove common variations and normalize
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        if not phone:
            return ""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        # Return last 10 digits (most US numbers)
        return digits[-10:] if len(digits) >= 10 else digits

    def normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        address = self.normalize_string(address)
        # Remove common address variations
        address = re.sub(r'\b(st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive)\b', '', address)
        return address.strip()

    def similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()

    def find_exact_duplicates(self) -> Dict[str, List[Resource]]:
        """Find resources with exact name matches."""
        name_groups = defaultdict(list)
        
        for resource in self.resources:
            normalized_name = self.normalize_string(resource.name)
            if normalized_name:
                name_groups[normalized_name].append(resource)
        
        return {name: resources for name, resources in name_groups.items() if len(resources) > 1}

    def find_phone_duplicates(self) -> Dict[str, List[Resource]]:
        """Find resources with same phone numbers."""
        phone_groups = defaultdict(list)
        
        for resource in self.resources:
            if resource.phone:
                normalized_phone = self.normalize_phone(resource.phone)
                if normalized_phone:
                    phone_groups[normalized_phone].append(resource)
        
        return {phone: resources for phone, resources in phone_groups.items() if len(resources) > 1}

    def find_website_duplicates(self) -> Dict[str, List[Resource]]:
        """Find resources with same websites."""
        website_groups = defaultdict(list)
        
        for resource in self.resources:
            if resource.website:
                # Normalize website URL
                website = resource.website.lower().strip()
                if website.startswith('http://'):
                    website = website[7:]
                elif website.startswith('https://'):
                    website = website[8:]
                if website.startswith('www.'):
                    website = website[4:]
                website_groups[website].append(resource)
        
        return {website: resources for website, resources in website_groups.items() if len(resources) > 1}

    def find_email_duplicates(self) -> Dict[str, List[Resource]]:
        """Find resources with same email addresses."""
        email_groups = defaultdict(list)
        
        for resource in self.resources:
            if resource.email:
                email = resource.email.lower().strip()
                email_groups[email].append(resource)
        
        return {email: resources for email, resources in email_groups.items() if len(resources) > 1}

    def find_address_duplicates(self) -> Dict[str, List[Resource]]:
        """Find resources with same addresses."""
        address_groups = defaultdict(list)
        
        for resource in self.resources:
            if resource.address1 and resource.city and resource.state:
                # Create a composite address key
                address_key = f"{self.normalize_address(resource.address1)}|{self.normalize_string(resource.city)}|{resource.state.upper()}"
                address_groups[address_key].append(resource)
        
        return {address: resources for address, resources in address_groups.items() if len(resources) > 1}

    def find_fuzzy_name_duplicates(self, threshold: float = 0.8) -> List[Tuple[Resource, Resource, float]]:
        """Find resources with similar names using fuzzy matching."""
        fuzzy_duplicates = []
        processed_pairs = set()
        
        resources_list = list(self.resources)
        
        for i, resource1 in enumerate(resources_list):
            for j, resource2 in enumerate(resources_list[i+1:], i+1):
                if resource1.id == resource2.id:
                    continue
                
                pair_key = tuple(sorted([resource1.id, resource2.id]))
                if pair_key in processed_pairs:
                    continue
                
                normalized_name1 = self.normalize_string(resource1.name)
                normalized_name2 = self.normalize_string(resource2.name)
                
                if normalized_name1 and normalized_name2:
                    similarity = self.similarity_score(normalized_name1, normalized_name2)
                    if similarity >= threshold:
                        fuzzy_duplicates.append((resource1, resource2, similarity))
                        processed_pairs.add(pair_key)
        
        return sorted(fuzzy_duplicates, key=lambda x: x[2], reverse=True)

    def find_contact_duplicates(self) -> List[Tuple[Resource, Resource, str]]:
        """Find resources with same contact information."""
        contact_duplicates = []
        processed_pairs = set()
        
        resources_list = list(self.resources)
        
        for i, resource1 in enumerate(resources_list):
            for j, resource2 in enumerate(resources_list[i+1:], i+1):
                if resource1.id == resource2.id:
                    continue
                
                pair_key = tuple(sorted([resource1.id, resource2.id]))
                if pair_key in processed_pairs:
                    continue
                
                # Check phone
                if (resource1.phone and resource2.phone and 
                    self.normalize_phone(resource1.phone) == self.normalize_phone(resource2.phone)):
                    contact_duplicates.append((resource1, resource2, "phone"))
                    processed_pairs.add(pair_key)
                    continue
                
                # Check email
                if (resource1.email and resource2.email and 
                    resource1.email.lower().strip() == resource2.email.lower().strip()):
                    contact_duplicates.append((resource1, resource2, "email"))
                    processed_pairs.add(pair_key)
                    continue
                
                # Check website
                if resource1.website and resource2.website:
                    website1 = resource1.website.lower().strip()
                    website2 = resource2.website.lower().strip()
                    if website1 == website2:
                        contact_duplicates.append((resource1, resource2, "website"))
                        processed_pairs.add(pair_key)
                        continue
        
        return contact_duplicates

    def get_duplicate_summary(self) -> Dict[str, Any]:
        """Get a summary of all duplicate types found."""
        exact_name_duplicates = self.find_exact_duplicates()
        phone_duplicates = self.find_phone_duplicates()
        website_duplicates = self.find_website_duplicates()
        email_duplicates = self.find_email_duplicates()
        address_duplicates = self.find_address_duplicates()
        fuzzy_duplicates = self.find_fuzzy_name_duplicates()
        contact_duplicates = self.find_contact_duplicates()
        
        return {
            'exact_name_duplicates': exact_name_duplicates,
            'phone_duplicates': phone_duplicates,
            'website_duplicates': website_duplicates,
            'email_duplicates': email_duplicates,
            'address_duplicates': address_duplicates,
            'fuzzy_duplicates': fuzzy_duplicates,
            'contact_duplicates': contact_duplicates,
            'summary': {
                'exact_name_groups': len(exact_name_duplicates),
                'phone_groups': len(phone_duplicates),
                'website_groups': len(website_duplicates),
                'email_groups': len(email_duplicates),
                'address_groups': len(address_duplicates),
                'fuzzy_pairs': len(fuzzy_duplicates),
                'contact_pairs': len(contact_duplicates),
            }
        }


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
