"""
Audit Models - Version History and Audit Trail Models

This module contains the audit and versioning models for tracking changes
and maintaining an immutable audit trail of all system actions. These models
provide comprehensive logging and version history capabilities.

Models:
    - ResourceVersion: Immutable snapshots of resource changes
    - AuditLog: Append-only audit log for all system actions

Features:
    - Immutable version snapshots with full resource state
    - Change tracking with field-level granularity
    - Comprehensive audit logging for all actions
    - JSON metadata storage for flexible context
    - Automatic timestamp and user tracking

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models.audit import ResourceVersion, AuditLog

    # Get version history for a resource
    versions = ResourceVersion.objects.filter(resource=resource)

    # Get audit logs for a specific action
    logs = AuditLog.objects.filter(action='create_resource')
"""

import json
from typing import Any, Dict, List

from django.contrib.auth.models import User
from django.db import models


class ResourceVersion(models.Model):
    """Immutable snapshots of resource changes.

    This model maintains an immutable history of all changes made to resources,
    providing a complete audit trail and version history. Each version contains
    a full snapshot of the resource state at the time of the change, along with
    metadata about what changed and who made the change.

    Versions are automatically created whenever a resource is saved, providing
    a complete history that can be used for auditing, rollback, or analysis.

    Attributes:
        resource (Resource): The resource this version belongs to
        version_number (int): Sequential version number for this resource
        snapshot_json (str): Full resource state as JSON string
        changed_fields (str): JSON array of field names that changed
        change_type (str): Type of change (create, update, status_change)
        changed_by (User): User who made the change
        changed_at (datetime): When the change was made

    Change Types:
        - create: Initial resource creation
        - update: Field value changes
        - status_change: Status workflow changes

    Example:
        >>> # Get all versions for a resource
        >>> versions = ResourceVersion.objects.filter(resource=resource)
        >>> latest = versions.first()
        >>> print(f"Version {latest.version_number} by {latest.changed_by}")
    """

    CHANGE_TYPES = [
        ("create", "Create"),
        ("update", "Update"),
        ("status_change", "Status Change"),
    ]

    resource = models.ForeignKey(
        "directory.Resource", on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    snapshot_json = models.TextField()  # Full resource state at save time
    changed_fields = models.TextField()  # JSON array of changed field names
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    changed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="resource_versions"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["resource", "version_number"]
        ordering = ["-version_number"]

    def __str__(self) -> str:
        """Return a string representation of the version."""
        return f"{self.resource.name} v{self.version_number}"

    @property
    def snapshot(self) -> Dict[str, Any]:
        """Get the snapshot data as a dictionary.

        Returns:
            Dict[str, Any]: The complete resource state at version time
        """
        return json.loads(self.snapshot_json)

    @property
    def changed_field_list(self) -> List[str]:
        """Get the list of changed fields.

        Returns:
            List[str]: List of field names that changed in this version
        """
        return json.loads(self.changed_fields)


class AuditLog(models.Model):
    """Append-only audit log for all system actions.

    This model provides a comprehensive audit trail of all actions performed
    in the system, including resource creation, updates, deletions, and
    administrative actions. The log is append-only to ensure data integrity
    and provides detailed context for each action.

    Each log entry includes the actor, action type, target information,
    and optional metadata for additional context. This enables complete
    audit trails for compliance and debugging purposes.

    Attributes:
        actor (User): User who performed the action
        action (str): Type of action performed (e.g., 'create_resource')
        target_table (str): Database table affected (e.g., 'resource')
        target_id (str): ID of the affected record
        metadata_json (str): Additional context as JSON string
        created_at (datetime): When the action was performed

    Example:
        >>> # Get recent audit logs
        >>> logs = AuditLog.objects.filter(actor=user).order_by('-created_at')[:10]
        >>> for log in logs:
        ...     print(f"{log.created_at}: {log.action} on {log.target_table}")
    """

    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="audit_actions"
    )
    action = models.CharField(
        max_length=100
    )  # e.g., 'create_resource', 'update_resource'
    target_table = models.CharField(
        max_length=50
    )  # e.g., 'resource', 'taxonomy_category'
    target_id = models.CharField(max_length=50)  # ID of the affected record
    metadata_json = models.TextField(blank=True)  # Additional context
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor"]),
            models.Index(fields=["action"]),
            models.Index(fields=["target_table"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Return a string representation of the audit log entry."""
        return f"{self.action} by {self.actor.username} at {self.created_at}"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata as a dictionary.

        Returns:
            Dict[str, Any]: The metadata context for this action, or empty dict
        """
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
