from django.core.management.base import BaseCommand
from django.db import transaction
from directory.models import Resource, ResourceVersion
import json


class Command(BaseCommand):
    help = 'Fix published resources that are missing version records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Finding published resources without version records...")
        
        # Find published resources
        published_resources = Resource.objects.filter(
            status='published',
            is_deleted=False
        )
        
        self.stdout.write(f"Found {published_resources.count()} published resources")
        
        # Check which ones are missing versions
        resources_to_fix = []
        for resource in published_resources:
            version_count = ResourceVersion.objects.filter(resource=resource).count()
            if version_count == 0:
                resources_to_fix.append(resource)
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Resource {resource.id}: {resource.name} - No versions")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Resource {resource.id}: {resource.name} - {version_count} versions")
                )
        
        if not resources_to_fix:
            self.stdout.write(
                self.style.SUCCESS("🎉 All published resources already have version records!")
            )
            return
        
        self.stdout.write(f"\n🔧 Found {len(resources_to_fix)} resources that need fixing")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
            return
        
        # Confirm before proceeding
        response = input(f"\nProceed to create version records for {len(resources_to_fix)} resources? (y/N): ")
        if response.lower() != 'y':
            self.stdout.write("Operation cancelled.")
            return
        
        # Create version records
        created_versions = []
        with transaction.atomic():
            for resource in resources_to_fix:
                try:
                    version = self.create_initial_version_for_resource(resource)
                    created_versions.append(version)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Failed to create version for {resource.name}: {e}")
                    )
                    raise
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Successfully created {len(created_versions)} version records!")
        )
        self.stdout.write("Published comparison views should now work correctly for these resources.")
        
        # Verify the fix
        self.verify_fix()

    def create_initial_version_for_resource(self, resource):
        """Create an initial version record for a published resource."""
        self.stdout.write(f"Creating initial version for resource {resource.id}: {resource.name}")
        
        # Create snapshot data
        snapshot_data = {
            "id": resource.id,
            "name": resource.name,
            "category_id": resource.category_id,
            "description": resource.description,
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            "status": resource.status,
            "source": resource.source,
            "notes": resource.notes,
            "hours_of_operation": resource.hours_of_operation,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            "is_emergency_service": resource.is_emergency_service,
            "is_24_hour_service": resource.is_24_hour_service,
            "insurance_accepted": resource.insurance_accepted,
            "capacity": resource.capacity,
            "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
            "last_verified_by_id": resource.last_verified_by_id,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
            "created_by_id": resource.created_by_id,
            "updated_by_id": resource.updated_by_id,
            "is_deleted": resource.is_deleted,
        }
        
        # Create the version record
        version = ResourceVersion.objects.create(
            resource=resource,
            version_number=1,
            snapshot_json=json.dumps(snapshot_data),
            changed_fields=json.dumps(list(snapshot_data.keys())),
            change_type="create",
            changed_by=resource.updated_by,
        )
        
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Created version {version.version_number} for {resource.name}")
        )
        return version

    def verify_fix(self):
        """Verify that the fix worked by checking version counts."""
        self.stdout.write("\n🔍 Verifying fix...")
        
        published_resources = Resource.objects.filter(
            status='published',
            is_deleted=False
        )
        
        all_fixed = True
        for resource in published_resources:
            version_count = ResourceVersion.objects.filter(resource=resource).count()
            if version_count == 0:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Resource {resource.id}: {resource.name} - Still no versions")
                )
                all_fixed = False
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Resource {resource.id}: {resource.name} - {version_count} versions")
                )
        
        if all_fixed:
            self.stdout.write(
                self.style.SUCCESS("\n🎉 All published resources now have version records!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("\n⚠️  Some resources still need fixing.")
            )
