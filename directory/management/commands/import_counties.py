"""
Management command to import county boundaries from TIGER/Line data.

This command downloads county shapefiles from the U.S. Census Bureau TIGER/Line
files and creates CoverageArea records for each county. The command handles
coordinate system conversion, geometry validation, and FIPS code mapping.

Features:
- Downloads county shapefiles for specified states or all states
- Converts coordinates to WGS84 (SRID 4326)
- Creates CoverageArea records with COUNTY kind
- Maps FIPS codes and county names
- Provides progress tracking and error handling
- Supports incremental updates and data validation

Usage:
    python manage.py import_counties --states KY,TN,VA
    python manage.py import_counties --all-states
    python manage.py import_counties --validate-only

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import zipfile
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction

from directory.models import CoverageArea

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import county boundaries from TIGER/Line data."""

    help = "Import county boundaries from U.S. Census TIGER/Line files"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--states",
            type=str,
            help="Comma-separated list of state FIPS codes (e.g., '21,47,51' for KY,TN,VA)",
        )
        parser.add_argument(
            "--all-states",
            action="store_true",
            help="Import counties for all states (this will take a long time)",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=2023,
            help="TIGER/Line year to use (default: 2023)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing county coverage areas before importing",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate existing county data without importing",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            help="Directory to save downloaded files (default: temp directory)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        year = options["year"]
        clear_existing = options["clear_existing"]
        validate_only = options["validate_only"]
        output_dir = options["output_dir"]
        
        # Check if GIS is enabled
        if not getattr(settings, 'GIS_ENABLED', False):
            self.stdout.write(
                self.style.WARNING(
                    "GIS is not enabled. This command requires GIS functionality. "
                    "Set GIS_ENABLED=1 in your environment to enable."
                )
            )
            return

        # Get or create default user for importing
        default_user, created = User.objects.get_or_create(
            username="tiger_importer",
            defaults={
                "email": "tiger@example.com",
                "first_name": "TIGER",
                "last_name": "Importer",
            }
        )
        if created:
            self.stdout.write("Created default user for TIGER imports")

        # Determine which states to process
        if options["all_states"]:
            state_fips_codes = self._get_all_state_fips_codes()
            self.stdout.write(f"Importing counties for all {len(state_fips_codes)} states")
        elif options["states"]:
            state_fips_codes = [code.strip() for code in options["states"].split(",")]
            self.stdout.write(f"Importing counties for states: {', '.join(state_fips_codes)}")
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please specify --states or --all-states"
                )
            )
            return

        # Clear existing county data if requested
        if clear_existing:
            self.stdout.write("Clearing existing county coverage areas...")
            deleted_count = CoverageArea.objects.filter(kind="COUNTY").delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} existing county coverage areas")
            )

        # Validate existing data if requested
        if validate_only:
            self._validate_existing_counties()
            return

        # Process each state
        total_imported = 0
        total_errors = 0
        
        for state_fips in state_fips_codes:
            try:
                imported, errors = self._import_state_counties(
                    state_fips, year, default_user, output_dir
                )
                total_imported += imported
                total_errors += errors
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing state {state_fips}: {str(e)}")
                )
                total_errors += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed! Imported: {total_imported}, Errors: {total_errors}"
            )
        )

    def _get_all_state_fips_codes(self) -> List[str]:
        """Get FIPS codes for all U.S. states and territories.
        
        Returns:
            List of state FIPS codes as strings
        """
        # This is a simplified list - in production, you might want to
        # fetch this from a more comprehensive source
        return [
            "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19",
            "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
            "36", "37", "38", "39", "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
            "54", "55", "56", "60", "66", "69", "72", "78"
        ]

    def _import_state_counties(
        self, 
        state_fips: str, 
        year: int, 
        default_user: User,
        output_dir: Optional[str]
    ) -> Tuple[int, int]:
        """Import counties for a specific state.
        
        Args:
            state_fips: State FIPS code
            year: TIGER/Line year
            default_user: User for creating records
            output_dir: Directory to save downloaded files
            
        Returns:
            Tuple of (imported_count, error_count)
        """
        self.stdout.write(f"Processing state {state_fips}...")
        
        # Download and extract shapefile
        shapefile_path = self._download_state_counties(state_fips, year, output_dir)
        if not shapefile_path:
            return 0, 1

        try:
            # Process the shapefile
            imported, errors = self._process_county_shapefile(
                shapefile_path, state_fips, default_user
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"State {state_fips}: Imported {imported} counties, {errors} errors"
                )
            )
            
            return imported, errors
            
        finally:
            # Clean up downloaded files
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)

    def _download_state_counties(
        self, 
        state_fips: str, 
        year: int,
        output_dir: Optional[str]
    ) -> Optional[str]:
        """Download county shapefile for a state.
        
        Args:
            state_fips: State FIPS code
            year: TIGER/Line year
            output_dir: Directory to save files
            
        Returns:
            Path to extracted shapefile or None if failed
        """
        # TIGER/Line URL format
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_{state_fips}_county.zip"
        
        # Create output directory
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            temp_dir = output_dir
        else:
            temp_dir = tempfile.mkdtemp()
        
        zip_path = os.path.join(temp_dir, f"tl_{year}_{state_fips}_county.zip")
        extract_path = os.path.join(temp_dir, f"tl_{year}_{state_fips}_county")
        
        try:
            # Download the file
            self.stdout.write(f"Downloading {url}...")
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Find the .shp file
            shp_files = [f for f in os.listdir(extract_path) if f.endswith('.shp')]
            if not shp_files:
                self.stdout.write(
                    self.style.ERROR(f"No shapefile found in {extract_path}")
                )
                return None
            
            return os.path.join(extract_path, shp_files[0])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error downloading/extracting {url}: {str(e)}")
            )
            return None

    def _process_county_shapefile(
        self, 
        shapefile_path: str, 
        state_fips: str,
        default_user: User
    ) -> Tuple[int, int]:
        """Process county shapefile and create CoverageArea records.
        
        Args:
            shapefile_path: Path to the shapefile
            state_fips: State FIPS code
            default_user: User for creating records
            
        Returns:
            Tuple of (imported_count, error_count)
        """
        if not getattr(settings, 'GIS_ENABLED', False):
            self.stdout.write(
                self.style.WARNING("GIS not enabled, skipping geometry processing")
            )
            return 0, 0

        try:
            import fiona
            from django.contrib.gis.geos import GEOSGeometry
            from django.contrib.gis.gdal import SpatialReference
            
            imported_count = 0
            error_count = 0
            
            # Open the shapefile
            with fiona.open(shapefile_path) as src:
                # Get the coordinate reference system
                crs = SpatialReference(src.crs)
                
                # Check if we need to transform coordinates
                needs_transform = crs.srid != 4326
                
                self.stdout.write(f"Processing {len(src)} counties...")
                
                for feature in src:
                    try:
                        # Extract county data
                        properties = feature['properties']
                        county_fips = properties.get('COUNTYFP', '')
                        county_name = properties.get('NAME', '')
                        
                        if not county_fips or not county_name:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Skipping county with missing FIPS or name: {properties}"
                                )
                            )
                            error_count += 1
                            continue
                        
                        # Create full FIPS code (state + county)
                        full_fips = f"{state_fips}{county_fips}"
                        
                        # Check if county already exists
                        if CoverageArea.objects.filter(
                            kind="COUNTY",
                            ext_ids__state_fips=state_fips,
                            ext_ids__county_fips=county_fips
                        ).exists():
                            self.stdout.write(
                                self.style.WARNING(
                                    f"County {county_name} ({full_fips}) already exists, skipping"
                                )
                            )
                            continue
                        
                        # Process geometry
                        geometry = GEOSGeometry(str(feature['geometry']))
                        
                        # Transform to WGS84 if needed
                        if needs_transform:
                            geometry.transform(4326)
                        
                        # Create ext_ids structure
                        ext_ids = {
                            "state_fips": state_fips,
                            "county_fips": county_fips,
                            "full_fips": full_fips,
                            "state_name": self._get_state_name(state_fips),
                            "county_name": county_name,
                        }
                        
                        # Create CoverageArea record
                        with transaction.atomic():
                            coverage_area = CoverageArea.objects.create(
                                kind="COUNTY",
                                name=f"{county_name} County",
                                geom=geometry,
                                center=geometry.centroid,
                                ext_ids=ext_ids,
                                created_by=default_user,
                                updated_by=default_user,
                            )
                        
                        imported_count += 1
                        
                        if imported_count % 10 == 0:
                            self.stdout.write(f"Imported {imported_count} counties...")
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error processing county {properties.get('NAME', 'Unknown')}: {str(e)}"
                            )
                        )
                        error_count += 1
            
            return imported_count, error_count
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("Fiona library not available for shapefile processing")
            )
            return 0, 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing shapefile: {str(e)}")
            )
            return 0, 1

    def _get_state_name(self, state_fips: str) -> str:
        """Get state name from FIPS code.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            State name
        """
        # Simplified state name mapping - in production, you might want
        # to use a more comprehensive source
        state_names = {
            "21": "Kentucky",
            "47": "Tennessee", 
            "51": "Virginia",
            # Add more states as needed
        }
        return state_names.get(state_fips, f"State {state_fips}")

    def _validate_existing_counties(self) -> None:
        """Validate existing county coverage areas.
        
        This method checks the integrity of existing county data and
        reports any issues found.
        """
        self.stdout.write("Validating existing county coverage areas...")
        
        counties = CoverageArea.objects.filter(kind="COUNTY")
        total_counties = counties.count()
        
        if total_counties == 0:
            self.stdout.write("No county coverage areas found")
            return
        
        # Check for missing required fields
        missing_geom = counties.filter(geom__isnull=True).count()
        missing_center = counties.filter(center__isnull=True).count()
        missing_ext_ids = counties.filter(ext_ids__isnull=True).count()
        
        # Check for invalid FIPS codes
        invalid_fips = 0
        for county in counties:
            ext_ids = county.ext_ids or {}
            if not ext_ids.get('full_fips') or len(ext_ids.get('full_fips', '')) != 5:
                invalid_fips += 1
        
        # Report results
        self.stdout.write(f"Total counties: {total_counties}")
        self.stdout.write(f"Missing geometry: {missing_geom}")
        self.stdout.write(f"Missing center point: {missing_center}")
        self.stdout.write(f"Missing ext_ids: {missing_ext_ids}")
        self.stdout.write(f"Invalid FIPS codes: {invalid_fips}")
        
        if missing_geom == 0 and missing_center == 0 and missing_ext_ids == 0 and invalid_fips == 0:
            self.stdout.write(
                self.style.SUCCESS("All county coverage areas are valid!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Some county coverage areas have issues")
            )
