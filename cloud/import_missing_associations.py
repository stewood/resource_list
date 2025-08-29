#!/usr/bin/env python3
"""
Import Missing Associations - Add missing resource-coverage associations to staging

Usage:
    python cloud/import_missing_associations.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def import_missing_associations():
    """Import missing resource-coverage associations to staging"""
    print("📥 Importing missing associations to staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import ResourceCoverage
    
    # Load export file
    exports_dir = project_root / 'cloud' / 'exports'
    with open(exports_dir / 'resource_coverage.json', 'r') as f:
        data = json.load(f)
    
    print(f"📂 Loaded {len(data)} associations from export file")
    
    # Get existing association IDs
    existing_assoc_ids = set(ResourceCoverage.objects.values_list('id', flat=True))
    print(f"📊 Found {len(existing_assoc_ids)} existing associations")
    
    # Import missing associations
    imported_count = 0
    for item in data:
        if item['pk'] not in existing_assoc_ids:
            fields = item['fields']
            try:
                ResourceCoverage.objects.create(
                    id=item['pk'],
                    resource_id=fields['resource_id'],
                    coverage_area_id=fields['coverage_area_id'],
                    created_at=datetime.fromisoformat(fields['created_at']),
                    created_by_id=fields['created_by_id'],
                    notes=fields['notes'],
                )
                imported_count += 1
            except Exception as e:
                print(f"⚠️  Failed to import association {item['pk']}: {e}")
    
    print(f"✅ Imported {imported_count} missing associations")
    
    # Final count
    final_count = ResourceCoverage.objects.count()
    print(f"📊 Final association count: {final_count}")
    
    print("🎉 Missing associations import completed!")

if __name__ == '__main__':
    import_missing_associations()

