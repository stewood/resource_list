"""
Management command to import state boundaries from TIGER/Line data.

This command downloads state shapefiles from the U.S. Census Bureau TIGER/Line
files and creates CoverageArea records for each state. The command handles
coordinate system conversion, geometry validation, and FIPS code mapping.

Features:
- Downloads state shapefiles for specified states or all states
- Converts coordinates to WGS84 (SRID 4326)
- Creates CoverageArea records with STATE kind
- Maps FIPS codes and state names
- Provides progress tracking and error handling
- Supports incremental updates and data validation

Usage:
    python manage.py import_states --states KY,TN,VA
    python manage.py import_states --all-states
    python manage.py import_states --validate-only

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
    """Import state boundaries from TIGER/Line data."""

    help = "Import state boundaries from U.S. Census TIGER/Line files"

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
            help="Import all states (this will take a long time)",
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
            help="Clear existing state coverage areas before importing",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate existing state data without importing",
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

        # Validate existing data if requested (can run without specifying states)
        if validate_only:
            self._validate_existing_states()
            return

        # Determine which states to process
        if options["all_states"]:
            state_fips_codes = self._get_all_state_fips_codes()
            self.stdout.write(f"Importing all {len(state_fips_codes)} states")
        elif options["states"]:
            state_fips_codes = [code.strip() for code in options["states"].split(",")]
            self.stdout.write(f"Importing states: {', '.join(state_fips_codes)}")
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please specify --states or --all-states"
                )
            )
            return

        # Clear existing state data if requested
        if clear_existing:
            self.stdout.write("Clearing existing state coverage areas...")
            deleted_count = CoverageArea.objects.filter(kind="STATE").delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} existing state coverage areas")
            )



        # Process each state
        total_imported = 0
        total_errors = 0
        
        for state_fips in state_fips_codes:
            try:
                imported, errors = self._import_state(
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

    def _import_state(
        self, 
        state_fips: str, 
        year: int, 
        default_user: User,
        output_dir: Optional[str]
    ) -> Tuple[int, int]:
        """Import a specific state.
        
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
        shapefile_path = self._download_state(state_fips, year, output_dir)
        if not shapefile_path:
            return 0, 1

        try:
            # Process the shapefile
            imported, errors = self._process_state_shapefile(
                shapefile_path, state_fips, default_user
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"State {state_fips}: Imported {imported} states, {errors} errors"
                )
            )
            
            return imported, errors
            
        finally:
            # Clean up downloaded files
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)

    def _download_state(
        self, 
        state_fips: str, 
        year: int,
        output_dir: Optional[str]
    ) -> Optional[str]:
        """Download state shapefile.
        
        Args:
            state_fips: State FIPS code (not used for download, but kept for interface consistency)
            year: TIGER/Line year
            output_dir: Directory to save files
            
        Returns:
            Path to extracted shapefile or None if failed
        """
        # TIGER/Line URL format for states (single file for all states)
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/STATE/tl_{year}_us_state.zip"
        
        # Create output directory
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            temp_dir = output_dir
        else:
            temp_dir = tempfile.mkdtemp()
        
        zip_path = os.path.join(temp_dir, f"tl_{year}_us_state.zip")
        extract_path = os.path.join(temp_dir, f"tl_{year}_us_state")
        
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

    def _process_state_shapefile(
        self, 
        shapefile_path: str, 
        state_fips: str,
        default_user: User
    ) -> Tuple[int, int]:
        """Process state shapefile and create CoverageArea records.
        
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
                
                self.stdout.write(f"Processing {len(src)} state features...")
                
                for feature in src:
                    try:
                        # Extract state data
                        properties = feature['properties']
                        state_name = properties.get('NAME', '')
                        feature_state_fips = properties.get('STATEFP', '')
                        
                        # Filter for the specific state we want
                        if feature_state_fips != state_fips:
                            continue
                        
                        if not state_name:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Skipping state with missing name: {properties}"
                                )
                            )
                            error_count += 1
                            continue
                        
                        # Check if state already exists
                        if CoverageArea.objects.filter(
                            kind="STATE",
                            ext_ids__state_fips=state_fips
                        ).exists():
                            self.stdout.write(
                                self.style.WARNING(
                                    f"State {state_name} ({state_fips}) already exists, skipping"
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
                            "state_name": state_name,
                            "state_abbr": self._get_state_abbreviation(state_fips),
                        }
                        
                        # Create CoverageArea record
                        with transaction.atomic():
                            coverage_area = CoverageArea.objects.create(
                                kind="STATE",
                                name=f"{state_name}",
                                geom=geometry,
                                center=geometry.centroid,
                                ext_ids=ext_ids,
                                created_by=default_user,
                                updated_by=default_user,
                            )
                        
                        imported_count += 1
                        self.stdout.write(f"Imported state: {state_name}")
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error processing state {properties.get('NAME', 'Unknown')}: {str(e)}"
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

    def _get_state_abbreviation(self, state_fips: str) -> str:
        """Get state abbreviation from FIPS code.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            State abbreviation
        """
        # State FIPS to abbreviation mapping
        state_abbreviations = {
            "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
            "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
            "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
            "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
            "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
            "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
            "54": "WV", "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI"
        }
        return state_abbreviations.get(state_fips, f"ST{state_fips}")

    def _validate_existing_states(self) -> None:
        """Validate existing state coverage areas.
        
        This method checks the integrity of existing state data and
        reports any issues found.
        """
        self.stdout.write("Validating existing state coverage areas...")
        
        states = CoverageArea.objects.filter(kind="STATE")
        total_states = states.count()
        
        if total_states == 0:
            self.stdout.write("No state coverage areas found")
            return
        
        # Check for missing required fields
        missing_geom = states.filter(geom__isnull=True).count()
        missing_center = states.filter(center__isnull=True).count()
        missing_ext_ids = states.filter(ext_ids__isnull=True).count()
        
        # Check for invalid FIPS codes
        invalid_fips = 0
        for state in states:
            ext_ids = state.ext_ids or {}
            if not ext_ids.get('state_fips') or len(ext_ids.get('state_fips', '')) != 2:
                invalid_fips += 1
        
        # Report results
        self.stdout.write(f"Total states: {total_states}")
        self.stdout.write(f"Missing geometry: {missing_geom}")
        self.stdout.write(f"Missing center point: {missing_center}")
        self.stdout.write(f"Missing ext_ids: {missing_ext_ids}")
        self.stdout.write(f"Invalid FIPS codes: {invalid_fips}")
        
        if missing_geom == 0 and missing_center == 0 and missing_ext_ids == 0 and invalid_fips == 0:
            self.stdout.write(
                self.style.SUCCESS("All state coverage areas are valid!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Some state coverage areas have issues")
            )
