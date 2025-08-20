"""Simplified management command to import county boundaries from TIGER/Line data.

This is an alternative approach to avoid the segmentation fault in the main
import_counties command. It uses a different strategy for processing shapefiles.

Usage:
    python manage.py import_counties_simple --states KY,TN,VA

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import zipfile
import tempfile
import urllib.request
import json
from typing import Any, Dict, List, Optional, Tuple
import logging

# Import Shapely first to avoid segmentation fault with Fiona
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction

from directory.models import CoverageArea

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import county boundaries using simplified approach."""

    help = "Import county boundaries using alternative processing method"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--states",
            type=str,
            help="Comma-separated list of state FIPS codes (e.g., '21' for KY)",
        )
        parser.add_argument(
            "--all-states",
            action="store_true",
            help="Import counties for all US states",
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
            "--update-existing",
            action="store_true",
            help="Update existing county records with new data",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        year = options["year"]
        clear_existing = options["clear_existing"]
        update_existing = options.get("update_existing", False)
        
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
            username="tiger_county_importer_simple",
            defaults={
                "email": "tiger_county_simple@example.com",
                "first_name": "TIGER",
                "last_name": "County Importer Simple",
            }
        )

        # Determine which states to process
        if options["all_states"]:
            state_fips_codes = self._get_all_state_fips_codes()
            self.stdout.write(f"Importing counties for all {len(state_fips_codes)} states")
        elif options["states"]:
            state_fips_codes = [code.strip() for code in options["states"].split(",")]
            self.stdout.write(f"Importing counties for states: {', '.join(state_fips_codes)}")
        else:
            self.stdout.write(
                self.style.ERROR("Please specify --states or --all-states")
            )
            return

        # Clear existing county data if requested
        if clear_existing:
            self.stdout.write("Clearing existing county coverage areas...")
            deleted_count = CoverageArea.objects.filter(kind="COUNTY").delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} existing county coverage areas")
            )

        # Process each state
        total_imported = 0
        total_errors = 0
        
        for state_fips in state_fips_codes:
            try:
                imported, errors = self._import_state_counties_simple(
                    state_fips, year, default_user
                )
                total_imported += imported
                total_errors += errors
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing counties for state {state_fips}: {str(e)}")
                )
                total_errors += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed! Imported: {total_imported}, Errors: {total_errors}"
            )
        )

    def _import_state_counties_simple(
        self, 
        state_fips: str, 
        year: int, 
        default_user: User
    ) -> Tuple[int, int]:
        """Import counties for a specific state using simplified approach.
        
        Args:
            state_fips: State FIPS code
            year: TIGER/Line year
            default_user: User for creating records
            
        Returns:
            Tuple of (imported_count, error_count)
        """
        self.stdout.write(f"Processing counties for state {state_fips} with simple method...")
        
        # Download and extract shapefile
        shapefile_path = self._download_counties_simple(year)
        if not shapefile_path:
            return 0, 1

        try:
            # Process the shapefile using alternative method
            imported, errors = self._process_counties_simple(
                shapefile_path, state_fips, default_user
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"State {state_fips}: Imported {imported} counties, {errors} errors"
                )
            )
            
            return imported, errors
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing counties for state {state_fips}: {str(e)}")
            )
            # Clean up on error
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)
            return 0, 1

    def _download_counties_simple(
        self, 
        year: int
    ) -> Optional[str]:
        """Download county shapefile using simple method.
        
        Args:
            year: TIGER/Line year
            
        Returns:
            Path to extracted shapefile or None if failed
        """
        # TIGER/Line URL format for counties (single file for all counties)
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip"
        
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"tl_{year}_us_county.zip")
        extract_path = os.path.join(temp_dir, f"tl_{year}_us_county")
        
        try:
            # Download the file with SSL verification disabled
            self.stdout.write(f"Downloading {url}...")
            self.stdout.write(f"File will be saved to: {zip_path}")
            
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.stdout.write(f"\rDownload progress: {percent:.1f}%", ending='')
            
            self.stdout.write("\nDownload completed!")
            
            # Check file size
            file_size = os.path.getsize(zip_path)
            self.stdout.write(f"Downloaded file size: {file_size} bytes")
            
            # Extract the zip file
            self.stdout.write(f"Extracting to {extract_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # List contents first
                file_list = zip_ref.namelist()
                self.stdout.write(f"Zip contains {len(file_list)} files:")
                for file in file_list[:5]:  # Show first 5 files
                    self.stdout.write(f"  - {file}")
                if len(file_list) > 5:
                    self.stdout.write(f"  ... and {len(file_list) - 5} more files")
                
                zip_ref.extractall(extract_path)
            
            # List extracted files
            self.stdout.write(f"Extracted files in {extract_path}:")
            for file in os.listdir(extract_path):
                self.stdout.write(f"  - {file}")
            
            # Find the .shp file
            shp_files = [f for f in os.listdir(extract_path) if f.endswith('.shp')]
            if not shp_files:
                self.stdout.write(
                    self.style.ERROR(f"No shapefile found in {extract_path}")
                )
                return None
            
            shapefile_path = os.path.join(extract_path, shp_files[0])
            self.stdout.write(f"Found shapefile: {shapefile_path}")
            
            # Verify file exists and has content
            if os.path.exists(shapefile_path):
                file_size = os.path.getsize(shapefile_path)
                self.stdout.write(f"Shapefile size: {file_size} bytes")
            else:
                self.stdout.write(self.style.ERROR("Shapefile does not exist after extraction!"))
                return None
            
            return shapefile_path
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error downloading/extracting {url}: {str(e)}")
            )
            return None

    def _process_counties_simple(
        self, 
        shapefile_path: str, 
        state_fips: str,
        default_user: User
    ) -> Tuple[int, int]:
        """Process county shapefile using simplified approach.
        
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
            # Try using ogr2ogr approach first (avoids Fiona for geometry processing)
            return self._process_counties_with_ogr2ogr(shapefile_path, state_fips, default_user)
        except Exception as e:
            self.stdout.write(f"ogr2ogr approach failed: {e}")
            return 0, 1

    def _process_counties_with_ogr2ogr(
        self, 
        shapefile_path: str, 
        state_fips: str,
        default_user: User
    ) -> Tuple[int, int]:
        """Process using ogr2ogr command line tool.
        
        Args:
            shapefile_path: Path to the shapefile
            state_fips: State FIPS code
            default_user: User for creating records
            
        Returns:
            Tuple of (imported_count, error_count)
        """
        self.stdout.write("Attempting ogr2ogr processing...")
        
        # Use ogr2ogr to convert to GeoJSON
        import subprocess
        import tempfile
        
        # Create a unique temporary file
        geojson_path = tempfile.mktemp(suffix='.geojson')
        
        try:
            # Convert shapefile to GeoJSON using ogr2ogr
            # Use absolute paths to avoid "Unable to open datasource" error
            cmd = [
                'ogr2ogr',
                '-f', 'GeoJSON',
                '-t_srs', 'EPSG:4326',  # Convert to WGS84
                os.path.abspath(geojson_path),
                os.path.abspath(shapefile_path)
            ]
            
            self.stdout.write(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.stdout.write(f"ogr2ogr failed: {result.stderr}")
                return 0, 1
            
            # Verify the GeoJSON file was created successfully
            if not os.path.exists(geojson_path):
                self.stdout.write(f"ogr2ogr did not create output file: {geojson_path}")
                return 0, 1
            
            # Read the GeoJSON file
            with open(geojson_path, 'r') as f:
                geojson_data = json.load(f)
            
            # Process features
            imported_count = 0
            error_count = 0
            
            for feature in geojson_data.get('features', []):
                try:
                    properties = feature.get('properties', {})
                    county_name = properties.get('NAME', '')
                    feature_state_fips = properties.get('STATEFP', '')
                    county_fips = properties.get('COUNTYFP', '')
                    
                    # Filter for the specific state we want
                    if feature_state_fips != state_fips:
                        continue
                    
                    if not county_name or not county_fips:
                        self.stdout.write(
                            self.style.WARNING(f"Skipping county with missing name or FIPS")
                        )
                        error_count += 1
                        continue
                    
                    # Check if county already exists
                    existing_county = CoverageArea.objects.filter(
                        kind="COUNTY",
                        ext_ids__state_fips=state_fips,
                        ext_ids__county_fips=county_fips
                    ).first()
                    
                    if existing_county and not update_existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f"County {county_name} ({state_fips}{county_fips}) already exists, skipping"
                            )
                        )
                        continue
                    
                    if existing_county and update_existing:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updating existing county {county_name} ({state_fips}{county_fips})"
                            )
                        )
                    
                    # Create geometry from GeoJSON
                    geometry = GEOSGeometry(json.dumps(feature['geometry']))
                    
                    # Ensure geometry is MULTIPOLYGON for database compatibility
                    if geometry.geom_type == 'Polygon':
                        geometry = MultiPolygon([geometry])
                    elif geometry.geom_type != 'MultiPolygon':
                        self.stdout.write(
                            self.style.WARNING(f"Unexpected geometry type for {county_name}: {geometry.geom_type}")
                        )
                        error_count += 1
                        continue
                    
                    # Create ext_ids structure
                    ext_ids = {
                        "state_fips": state_fips,
                        "county_fips": county_fips,
                        "county_name": county_name,
                        "state_name": self._get_state_name(state_fips),
                        "state_abbr": self._get_state_abbreviation(state_fips),
                    }
                    
                    # Create or update CoverageArea record
                    with transaction.atomic():
                        if existing_county and update_existing:
                            # Update existing record
                            existing_county.geom = geometry
                            existing_county.center = geometry.centroid
                            existing_county.ext_ids = ext_ids
                            existing_county.updated_by = default_user
                            existing_county.save()
                            coverage_area = existing_county
                        else:
                            # Create new record
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
                    self.stdout.write(f"Successfully imported county: {county_name}")
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing county {properties.get('NAME', 'Unknown')}: {str(e)}")
                    )
                    error_count += 1
            
            return imported_count, error_count
            
        finally:
            # Clean up temporary files AFTER processing is complete
            if os.path.exists(geojson_path):
                os.unlink(geojson_path)
            # Clean up downloaded shapefile AFTER ogr2ogr has finished
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)

    def _get_state_name(self, state_fips: str) -> str:
        """Get state name from FIPS code.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            State name
        """
        # State FIPS to name mapping
        state_names = {
            "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas", "06": "California", 
            "08": "Colorado", "09": "Connecticut", "10": "Delaware", "11": "District of Columbia",
            "12": "Florida", "13": "Georgia", "15": "Hawaii", "16": "Idaho", "17": "Illinois", 
            "18": "Indiana", "19": "Iowa", "20": "Kansas", "21": "Kentucky", "22": "Louisiana",
            "23": "Maine", "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
            "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
            "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
            "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
            "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina",
            "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah", "50": "Vermont",
            "51": "Virginia", "53": "Washington", "54": "West Virginia", "55": "Wisconsin",
            "56": "Wyoming", "60": "American Samoa", "66": "Guam", "69": "Commonwealth of the Northern Mariana Islands",
            "72": "Puerto Rico", "78": "United States Virgin Islands"
        }
        return state_names.get(state_fips, f"State {state_fips}")

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

    def _get_all_state_fips_codes(self) -> List[str]:
        """Get all US state FIPS codes.
        
        Returns:
            List of state FIPS codes
        """
        return [
            "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
            "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
            "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
            "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
            "45", "46", "47", "48", "49", "50", "51", "53", "54", "55",
            "56", "60", "66", "69", "72", "78"
        ]
