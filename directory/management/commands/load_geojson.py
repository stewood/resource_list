"""Management command to load GeoJSON files into CoverageArea model.

This command allows importing custom geometry data from GeoJSON files,
with comprehensive validation, geometry processing, and error handling.

Usage:
    python manage.py load_geojson path/to/file.geojson --name "Custom Area"
    python manage.py load_geojson path/to/file.geojson --kind CUSTOM --validate-only
    python manage.py load_geojson path/to/file.geojson --simplify-geometry

Features:
    - GeoJSON format validation
    - SRID conversion to WGS84 (EPSG:4326)
    - Geometry validation and simplification
    - Duplicate detection
    - Comprehensive error handling
    - Batch processing for multiple features

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError

from directory.models import CoverageArea

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Load GeoJSON files into CoverageArea model."""

    help = "Import custom geometry data from GeoJSON files"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "geojson_file",
            type=str,
            help="Path to the GeoJSON file to import",
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Name for the coverage area (if single feature)",
        )
        parser.add_argument(
            "--kind",
            type=str,
            default="POLYGON",
            choices=["POLYGON", "RADIUS", "CITY", "COUNTY", "STATE"],
            help="Kind of coverage area (default: POLYGON)",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate the GeoJSON file without importing",
        )
        parser.add_argument(
            "--simplify-geometry",
            action="store_true",
            help="Simplify geometry for better performance",
        )
        parser.add_argument(
            "--simplify-tolerance",
            type=float,
            default=0.001,
            help="Tolerance for geometry simplification (default: 0.001)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing custom coverage areas before importing",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing coverage areas with matching names",
        )
        parser.add_argument(
            "--max-vertices",
            type=int,
            default=10000,
            help="Maximum number of vertices per geometry (default: 10000)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        geojson_file = options["geojson_file"]
        validate_only = options["validate_only"]
        
        # Check if GIS is enabled
        if not getattr(settings, 'GIS_ENABLED', False):
            self.stdout.write(
                self.style.WARNING(
                    "GIS is not enabled. This command requires GIS functionality. "
                    "Set GIS_ENABLED=1 in your environment to enable."
                )
            )
            return

        # Validate file exists
        if not os.path.exists(geojson_file):
            raise CommandError(f"GeoJSON file not found: {geojson_file}")

        # Get or create default user for importing
        default_user, created = User.objects.get_or_create(
            username="geojson_importer",
            defaults={
                "email": "geojson@example.com",
                "first_name": "GeoJSON",
                "last_name": "Importer",
            }
        )
        if created:
            self.stdout.write("Created default user for GeoJSON imports")

        try:
            # Load and validate GeoJSON
            self.stdout.write(f"Loading GeoJSON file: {geojson_file}")
            geojson_data = self._load_geojson(geojson_file)
            
            # Validate GeoJSON structure
            validation_errors = self._validate_geojson(geojson_data, options)
            
            if validation_errors:
                self.stdout.write(
                    self.style.ERROR(f"GeoJSON validation failed with {len(validation_errors)} errors:")
                )
                for error in validation_errors:
                    self.stdout.write(f"  - {error}")
                return
            
            self.stdout.write(
                self.style.SUCCESS("GeoJSON validation passed")
            )
            
            if validate_only:
                self.stdout.write("Validation complete. Use without --validate-only to import.")
                return
            
            # Clear existing areas if requested
            if options["clear_existing"]:
                self._clear_existing_areas(options["kind"])
            
            # Process and import features
            imported, errors = self._import_features(geojson_data, options, default_user)
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"Import completed! Imported: {imported}, Errors: {errors}"
                )
            )
            
        except Exception as e:
            raise CommandError(f"Error processing GeoJSON file: {str(e)}")

    def _load_geojson(self, file_path: str) -> Dict[str, Any]:
        """Load GeoJSON from file.
        
        Args:
            file_path: Path to GeoJSON file
            
        Returns:
            Parsed GeoJSON data
            
        Raises:
            CommandError: If file cannot be loaded or parsed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stdout.write(f"Loaded GeoJSON with {len(data.get('features', []))} features")
            return data
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in file {file_path}: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error reading file {file_path}: {str(e)}")

    def _validate_geojson(self, geojson_data: Dict[str, Any], options: Dict[str, Any]) -> List[str]:
        """Validate GeoJSON structure and content.
        
        Args:
            geojson_data: Parsed GeoJSON data
            options: Command options
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check basic GeoJSON structure
        if not isinstance(geojson_data, dict):
            errors.append("GeoJSON must be a JSON object")
            return errors
        
        if geojson_data.get("type") != "FeatureCollection":
            errors.append("GeoJSON must be a FeatureCollection")
        
        features = geojson_data.get("features", [])
        if not features:
            errors.append("GeoJSON must contain at least one feature")
            return errors
        
        if not isinstance(features, list):
            errors.append("Features must be a list")
            return errors
        
        max_vertices = options.get("max_vertices", 10000)
        
        # Validate each feature
        for i, feature in enumerate(features):
            if not isinstance(feature, dict):
                errors.append(f"Feature {i} must be a JSON object")
                continue
            
            if feature.get("type") != "Feature":
                errors.append(f"Feature {i} must have type 'Feature'")
            
            geometry = feature.get("geometry")
            if not geometry:
                errors.append(f"Feature {i} must have geometry")
                continue
            
            # Validate geometry
            try:
                geom = GEOSGeometry(json.dumps(geometry))
                
                # Check geometry type
                if geom.geom_type not in ["Polygon", "MultiPolygon"]:
                    errors.append(
                        f"Feature {i} has unsupported geometry type: {geom.geom_type}. "
                        "Only Polygon and MultiPolygon are supported."
                    )
                
                # Check vertex count
                vertex_count = self._count_vertices(geom)
                if vertex_count > max_vertices:
                    errors.append(
                        f"Feature {i} has {vertex_count} vertices, "
                        f"exceeding maximum of {max_vertices}"
                    )
                
                # Check for valid geometry
                if not geom.valid:
                    errors.append(f"Feature {i} has invalid geometry: {geom.valid_reason}")
                
            except Exception as e:
                errors.append(f"Feature {i} has invalid geometry: {str(e)}")
        
        return errors

    def _count_vertices(self, geometry: GEOSGeometry) -> int:
        """Count vertices in a geometry.
        
        Args:
            geometry: GEOS geometry object
            
        Returns:
            Total number of vertices
        """
        if geometry.geom_type == "Polygon":
            return len(geometry.coords[0])  # Exterior ring
        elif geometry.geom_type == "MultiPolygon":
            total = 0
            for polygon in geometry:
                total += len(polygon.coords[0])  # Exterior ring of each polygon
            return total
        else:
            return 0

    def _clear_existing_areas(self, kind: str) -> None:
        """Clear existing coverage areas of the specified kind.
        
        Args:
            kind: Kind of coverage areas to clear
        """
        self.stdout.write(f"Clearing existing {kind} coverage areas...")
        deleted_count = CoverageArea.objects.filter(kind=kind).delete()[0]
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} existing {kind} coverage areas")
        )

    def _import_features(
        self, 
        geojson_data: Dict[str, Any], 
        options: Dict[str, Any], 
        default_user: User
    ) -> Tuple[int, int]:
        """Import GeoJSON features into CoverageArea model.
        
        Args:
            geojson_data: Parsed GeoJSON data
            options: Command options
            default_user: User for creating records
            
        Returns:
            Tuple of (imported_count, error_count)
        """
        features = geojson_data.get("features", [])
        imported_count = 0
        error_count = 0
        
        kind = options.get("kind", "CUSTOM")
        simplify_geometry = options.get("simplify_geometry", False)
        simplify_tolerance = options.get("simplify_tolerance", 0.001)
        update_existing = options.get("update_existing", False)
        name_override = options.get("name")
        
        self.stdout.write(f"Processing {len(features)} features...")
        
        for i, feature in enumerate(features):
            try:
                with transaction.atomic():
                    # Extract properties
                    properties = feature.get("properties", {})
                    
                    # Determine name
                    if name_override and len(features) == 1:
                        # Use provided name for single feature
                        area_name = name_override
                    elif properties.get("name"):
                        area_name = properties["name"]
                    elif properties.get("NAME"):
                        area_name = properties["NAME"]
                    else:
                        area_name = f"Custom Area {i + 1}"
                    
                    # Create geometry
                    geometry = GEOSGeometry(json.dumps(feature["geometry"]))
                    
                    # Convert to WGS84 if needed
                    if geometry.srid != 4326:
                        geometry.transform(4326)
                    
                    # Ensure MultiPolygon for database compatibility
                    if geometry.geom_type == "Polygon":
                        geometry = MultiPolygon(geometry)
                    
                    # Simplify geometry if requested
                    if simplify_geometry:
                        original_vertices = self._count_vertices(geometry)
                        geometry = geometry.simplify(simplify_tolerance, preserve_topology=True)
                        
                        # Ensure result is still MultiPolygon after simplification
                        if geometry.geom_type == "Polygon":
                            geometry = MultiPolygon(geometry)
                        
                        simplified_vertices = self._count_vertices(geometry)
                        self.stdout.write(
                            f"Simplified geometry for {area_name}: "
                            f"{original_vertices} -> {simplified_vertices} vertices"
                        )
                    
                    # Check for existing area
                    existing_area = None
                    if update_existing:
                        existing_area = CoverageArea.objects.filter(
                            kind=kind,
                            name=area_name
                        ).first()
                    
                    # Create ext_ids from properties
                    ext_ids = {}
                    for key, value in properties.items():
                        if isinstance(value, (str, int, float, bool)) and key.lower() not in ["geometry"]:
                            ext_ids[key] = value
                    
                    if existing_area:
                        # Update existing area
                        existing_area.geom = geometry
                        existing_area.center = geometry.centroid
                        existing_area.ext_ids = ext_ids
                        existing_area.updated_by = default_user
                        existing_area.save()
                        
                        self.stdout.write(f"Updated existing area: {area_name}")
                    else:
                        # Create new area
                        coverage_area = CoverageArea.objects.create(
                            kind=kind,
                            name=area_name,
                            geom=geometry,
                            center=geometry.centroid,
                            ext_ids=ext_ids,
                            created_by=default_user,
                            updated_by=default_user,
                        )
                        
                        self.stdout.write(f"Created new area: {area_name}")
                    
                    imported_count += 1
                    
            except ValidationError as e:
                error_msg = f"Validation error for feature {i}: {e}"
                self.stdout.write(self.style.ERROR(error_msg))
                error_count += 1
                
            except Exception as e:
                error_msg = f"Error processing feature {i}: {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                error_count += 1
        
        return imported_count, error_count
