#!/usr/bin/env python3
"""
GIS Data Migration: Local Development → Render Staging

This script exports GIS data from local development environment and imports it to Render staging.
Handles spatial data properly including geometry fields and PostGIS-specific data.

Usage:
    python cloud/migrate_gis_data.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_gis_data_from_dev():
    """Export GIS data from local development environment"""
    print("📤 Exporting GIS data from local development...")
    
    # Set up Django for local development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
    import django
    django.setup()
    
    from directory.models import Resource, TaxonomyCategory, ServiceType, CoverageArea, ResourceCoverage
    from django.contrib.auth.models import User
    
    # Create exports directory
    exports_dir = project_root / 'cloud' / 'exports'
    exports_dir.mkdir(exist_ok=True)
    
    # Export users (needed for foreign keys)
    users = User.objects.all()
    user_data = []
    for user in users:
        user_data.append({
            'model': 'auth.user',
            'pk': user.id,
            'fields': {
                'password': user.password,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_superuser': user.is_superuser,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
            }
        })
    
    with open(exports_dir / 'users.json', 'w') as f:
        json.dump(user_data, f, indent=2)
    print(f"✅ Exported {len(user_data)} users")
    
    # Export taxonomy categories
    categories = TaxonomyCategory.objects.all()
    category_data = []
    for cat in categories:
        category_data.append({
            'model': 'directory.taxonomycategory',
            'pk': cat.id,
            'fields': {
                'name': cat.name,
                'description': cat.description or '',
                'slug': cat.slug,
                'created_at': cat.created_at.isoformat(),
                'updated_at': cat.updated_at.isoformat(),
            }
        })
    
    with open(exports_dir / 'categories.json', 'w') as f:
        json.dump(category_data, f, indent=2)
    print(f"✅ Exported {len(category_data)} categories")
    
    # Export service types
    service_types = ServiceType.objects.all()
    service_type_data = []
    for st in service_types:
        service_type_data.append({
            'model': 'directory.servicetype',
            'pk': st.id,
            'fields': {
                'name': st.name,
                'description': st.description or '',
                'slug': st.slug,
                'created_at': st.created_at.isoformat(),
            }
        })
    
    with open(exports_dir / 'service_types.json', 'w') as f:
        json.dump(service_type_data, f, indent=2)
    print(f"✅ Exported {len(service_type_data)} service types")
    
    # Export coverage areas with spatial data
    coverage_areas = CoverageArea.objects.all()
    coverage_data = []
    for ca in coverage_areas:
        # Handle spatial fields properly
        geom_data = None
        center_data = None
        
        if ca.geom:
            geom_data = ca.geom.ewkt  # Export as WKT with SRID
        
        if ca.center:
            center_data = ca.center.ewkt  # Export as WKT with SRID
        
        coverage_data.append({
            'model': 'directory.coveragearea',
            'pk': ca.id,
            'fields': {
                'kind': ca.kind,
                'name': ca.name,
                'geom': geom_data,
                'center': center_data,
                'radius_m': ca.radius_m,
                'ext_ids': ca.ext_ids,
                'created_at': ca.created_at.isoformat(),
                'updated_at': ca.updated_at.isoformat(),
                'created_by_id': ca.created_by.id,
                'updated_by_id': ca.updated_by.id,
            }
        })
    
    with open(exports_dir / 'coverage_areas.json', 'w') as f:
        json.dump(coverage_data, f, indent=2)
    print(f"✅ Exported {len(coverage_data)} coverage areas with spatial data")
    
    # Export resources
    resources = Resource.objects.all()
    resource_data = []
    for resource in resources:
        # Get service type IDs
        service_type_ids = list(resource.service_types.values_list('id', flat=True))
        
        resource_data.append({
            'model': 'directory.resource',
            'pk': resource.id,
            'fields': {
                'name': resource.name,
                'category_id': resource.category.id if resource.category else None,
                'service_types': service_type_ids,
                'description': resource.description,
                'phone': resource.phone,
                'email': resource.email,
                'website': resource.website,
                'address1': resource.address1,
                'address2': resource.address2,
                'city': resource.city,
                'state': resource.state,
                'county': resource.county,
                'postal_code': resource.postal_code,
                'status': resource.status,
                'source': resource.source,
                'notes': resource.notes,
                'hours_of_operation': resource.hours_of_operation,
                'is_emergency_service': resource.is_emergency_service,
                'is_24_hour_service': resource.is_24_hour_service,
                'eligibility_requirements': resource.eligibility_requirements,
                'populations_served': resource.populations_served,
                'insurance_accepted': resource.insurance_accepted,
                'cost_information': resource.cost_information,
                'languages_available': resource.languages_available,
                'capacity': resource.capacity,
                'last_verified_at': resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                'last_verified_by_id': resource.last_verified_by.id if resource.last_verified_by else None,
                'verification_frequency_days': resource.verification_frequency_days,
                'created_at': resource.created_at.isoformat(),
                'updated_at': resource.updated_at.isoformat(),
                'created_by_id': resource.created_by.id,
                'updated_by_id': resource.updated_by.id,
                'is_deleted': resource.is_deleted,
                'is_archived': resource.is_archived,
                'archived_at': resource.archived_at.isoformat() if resource.archived_at else None,
                'archived_by_id': resource.archived_by.id if resource.archived_by else None,
                'archive_reason': resource.archive_reason,
            }
        })
    
    with open(exports_dir / 'resources.json', 'w') as f:
        json.dump(resource_data, f, indent=2)
    print(f"✅ Exported {len(resource_data)} resources")
    
    # Export resource-coverage associations
    associations = ResourceCoverage.objects.all()
    association_data = []
    for assoc in associations:
        association_data.append({
            'model': 'directory.resourcecoverage',
            'pk': assoc.id,
            'fields': {
                'resource_id': assoc.resource.id,
                'coverage_area_id': assoc.coverage_area.id,
                'created_at': assoc.created_at.isoformat(),
                'created_by_id': assoc.created_by.id,
                'notes': assoc.notes,
            }
        })
    
    with open(exports_dir / 'resource_coverage.json', 'w') as f:
        json.dump(association_data, f, indent=2)
    print(f"✅ Exported {len(association_data)} resource-coverage associations")
    
    print("🎉 GIS data export completed successfully!")

def import_gis_data_to_staging():
    """Import GIS data to Render staging environment"""
    print("📥 Importing GIS data to Render staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import Resource, TaxonomyCategory, ServiceType, CoverageArea, ResourceCoverage
    from django.contrib.auth.models import User
    from django.contrib.gis.geos import GEOSGeometry
    
    # Clear existing data (optional - comment out if you want to preserve existing data)
    print("🗑️ Clearing existing data...")
    ResourceCoverage.objects.all().delete()
    Resource.objects.all().delete()
    CoverageArea.objects.all().delete()
    ServiceType.objects.all().delete()
    TaxonomyCategory.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    
    exports_dir = project_root / 'cloud' / 'exports'
    
    # Import users
    with open(exports_dir / 'users.json', 'r') as f:
        user_data = json.load(f)
    
    for user_item in user_data:
        fields = user_item['fields']
        user = User.objects.create(
            id=user_item['pk'],
            username=fields['username'],
            email=fields['email'],
            first_name=fields['first_name'],
            last_name=fields['last_name'],
            is_staff=fields['is_staff'],
            is_superuser=fields['is_superuser'],
            is_active=fields['is_active'],
            date_joined=datetime.fromisoformat(fields['date_joined']),
        )
        user.password = fields['password']  # Set hashed password
        user.save()
    print(f"✅ Imported {len(user_data)} users")
    
    # Import categories
    with open(exports_dir / 'categories.json', 'r') as f:
        category_data = json.load(f)
    
    for cat_item in category_data:
        fields = cat_item['fields']
        TaxonomyCategory.objects.create(
            id=cat_item['pk'],
            name=fields['name'],
            description=fields['description'],
            slug=fields['slug'],
            created_at=datetime.fromisoformat(fields['created_at']),
            updated_at=datetime.fromisoformat(fields['updated_at']),
        )
    print(f"✅ Imported {len(category_data)} categories")
    
    # Import service types
    with open(exports_dir / 'service_types.json', 'r') as f:
        service_type_data = json.load(f)
    
    for st_item in service_type_data:
        fields = st_item['fields']
        ServiceType.objects.create(
            id=st_item['pk'],
            name=fields['name'],
            description=fields['description'],
            slug=fields['slug'],
            created_at=datetime.fromisoformat(fields['created_at']),
        )
    print(f"✅ Imported {len(service_type_data)} service types")
    
    # Import coverage areas with spatial data
    with open(exports_dir / 'coverage_areas.json', 'r') as f:
        coverage_data = json.load(f)
    
    for ca_item in coverage_data:
        fields = ca_item['fields']
        
        # Handle spatial fields
        geom = None
        center = None
        
        if fields['geom']:
            geom = GEOSGeometry(fields['geom'])
        
        if fields['center']:
            center = GEOSGeometry(fields['center'])
        
        CoverageArea.objects.create(
            id=ca_item['pk'],
            kind=fields['kind'],
            name=fields['name'],
            geom=geom,
            center=center,
            radius_m=fields['radius_m'],
            ext_ids=fields['ext_ids'],
            created_at=datetime.fromisoformat(fields['created_at']),
            updated_at=datetime.fromisoformat(fields['updated_at']),
            created_by_id=fields['created_by_id'],
            updated_by_id=fields['updated_by_id'],
        )
    print(f"✅ Imported {len(coverage_data)} coverage areas with spatial data")
    
    # Import resources
    with open(exports_dir / 'resources.json', 'r') as f:
        resource_data = json.load(f)
    
    for res_item in resource_data:
        fields = res_item['fields']
        
        # Create resource without M2M fields first
        resource = Resource.objects.create(
            id=res_item['pk'],
            name=fields['name'],
            category_id=fields['category_id'],
            description=fields['description'],
            phone=fields['phone'],
            email=fields['email'],
            website=fields['website'],
            address1=fields['address1'],
            address2=fields['address2'],
            city=fields['city'],
            state=fields['state'],
            county=fields['county'],
            postal_code=fields['postal_code'],
            status=fields['status'],
            source=fields['source'],
            notes=fields['notes'],
            hours_of_operation=fields['hours_of_operation'],
            is_emergency_service=fields['is_emergency_service'],
            is_24_hour_service=fields['is_24_hour_service'],
            eligibility_requirements=fields['eligibility_requirements'],
            populations_served=fields['populations_served'],
            insurance_accepted=fields['insurance_accepted'],
            cost_information=fields['cost_information'],
            languages_available=fields['languages_available'],
            capacity=fields['capacity'],
            last_verified_at=datetime.fromisoformat(fields['last_verified_at']) if fields['last_verified_at'] else None,
            last_verified_by_id=fields['last_verified_by_id'],
            verification_frequency_days=fields['verification_frequency_days'],
            created_at=datetime.fromisoformat(fields['created_at']),
            updated_at=datetime.fromisoformat(fields['updated_at']),
            created_by_id=fields['created_by_id'],
            updated_by_id=fields['updated_by_id'],
            is_deleted=fields['is_deleted'],
            is_archived=fields['is_archived'],
            archived_at=datetime.fromisoformat(fields['archived_at']) if fields['archived_at'] else None,
            archived_by_id=fields['archived_by_id'],
            archive_reason=fields['archive_reason'],
        )
        
        # Add service types
        if fields['service_types']:
            service_types = ServiceType.objects.filter(id__in=fields['service_types'])
            resource.service_types.set(service_types)
    
    print(f"✅ Imported {len(resource_data)} resources")
    
    # Import resource-coverage associations
    with open(exports_dir / 'resource_coverage.json', 'r') as f:
        association_data = json.load(f)
    
    for assoc_item in association_data:
        fields = assoc_item['fields']
        ResourceCoverage.objects.create(
            id=assoc_item['pk'],
            resource_id=fields['resource_id'],
            coverage_area_id=fields['coverage_area_id'],
            created_at=datetime.fromisoformat(fields['created_at']),
            created_by_id=fields['created_by_id'],
            notes=fields['notes'],
        )
    
    print(f"✅ Imported {len(association_data)} resource-coverage associations")
    
    print("🎉 GIS data import to staging completed successfully!")

def test_gis_functionality():
    """Test GIS functionality on staging"""
    print("🧪 Testing GIS functionality on staging...")
    
    # Set up Django for staging
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.cloud_settings')
    import django
    django.setup()
    
    from directory.models import Resource, CoverageArea, ResourceCoverage
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    
    # Test basic counts
    resource_count = Resource.objects.count()
    coverage_count = CoverageArea.objects.count()
    association_count = ResourceCoverage.objects.count()
    
    print(f"📊 Data counts:")
    print(f"  - Resources: {resource_count}")
    print(f"  - Coverage Areas: {coverage_count}")
    print(f"  - Associations: {association_count}")
    
    # Test spatial query
    if coverage_count > 0:
        # Find coverage areas with center points
        areas_with_center = CoverageArea.objects.filter(center__isnull=False)
        if areas_with_center.exists():
            test_point = Point(-84.0849, 37.1289, srid=4326)  # London, KY
            nearby_areas = areas_with_center.filter(
                center__distance_lte=(test_point, 10000)
            ).annotate(
                distance=Distance('center', test_point)
            ).order_by('distance')[:3]
            
            print(f"📍 Spatial query test:")
            for area in nearby_areas:
                print(f"  - {area.name}: {area.distance.m:.0f}m away")
    
    print("✅ GIS functionality test completed!")

def main():
    """Main migration function"""
    print("🚀 Starting GIS Data Migration: Local Dev → Render Staging")
    print("=" * 60)
    
    # Step 1: Export from development
    export_gis_data_from_dev()
    print()
    
    # Step 2: Import to staging
    import_gis_data_to_staging()
    print()
    
    # Step 3: Test functionality
    test_gis_functionality()
    print()
    
    print("🎉 GIS Data Migration completed successfully!")
    print("Your Render staging environment now has full GIS functionality!")

if __name__ == '__main__':
    main()

