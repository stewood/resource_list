"""
Audit models and signals for tracking changes.
"""
import json
from typing import Any, Dict, List

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from directory.models import Resource, ResourceVersion, AuditLog


class AuditManager:
    """Manager for audit operations."""
    
    @staticmethod
    def log_action(
        actor: User,
        action: str,
        target_table: str,
        target_id: str,
        metadata: Dict[str, Any] = None
    ) -> AuditLog:
        """Log an audit action."""
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_table=target_table,
            target_id=str(target_id),
            metadata_json=json.dumps(metadata) if metadata else ''
        )
    
    @staticmethod
    def create_version(
        resource: Resource,
        changed_by: User,
        change_type: str,
        changed_fields: List[str] = None
    ) -> ResourceVersion:
        """Create a new version of a resource."""
        # Get the next version number
        latest_version = ResourceVersion.objects.filter(
            resource=resource
        ).order_by('-version_number').first()
        
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create snapshot of current resource state
        snapshot_data = {
            'id': resource.id,
            'name': resource.name,
            'category_id': resource.category_id,
            'description': resource.description,
            'phone': resource.phone,
            'email': resource.email,
            'website': resource.website,
            'address1': resource.address1,
            'address2': resource.address2,
            'city': resource.city,
            'state': resource.state,
            'postal_code': resource.postal_code,
            'status': resource.status,
            'source': resource.source,
            'last_verified_at': resource.last_verified_at.isoformat() if resource.last_verified_at else None,
            'last_verified_by_id': resource.last_verified_by_id,
            'created_at': resource.created_at.isoformat(),
            'updated_at': resource.updated_at.isoformat(),
            'created_by_id': resource.created_by_id,
            'updated_by_id': resource.updated_by_id,
            'is_deleted': resource.is_deleted,
        }
        
        return ResourceVersion.objects.create(
            resource=resource,
            version_number=version_number,
            snapshot_json=json.dumps(snapshot_data),
            changed_fields=json.dumps(changed_fields or []),
            change_type=change_type,
            changed_by=changed_by
        )


@receiver(post_save, sender=Resource)
def handle_resource_save(sender: Any, instance: Resource, created: bool, **kwargs: Any) -> None:
    """Handle resource save events for versioning and audit logging."""
    # Skip if this is a bulk operation
    if kwargs.get('raw', False):
        return
    
    # Determine change type and changed fields
    if created:
        change_type = 'create'
        changed_fields = list(instance._state.fields_cache.keys()) if hasattr(instance, '_state') else []
    else:
        change_type = 'update'
        # For now, we'll track all fields as changed
        # In a more sophisticated implementation, you'd compare old vs new values
        changed_fields = [
            'name', 'category', 'description', 'phone', 'email', 'website',
            'address1', 'address2', 'city', 'state', 'postal_code',
            'status', 'source', 'last_verified_at', 'last_verified_by'
        ]
    
    # Create version
    AuditManager.create_version(
        resource=instance,
        changed_by=instance.updated_by,
        change_type=change_type,
        changed_fields=changed_fields
    )
    
    # Log audit action
    action = 'create_resource' if created else 'update_resource'
    AuditManager.log_action(
        actor=instance.updated_by,
        action=action,
        target_table='resource',
        target_id=instance.id,
        metadata={
            'resource_name': instance.name,
            'status': instance.status,
            'change_type': change_type,
        }
    )


@receiver(post_save, sender=ResourceVersion)
def prevent_version_updates(sender: Any, instance: ResourceVersion, **kwargs: Any) -> None:
    """Ensure ResourceVersion records cannot be updated after creation."""
    if not kwargs.get('created', False):
        # This should be prevented by database triggers, but we add a safety check
        raise ValueError("ResourceVersion records cannot be updated")


@receiver(post_save, sender=AuditLog)
def prevent_audit_updates(sender: Any, instance: AuditLog, **kwargs: Any) -> None:
    """Ensure AuditLog records cannot be updated after creation."""
    if not kwargs.get('created', False):
        # This should be prevented by database triggers, but we add a safety check
        raise ValueError("AuditLog records cannot be updated")
