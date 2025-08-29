"""
Duplicate resolution utilities for resource management.

This module contains logic for resolving duplicate resources by merging,
archiving, or flagging them for manual review.
"""

import csv
from typing import Any, Dict, List, Tuple

from django.utils import timezone

from directory.models import Resource


class DuplicateResolver:
    """Handle resolution of duplicate resources."""

    def __init__(self):
        self.resolution_log = []

    def merge_resources(
        self, primary_resource: Resource, duplicate_resources: List[Resource]
    ) -> Dict[str, Any]:
        """
        Merge duplicate resources into a primary resource.

        Args:
            primary_resource: The resource to keep
            duplicate_resources: List of resources to merge and archive

        Returns:
            Dict containing merge results and any issues
        """
        results = {
            "success": True,
            "merged_count": 0,
            "issues": [],
            "archived_resources": [],
        }

        for duplicate in duplicate_resources:
            try:
                # Archive the duplicate resource
                duplicate.is_archived = True
                duplicate.archived_at = timezone.now()
                duplicate.archive_reason = f"Merged into resource {primary_resource.id}"
                duplicate.save()

                results["merged_count"] += 1
                results["archived_resources"].append(duplicate.id)

                self.resolution_log.append(
                    {
                        "action": "merge",
                        "primary_resource_id": primary_resource.id,
                        "duplicate_resource_id": duplicate.id,
                        "timestamp": timezone.now(),
                        "success": True,
                    }
                )

            except Exception as e:
                results["issues"].append(
                    f"Failed to merge resource {duplicate.id}: {str(e)}"
                )
                results["success"] = False

                self.resolution_log.append(
                    {
                        "action": "merge",
                        "primary_resource_id": primary_resource.id,
                        "duplicate_resource_id": duplicate.id,
                        "timestamp": timezone.now(),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def flag_for_review(
        self, resources: List[Resource], reason: str = "Potential duplicate"
    ) -> Dict[str, Any]:
        """
        Flag resources for manual review.

        Args:
            resources: List of resources to flag
            reason: Reason for flagging

        Returns:
            Dict containing flagging results
        """
        results = {"success": True, "flagged_count": 0, "issues": []}

        for resource in resources:
            try:
                # Add a note to the resource for review
                if not resource.notes:
                    resource.notes = ""

                resource.notes += f"\n\n--- FLAGGED FOR REVIEW ---\n{reason}\nFlagged at: {timezone.now()}\n"
                resource.save()

                results["flagged_count"] += 1

                self.resolution_log.append(
                    {
                        "action": "flag_for_review",
                        "resource_id": resource.id,
                        "reason": reason,
                        "timestamp": timezone.now(),
                        "success": True,
                    }
                )

            except Exception as e:
                results["issues"].append(
                    f"Failed to flag resource {resource.id}: {str(e)}"
                )
                results["success"] = False

                self.resolution_log.append(
                    {
                        "action": "flag_for_review",
                        "resource_id": resource.id,
                        "reason": reason,
                        "timestamp": timezone.now(),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def archive_duplicates(
        self, resources: List[Resource], reason: str = "Duplicate resource"
    ) -> Dict[str, Any]:
        """
        Archive duplicate resources.

        Args:
            resources: List of resources to archive
            reason: Reason for archiving

        Returns:
            Dict containing archiving results
        """
        results = {"success": True, "archived_count": 0, "issues": []}

        for resource in resources:
            try:
                resource.is_archived = True
                resource.archived_at = timezone.now()
                resource.archive_reason = reason
                resource.save()

                results["archived_count"] += 1

                self.resolution_log.append(
                    {
                        "action": "archive",
                        "resource_id": resource.id,
                        "reason": reason,
                        "timestamp": timezone.now(),
                        "success": True,
                    }
                )

            except Exception as e:
                results["issues"].append(
                    f"Failed to archive resource {resource.id}: {str(e)}"
                )
                results["success"] = False

                self.resolution_log.append(
                    {
                        "action": "archive",
                        "resource_id": resource.id,
                        "reason": reason,
                        "timestamp": timezone.now(),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def get_resolution_summary(self) -> Dict[str, Any]:
        """Get a summary of all resolution actions taken."""
        summary = {
            "total_actions": len(self.resolution_log),
            "successful_actions": len(
                [log for log in self.resolution_log if log.get("success", False)]
            ),
            "failed_actions": len(
                [log for log in self.resolution_log if not log.get("success", False)]
            ),
            "actions_by_type": {},
            "recent_actions": self.resolution_log[-10:] if self.resolution_log else [],
        }

        # Count actions by type
        for log in self.resolution_log:
            action_type = log.get("action", "unknown")
            summary["actions_by_type"][action_type] = (
                summary["actions_by_type"].get(action_type, 0) + 1
            )

        return summary

    def export_resolution_log(self, filename: str = None) -> str:
        """
        Export resolution log to CSV file.

        Args:
            filename: Optional filename, will generate one if not provided

        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_resolution_log_{timestamp}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Timestamp",
                    "Action",
                    "Resource ID",
                    "Primary Resource ID",
                    "Reason",
                    "Success",
                    "Error",
                ]
            )

            for log in self.resolution_log:
                writer.writerow(
                    [
                        log.get("timestamp", ""),
                        log.get("action", ""),
                        log.get("resource_id", ""),
                        log.get("primary_resource_id", ""),
                        log.get("reason", ""),
                        log.get("success", False),
                        log.get("error", ""),
                    ]
                )

        return filename
