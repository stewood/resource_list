"""
Django management command to merge duplicate resources.

This command consolidates duplicate resources by:
1. Selecting the best record as the primary (usually most complete/verified)
2. Merging complementary information from duplicates
3. Archiving the duplicate records
4. Preserving audit trails

Usage:
    python manage.py merge_duplicates --primary-id=317 --duplicate-ids=263,68,267
    python manage.py merge_duplicates --auto-merge --confidence=high
"""

import json
from typing import Any, Dict, List, Optional, Set

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from directory.models import Resource, ResourceVersion, AuditLog


class DuplicateMerger:
    """Handle merging of duplicate resources."""

    def __init__(self, user: User):
        self.user = user
        self.merged_count = 0
        self.archived_count = 0

    def merge_resources(
        self, primary_id: int, duplicate_ids: List[int], merge_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Merge duplicate resources into a primary resource.

        Args:
            primary_id: ID of the primary resource to keep
            duplicate_ids: List of duplicate resource IDs to merge and archive
            merge_notes: Notes about the merge operation

        Returns:
            Dictionary with merge results
        """
        try:
            with transaction.atomic():
                # Get the primary resource
                primary = Resource.objects.get(id=primary_id)
                duplicates = Resource.objects.filter(id__in=duplicate_ids)

                if not duplicates.exists():
                    raise CommandError(
                        f"No duplicate resources found with IDs: {duplicate_ids}"
                    )

                # Create a backup of the primary resource before merging
                self._create_backup_version(primary, "pre_merge_backup")

                # Merge information from duplicates into primary
                merged_data = self._merge_resource_data(primary, duplicates)

                # Update the primary resource with merged data
                self._update_primary_resource(primary, merged_data)

                # Archive the duplicate resources
                archived_resources = self._archive_duplicates(
                    duplicates, primary_id, merge_notes
                )

                # Log the merge operation
                self._log_merge_operation(primary, duplicates, merge_notes)

                self.merged_count += 1
                self.archived_count += len(duplicates)

                return {
                    "success": True,
                    "primary_id": primary_id,
                    "archived_ids": list(duplicates.values_list("id", flat=True)),
                    "merged_data": merged_data,
                    "message": f"Successfully merged {len(duplicates)} duplicates into primary resource {primary_id}",
                }

        except Resource.DoesNotExist:
            raise CommandError(f"Primary resource with ID {primary_id} not found")
        except Exception as e:
            raise CommandError(f"Merge failed: {str(e)}")

    def _create_backup_version(self, resource: Resource, change_type: str) -> None:
        """Create a backup version of the resource before merging."""
        ResourceVersion.objects.create(
            resource=resource,
            version_number=ResourceVersion.objects.filter(resource=resource).count()
            + 1,
            snapshot_json=json.dumps(self._get_resource_snapshot(resource)),
            changed_fields=json.dumps([]),
            change_type=change_type,
            changed_by=self.user,
        )

    def _get_resource_snapshot(self, resource: Resource) -> Dict[str, Any]:
        """Get a snapshot of the resource's current state."""
        return {
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
            "county": resource.county,
            "postal_code": resource.postal_code,
            "status": resource.status,
            "source": resource.source,
            "notes": resource.notes,
            "hours_of_operation": resource.hours_of_operation,
            "is_emergency_service": resource.is_emergency_service,
            "is_24_hour_service": resource.is_24_hour_service,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "insurance_accepted": resource.insurance_accepted,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            "capacity": resource.capacity,
            "last_verified_at": (
                resource.last_verified_at.isoformat()
                if resource.last_verified_at
                else None
            ),
            "last_verified_by_id": resource.last_verified_by_id,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
            "created_by_id": resource.created_by_id,
            "updated_by_id": resource.updated_by_id,
            "is_deleted": resource.is_deleted,
            "is_archived": resource.is_archived,
        }

    def _merge_resource_data(
        self, primary: Resource, duplicates: List[Resource]
    ) -> Dict[str, Any]:
        """Merge data from duplicates into primary resource."""
        merged_data = {
            "service_types": set(),
            "phone_numbers": set(),
            "emails": set(),
            "websites": set(),
            "descriptions": [],
            "notes": [],
            "hours": [],
            "eligibility": [],
            "populations": [],
            "insurance": [],
            "costs": [],
            "languages": [],
            "capacity": [],
        }

        # Collect all resources (primary + duplicates)
        all_resources = [primary] + list(duplicates)

        for resource in all_resources:
            # Collect service types
            merged_data["service_types"].update(resource.service_types.all())

            # Collect contact information
            if resource.phone:
                merged_data["phone_numbers"].add(resource.phone)
            if resource.email:
                merged_data["emails"].add(resource.email)
            if resource.website:
                merged_data["websites"].add(resource.website)

            # Collect text fields (avoid duplicates)
            if (
                resource.description
                and resource.description not in merged_data["descriptions"]
            ):
                merged_data["descriptions"].append(resource.description)
            if resource.notes and resource.notes not in merged_data["notes"]:
                merged_data["notes"].append(resource.notes)
            if (
                resource.hours_of_operation
                and resource.hours_of_operation not in merged_data["hours"]
            ):
                merged_data["hours"].append(resource.hours_of_operation)
            if (
                resource.eligibility_requirements
                and resource.eligibility_requirements not in merged_data["eligibility"]
            ):
                merged_data["eligibility"].append(resource.eligibility_requirements)
            if (
                resource.populations_served
                and resource.populations_served not in merged_data["populations"]
            ):
                merged_data["populations"].append(resource.populations_served)
            if (
                resource.insurance_accepted
                and resource.insurance_accepted not in merged_data["insurance"]
            ):
                merged_data["insurance"].append(resource.insurance_accepted)
            if (
                resource.cost_information
                and resource.cost_information not in merged_data["costs"]
            ):
                merged_data["costs"].append(resource.cost_information)
            if (
                resource.languages_available
                and resource.languages_available not in merged_data["languages"]
            ):
                merged_data["languages"].append(resource.languages_available)
            if resource.capacity and resource.capacity not in merged_data["capacity"]:
                merged_data["capacity"].append(resource.capacity)

        return merged_data

    def _update_primary_resource(
        self, primary: Resource, merged_data: Dict[str, Any]
    ) -> None:
        """Update the primary resource with merged data."""
        # Update service types
        primary.service_types.set(merged_data["service_types"])

        # Update contact information (keep primary's info, add missing from duplicates)
        if not primary.phone and merged_data["phone_numbers"]:
            # Use the most common phone number
            phone_numbers = list(merged_data["phone_numbers"])
            primary.phone = phone_numbers[0]  # Could implement logic to choose best

        if not primary.email and merged_data["emails"]:
            primary.email = list(merged_data["emails"])[0]

        if not primary.website and merged_data["websites"]:
            primary.website = list(merged_data["websites"])[0]

        # Merge text fields
        if merged_data["descriptions"] and not primary.description:
            primary.description = merged_data["descriptions"][0]

        # Combine notes
        if merged_data["notes"]:
            existing_notes = primary.notes or ""
            new_notes = " | ".join(merged_data["notes"])
            if existing_notes:
                primary.notes = f"{existing_notes} | MERGED INFO: {new_notes}"
            else:
                primary.notes = f"MERGED INFO: {new_notes}"

        # Update other fields if primary is missing them
        if not primary.hours_of_operation and merged_data["hours"]:
            primary.hours_of_operation = merged_data["hours"][0]
        if not primary.eligibility_requirements and merged_data["eligibility"]:
            primary.eligibility_requirements = merged_data["eligibility"][0]
        if not primary.populations_served and merged_data["populations"]:
            primary.populations_served = merged_data["populations"][0]
        if not primary.insurance_accepted and merged_data["insurance"]:
            primary.insurance_accepted = merged_data["insurance"][0]
        if not primary.cost_information and merged_data["costs"]:
            primary.cost_information = merged_data["costs"][0]
        if not primary.languages_available and merged_data["languages"]:
            primary.languages_available = merged_data["languages"][0]
        if not primary.capacity and merged_data["capacity"]:
            primary.capacity = merged_data["capacity"][0]

        # Update metadata
        primary.updated_by = self.user
        primary.updated_at = timezone.now()

        # Save the updated primary resource
        primary.save()

    def _archive_duplicates(
        self, duplicates: List[Resource], primary_id: int, merge_notes: str
    ) -> List[Resource]:
        """Archive duplicate resources."""
        archived_resources = []

        for duplicate in duplicates:
            duplicate.is_archived = True
            duplicate.archived_at = timezone.now()
            duplicate.archived_by = self.user
            duplicate.archive_reason = (
                f"Merged into primary resource ID {primary_id}. {merge_notes}"
            )
            duplicate.updated_by = self.user
            duplicate.updated_at = timezone.now()
            duplicate.save()

            archived_resources.append(duplicate)

        return archived_resources

    def _log_merge_operation(
        self, primary: Resource, duplicates: List[Resource], merge_notes: str
    ) -> None:
        """Log the merge operation in audit trail."""
        duplicate_ids = [str(d.id) for d in duplicates]

        # Log merge action
        AuditLog.objects.create(
            actor=self.user,
            action="merge_duplicates",
            target_table="resource",
            target_id=str(primary.id),
            metadata_json=json.dumps(
                {
                    "primary_resource_id": primary.id,
                    "primary_resource_name": primary.name,
                    "duplicate_resource_ids": duplicate_ids,
                    "merge_notes": merge_notes,
                    "merged_at": timezone.now().isoformat(),
                }
            ),
        )

        # Log archive actions for each duplicate
        for duplicate in duplicates:
            AuditLog.objects.create(
                actor=self.user,
                action="archive_duplicate",
                target_table="resource",
                target_id=str(duplicate.id),
                metadata_json=json.dumps(
                    {
                        "archived_resource_id": duplicate.id,
                        "archived_resource_name": duplicate.name,
                        "merged_into_primary_id": primary.id,
                        "merge_notes": merge_notes,
                        "archived_at": timezone.now().isoformat(),
                    }
                ),
            )


class Command(BaseCommand):
    help = "Merge duplicate resources into a single comprehensive record"

    def add_arguments(self, parser):
        parser.add_argument(
            "--primary-id",
            type=int,
            required=False,
            help="ID of the primary resource to keep",
        )
        parser.add_argument(
            "--duplicate-ids",
            type=str,
            required=False,
            help="Comma-separated list of duplicate resource IDs to merge",
        )
        parser.add_argument(
            "--auto-merge",
            action="store_true",
            help="Automatically merge duplicates based on confidence levels",
        )
        parser.add_argument(
            "--confidence",
            choices=["high", "medium", "low"],
            default="high",
            help="Confidence level for auto-merge (default: high)",
        )
        parser.add_argument(
            "--merge-notes",
            type=str,
            default="",
            help="Additional notes about the merge operation",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be merged without actually performing the merge",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )

        if options["auto_merge"]:
            self._auto_merge_duplicates(options)
        elif options["primary_id"] and options["duplicate_ids"]:
            self._manual_merge(options)
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please specify either --auto-merge or both --primary-id and --duplicate-ids"
                )
            )

    def _manual_merge(self, options: Dict[str, Any]) -> None:
        """Perform manual merge of specified resources."""
        primary_id = options["primary_id"]
        duplicate_ids = [int(x.strip()) for x in options["duplicate_ids"].split(",")]
        merge_notes = options["merge_notes"]
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.SUCCESS(
                f"🔄 Starting manual merge of {len(duplicate_ids)} duplicates into primary ID {primary_id}"
            )
        )

        if dry_run:
            self._show_merge_preview(primary_id, duplicate_ids)
            return

        # Get the current user (you might want to specify this)
        user = User.objects.first()  # Or get from options
        if not user:
            raise CommandError("No user found for merge operation")

        merger = DuplicateMerger(user)
        result = merger.merge_resources(primary_id, duplicate_ids, merge_notes)

        self.stdout.write(self.style.SUCCESS(f'✅ {result["message"]}'))
        self.stdout.write(
            f'📊 Archived {len(result["archived_ids"])} duplicate resources'
        )

    def _auto_merge_duplicates(self, options: Dict[str, Any]) -> None:
        """Automatically merge duplicates based on confidence levels."""
        confidence = options["confidence"]
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.SUCCESS(
                f"🔄 Starting auto-merge with {confidence} confidence level"
            )
        )

        # This would implement automatic duplicate detection and merging
        # For now, we'll just show what would be done
        self.stdout.write(
            self.style.WARNING("Auto-merge functionality not yet implemented")
        )

    def _show_merge_preview(self, primary_id: int, duplicate_ids: List[int]) -> None:
        """Show a preview of what would be merged."""
        try:
            primary = Resource.objects.get(id=primary_id)
            duplicates = Resource.objects.filter(id__in=duplicate_ids)

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("📋 MERGE PREVIEW")
            self.stdout.write("=" * 60)

            self.stdout.write(f"\n🎯 PRIMARY RESOURCE (ID: {primary_id}):")
            self.stdout.write(f"   Name: {primary.name}")
            self.stdout.write(f"   Phone: {primary.phone}")
            self.stdout.write(f"   Email: {primary.email}")
            self.stdout.write(f"   Website: {primary.website}")
            self.stdout.write(f"   Status: {primary.status}")

            self.stdout.write(f"\n🗑️  DUPLICATES TO ARCHIVE:")
            for duplicate in duplicates:
                self.stdout.write(f"   ID {duplicate.id}: {duplicate.name}")
                self.stdout.write(f"      Phone: {duplicate.phone}")
                self.stdout.write(f"      Email: {duplicate.email}")
                self.stdout.write(f"      Status: {duplicate.status}")

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("DRY RUN COMPLETE - No changes made")
            self.stdout.write("=" * 60)

        except Resource.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"❌ Resource not found: {e}"))
