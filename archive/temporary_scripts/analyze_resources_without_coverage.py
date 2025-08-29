#!/usr/bin/env python3
"""
Analyze Resources Without Coverage Areas

This script analyzes resources that don't have coverage areas assigned by category and location.
"""
import os
import sys
import django
from collections import Counter

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource

def analyze_resources_without_coverage():
    print("🔍 Analyzing Resources Without Coverage Areas...")
    
    # Get resources without coverage
    resources_without = Resource.objects.filter(
        resource_coverage_associations__isnull=True
    ).order_by('id')
    
    total = resources_without.count()
    print(f"📊 Total Resources Without Coverage: {total}")
    
    # Analyze by category
    print(f"\n📋 Analysis by Category:")
    categories = Counter()
    for resource in resources_without:
        category_name = resource.category.name if resource.category else 'No Category'
        categories[category_name] += 1
    
    for category, count in categories.most_common():
        print(f"  {category}: {count} resources")
    
    # Analyze by state
    print(f"\n📋 Analysis by State:")
    states = Counter()
    for resource in resources_without:
        state = resource.state if resource.state else 'No State'
        states[state] += 1
    
    for state, count in states.most_common():
        print(f"  {state}: {count} resources")
    
    # Look for patterns in names
    print(f"\n📋 Common Patterns in Resource Names:")
    name_patterns = Counter()
    for resource in resources_without:
        name = resource.name.lower()
        if 'kentucky' in name:
            name_patterns['Contains "Kentucky"'] += 1
        if 'hotline' in name:
            name_patterns['Contains "Hotline"'] += 1
        if 'national' in name or 'federal' in name:
            name_patterns['Contains "National/Federal"'] += 1
        if 'statewide' in name:
            name_patterns['Contains "Statewide"'] += 1
        if 'call center' in name:
            name_patterns['Contains "Call Center"'] += 1
    
    for pattern, count in name_patterns.most_common():
        print(f"  {pattern}: {count} resources")
    
    # Show some examples that might need research
    print(f"\n📋 Examples of Resources That May Need Research:")
    examples = []
    for resource in resources_without:
        name = resource.name.lower()
        if any(keyword in name for keyword in ['kentucky', 'national', 'federal', 'statewide']):
            examples.append(resource)
    
    for i, resource in enumerate(examples[:10], 1):
        print(f"  {i}. ID {resource.id} - {resource.name}")
        print(f"     Location: {resource.city}, {resource.state}")
        print(f"     Category: {resource.category.name if resource.category else 'None'}")
        print()

if __name__ == "__main__":
    analyze_resources_without_coverage()
