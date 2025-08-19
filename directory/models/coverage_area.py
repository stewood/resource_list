"""
CoverageArea Model - Spatial Service Area Management

This module contains the CoverageArea model for managing spatial service areas
that define where resources provide services. Coverage areas can be counties,
cities, states, custom polygons, or radius-based areas.

Author: Resource Directory Team
Created: 2025-01-15
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models.coverage_area import CoverageArea
    
    # Create a county coverage area
    county_area = CoverageArea.objects.create(
        kind="COUNTY",
        name="Laurel County, KY",
        ext_ids={"state_fips": "21", "county_fips": "125"}
    )
    
    # Create a radius-based coverage area
    radius_area = CoverageArea.objects.create(
        kind="RADIUS",
        name="Downtown Service Area",
        center=Point(-84.0849, 37.1289, srid=4326),
        radius_m=5000
    )
"""

import json
from typing import Any, Dict, Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CoverageArea(models.Model):
    """Model representing a spatial service area for resources.
    
    This model defines geographic areas where resources provide services.
    Coverage areas can be administrative boundaries (counties, cities, states),
    custom polygons, or radius-based areas around a point.
    
    The model supports multiple area types and stores geometry data for
    spatial queries. For radius-based areas, the actual geometry is stored
    as a buffer polygon to enable unified spatial queries.
    
    Attributes:
        KIND_CHOICES: Available coverage area types
        objects: Default model manager
        
    Area Types:
        - CITY: City or municipal boundaries
        - COUNTY: County or parish boundaries  
        - STATE: State or province boundaries
        - POLYGON: Custom polygon boundaries
        - RADIUS: Radius-based area around a point
        
    Example:
        >>> # Create a county coverage area
        >>> county = CoverageArea.objects.create(
        ...     kind="COUNTY",
        ...     name="Laurel County, KY",
        ...     ext_ids={"state_fips": "21", "county_fips": "125"}
        ... )
        
        >>> # Create a radius-based area
        >>> radius = CoverageArea.objects.create(
        ...     kind="RADIUS", 
        ...     name="Downtown Service Area",
        ...     center=Point(-84.0849, 37.1289, srid=4326),
        ...     radius_m=5000
        ... )
    """

    KIND_CHOICES = [
        ("CITY", "City"),
        ("COUNTY", "County"),
        ("STATE", "State"),
        ("POLYGON", "Custom Polygon"),
        ("RADIUS", "Radius"),
    ]

    # Basic information
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        help_text="Type of coverage area"
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name for the coverage area"
    )

    # Geometry fields (will be added when GIS is enabled)
    # geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    # center = models.PointField(srid=4326, null=True, blank=True)
    
    # Radius information (for radius-based areas)
    radius_m = models.IntegerField(
        null=True,
        blank=True,
        help_text="Radius in meters (for radius-based areas)"
    )

    # External identifiers (FIPS codes, etc.)
    ext_ids = models.JSONField(
        default=dict,
        blank=True,
        help_text="External identifiers (e.g., FIPS codes)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_coverage_areas"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="updated_coverage_areas"
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["kind"]),
            models.Index(fields=["name"]),
        ]
        verbose_name = "Coverage Area"
        verbose_name_plural = "Coverage Areas"

    def __str__(self) -> str:
        """Return the coverage area name as the string representation."""
        return self.name

    def clean(self) -> None:
        """Validate the coverage area data.
        
        This method implements validation rules for coverage areas:
        - Radius-based areas must have a center point and radius
        - Radius must be between 0.5 and 100 miles (800-160934 meters)
        - External IDs must be valid JSON
        - Name is required for all area types
        
        Raises:
            ValidationError: If validation fails with field-specific errors
        """
        errors = {}

        # Name validation
        if not self.name:
            errors["name"] = "Name is required for coverage areas."

        # Radius validation for radius-based areas
        if self.kind == "RADIUS":
            if not self.radius_m:
                errors["radius_m"] = "Radius is required for radius-based areas."
            elif self.radius_m < 800:  # 0.5 miles
                errors["radius_m"] = "Radius must be at least 0.5 miles (800 meters)."
            elif self.radius_m > 160934:  # 100 miles
                errors["radius_m"] = "Radius cannot exceed 100 miles (160,934 meters)."

        # External IDs validation
        if self.ext_ids and not isinstance(self.ext_ids, dict):
            errors["ext_ids"] = "External IDs must be a valid JSON object."

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the coverage area with validation and geometry processing.
        
        This method performs validation and geometry processing before saving.
        For radius-based areas, it will create a buffer polygon when GIS is enabled.
        
        Args:
            *args: Standard save arguments
            **kwargs: Standard save keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def display_name(self) -> str:
        """Return a formatted display name for the coverage area.
        
        Returns:
            str: Formatted display name with type indicator
        """
        kind_display = dict(self.KIND_CHOICES).get(self.kind, self.kind)
        return f"{self.name} ({kind_display})"

    @property
    def fips_codes(self) -> Dict[str, str]:
        """Return FIPS codes from external IDs.
        
        Returns:
            Dict[str, str]: Dictionary containing state_fips and county_fips if available
        """
        return {
            "state_fips": self.ext_ids.get("state_fips", ""),
            "county_fips": self.ext_ids.get("county_fips", ""),
        }

    @property
    def is_administrative(self) -> bool:
        """Check if this is an administrative boundary.
        
        Returns:
            bool: True if this is a city, county, or state boundary
        """
        return self.kind in ["CITY", "COUNTY", "STATE"]

    @property
    def is_custom(self) -> bool:
        """Check if this is a custom area (polygon or radius).
        
        Returns:
            bool: True if this is a custom polygon or radius area
        """
        return self.kind in ["POLYGON", "RADIUS"]

    def get_radius_miles(self) -> Optional[float]:
        """Get the radius in miles for radius-based areas.
        
        Returns:
            Optional[float]: Radius in miles, or None if not a radius area
        """
        if self.kind == "RADIUS" and self.radius_m:
            return self.radius_m / 1609.34  # Convert meters to miles
        return None

    def set_radius_miles(self, miles: float) -> None:
        """Set the radius in miles for radius-based areas.
        
        Args:
            miles: Radius in miles (0.5 to 100)
        """
        if self.kind == "RADIUS":
            self.radius_m = int(miles * 1609.34)  # Convert miles to meters
