"""
Resource Verification Service for finding and managing resources needing verification.

This service handles the logic for finding resources that need verification
based on priority criteria and formatting resource data for verification.
"""

import datetime
from typing import List, Optional

from django.db.models import Q
from django.utils import timezone

from directory.models import Resource
from directory.models.verification_models import ResourceData
from directory.utils.verification_utils import (
    calculate_days_since_verification,
    determine_verification_priority
)
from directory.config.verification_config import VerificationConfig, default_verification_config


class ResourceVerificationService:
    """
    Service for resource verification operations.

    This service encapsulates the logic for finding resources that need verification
    and formatting resource data for the verification process.
    """

    def __init__(self, config: Optional[VerificationConfig] = None):
        """
        Initialize the resource verification service.

        Args:
            config: Configuration for the service
        """
        self.config = config or default_verification_config

    def find_resources_needing_verification(self, limit: int = 1) -> List[Resource]:
        """
        Find resources that need verification based on priority criteria.

        Priority order:
        1. Resources with no verification date AND no service areas defined (highest priority)
        2. Resources with no verification date (high priority)
        3. Resources with expired verification dates (medium priority)

        Args:
            limit: Maximum number of resources to return

        Returns:
            List of resources ordered by priority and ID
        """
        # Priority 1: No verification date + no service areas (highest priority)
        priority_1 = Resource.objects.filter(
            Q(last_verified_at__isnull=True) &
            Q(coverage_areas__isnull=True)
        ).order_by('id')

        if priority_1.exists():
            return list(priority_1[:limit])

        # Priority 2: No verification date (high priority)
        priority_2 = Resource.objects.filter(
            last_verified_at__isnull=True
        ).order_by('id')

        if priority_2.exists():
            return list(priority_2[:limit])

        # Priority 3: Expired verification dates (medium priority)
        # Default verification frequency is 180 days
        cutoff_date = timezone.now() - datetime.timedelta(days=self.config.verification_frequency_days)
        priority_3 = Resource.objects.filter(
            Q(last_verified_at__lt=cutoff_date) &
            Q(status='published')  # Only check published resources for re-verification
        ).order_by('id')

        if priority_3.exists():
            return list(priority_3[:limit])

        # No resources need verification
        return []

    def format_resource_for_verification(self, resource: Resource, verbose: bool = False) -> ResourceData:
        """
        Format a resource for verification output.

        Args:
            resource: Resource instance to format
            verbose: Whether to include verbose information

        Returns:
            ResourceData with formatted resource information
        """
        # Basic resource information
        resource_data = ResourceData(
            id=resource.id,
            name=resource.name,
            status=resource.status,
            category=resource.category.name if resource.category else None,
            description=resource.description,
            city=resource.city,
            state=resource.state,
            county=resource.county,
            verification_status={
                "last_verified_at": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                "last_verified_by": resource.last_verified_by.username if resource.last_verified_by else None,
                "verification_frequency_days": resource.verification_frequency_days,
                "days_since_verification": calculate_days_since_verification(resource),
                "verification_priority": determine_verification_priority(resource)
            },
            service_areas={
                "assigned": list(resource.coverage_areas.values_list('name', flat=True)),
                "count": resource.coverage_areas.count()
            },
            service_types={
                "assigned": list(resource.service_types.values_list('name', flat=True)),
                "count": resource.service_types.count()
            }
        )

        # Add verbose information if requested
        if verbose:
            resource_data.contact_information = {
                "phone": resource.phone,
                "email": resource.email,
                "website": resource.website,
                "address1": resource.address1,
                "address2": resource.address2,
                "postal_code": resource.postal_code
            }
            resource_data.operational_details = {
                "hours_of_operation": resource.hours_of_operation,
                "is_emergency_service": resource.is_emergency_service,
                "is_24_hour_service": resource.is_24_hour_service,
                "capacity": resource.capacity
            }
            resource_data.service_details = {
                "eligibility_requirements": resource.eligibility_requirements,
                "populations_served": resource.populations_served,
                "insurance_accepted": resource.insurance_accepted,
                "cost_information": resource.cost_information,
                "languages_available": resource.languages_available
            }
            resource_data.metadata = {
                "source": resource.source,
                "notes": resource.notes,
                "created_at": resource.created_at.isoformat() if resource.created_at else None,
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
            }

        return resource_data

    def get_resource_by_id(self, resource_id: int) -> Optional[Resource]:
        """
        Get a resource by its ID.

        Args:
            resource_id: ID of the resource to retrieve

        Returns:
            Resource instance or None if not found
        """
        try:
            return Resource.objects.get(id=resource_id)
        except Resource.DoesNotExist:
            return None

    def get_verification_stats(self) -> dict:
        """
        Get statistics about resource verification status.

        Returns:
            Dictionary with verification statistics
        """
        total_resources = Resource.objects.count()
        verified_resources = Resource.objects.filter(last_verified_at__isnull=False).count()
        unverified_resources = Resource.objects.filter(last_verified_at__isnull=True).count()

        # Resources with expired verification
        cutoff_date = timezone.now() - datetime.timedelta(days=self.config.verification_frequency_days)
        expired_resources = Resource.objects.filter(
            Q(last_verified_at__lt=cutoff_date) &
            Q(status='published')
        ).count()

        # Resources without service areas
        no_service_areas = Resource.objects.filter(coverage_areas__isnull=True).count()

        return {
            "total_resources": total_resources,
            "verified_resources": verified_resources,
            "unverified_resources": unverified_resources,
            "expired_resources": expired_resources,
            "no_service_areas": no_service_areas,
            "verification_rate": (verified_resources / total_resources * 100) if total_resources > 0 else 0
        }

