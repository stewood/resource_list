"""
Duplicate detection utilities for resource management.

This module contains the core logic for detecting duplicate resources
using various criteria including exact matches, fuzzy matching, and
contact information comparison.
"""

import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set, Tuple

from django.db.models import Q

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
