"""Enhanced management command to import city boundaries from TIGER/Line data.

This command provides a better user experience with progress bars, colored output,
and clear status messages.

Usage:
    python manage.py import_cities_enhanced --states KY

Author: Resource Directory Team
Created: 2025-01-15
Version: 2.0.0
"""

import os
import zipfile
import tempfile
import urllib.request
import json
import sys
from typing import Any, Dict, List, Optional, Tuple
import logging

# Import Shapely first to avoid segmentation fault with Fiona
from django.contrib.gis.geos import GEOSGeometry

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction

# Import CoverageArea model
from directory.models import CoverageArea

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


# ANSI color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ColoredUI:
    """Enhanced UI class for colored terminal output."""

    @staticmethod
    def header(text: str) -> None:
        """Print a header message."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print("─" * len(text))

    @staticmethod
    def step(text: str) -> None:
        """Print a step message."""
        print(f"\n{Colors.OKBLUE}🔄 {text}{Colors.ENDC}")

    @staticmethod
    def success(text: str) -> None:
        """Print a success message."""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

    @staticmethod
    def warning(text: str) -> None:
        """Print a warning message."""
        print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

    @staticmethod
    def error(text: str) -> None:
        """Print an error message."""
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

    @staticmethod
    def info(text: str) -> None:
        """Print an info message."""
        print(f"{Colors.OKCYAN}ℹ️ {text}{Colors.ENDC}")

    @staticmethod
    def progress(text: str, current: int, total: int, bar_length: int = 40) -> None:
        """Print a progress bar."""
        if not TQDM_AVAILABLE:
            percent = (current / total) * 100
            filled_length = int(bar_length * current // total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(
                f"\r{Colors.OKBLUE}{text}: [{bar}] {percent:.1f}% ({current:,}/{total:,}){Colors.ENDC}",
                end="",
                flush=True,
            )
            if current == total:
                print()  # New line when complete

    @staticmethod
    def summary(title: str, data: Dict[str, Any]) -> None:
        """Print a summary section."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}▶ {title}{Colors.ENDC}")
        print("─" * (len(title) + 3))
        for key, value in data.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:,}")
            else:
                print(f"  {key}: {value}")
        print()


class Command(BaseCommand):
    """Enhanced management command to import city boundaries."""

    help = "Import city boundaries from TIGER/Line data with enhanced UI"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--states",
            type=str,
            help='State FIPS codes to import (e.g., "21,18" for Kentucky and Indiana)',
        )
        parser.add_argument(
            "--all-states", action="store_true", help="Import cities for all states"
        )
        parser.add_argument(
            "--year",
            type=int,
            default=2023,
            help="TIGER/Line data year (default: 2023)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing city data before import",
        )
        parser.add_argument(
            "--update-existing", action="store_true", help="Update existing city data"
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        ui = ColoredUI()

        # Display header
        ui.header("Enhanced City Boundary Import")

        # Validate arguments
        if not options["states"] and not options["all_states"]:
            ui.error("Please specify --states or --all-states")
            return

        # Get state FIPS codes
        if options["all_states"]:
            state_fips_codes = self._get_all_state_fips_codes()
            ui.info(f"Importing cities for all {len(state_fips_codes)} states")
        else:
            # Parse comma-separated state FIPS codes
            state_fips_codes = [
                s.strip() for s in options["states"].split(",") if s.strip()
            ]
            ui.info(
                f"Importing cities for {len(state_fips_codes)} states: {', '.join(state_fips_codes)}"
            )

        # Get or create default user
        default_user = self._get_default_user()

        # Clear existing data if requested
        if options["clear_existing"]:
            ui.step("Clearing existing city data...")
            deleted_count = CoverageArea.objects.filter(kind="CITY").delete()[0]
            ui.success(f"Deleted {deleted_count} existing city records")

        # Import cities
        ui.step("Starting city import process...")
        total_imported = 0
        total_errors = 0

        # Optimized approach: Download file once and process all states
        if len(state_fips_codes) > 1:
            # Download the file once for multiple states
            ui.progress("Downloading city shapefile (once for all states)...")
            shapefile_path = self._download_city_enhanced("ALL", options["year"])
            
            if not shapefile_path:
                ui.error("Failed to download cities shapefile")
                return
            
            # Process all states from the single file
            ui.progress("Processing all states from downloaded file...")
            imported, errors = self._process_all_cities_enhanced(
                shapefile_path, state_fips_codes, default_user, options["update_existing"]
            )
            total_imported = imported
            total_errors = errors
            
        else:
            # For single state, use the original approach
            for state_fips in state_fips_codes:
                try:
                    imported, errors = self._import_city_enhanced(
                        state_fips,
                        options["year"],
                        default_user,
                        options["update_existing"],
                    )
                    total_imported += imported
                    total_errors += errors
                except Exception as e:
                    ui.error(f"Error processing state {state_fips}: {str(e)}")
                    total_errors += 1

        # Display summary
        success_rate = (
            (total_imported / (total_imported + total_errors)) * 100
            if (total_imported + total_errors) > 0
            else 0
        )
        ui.summary(
            "Import Summary",
            {
                "Cities Imported": total_imported,
                "Errors Encountered": total_errors,
                "Success Rate": f"{success_rate:.1f}%",
            },
        )

        if total_errors > 0:
            ui.warning(f"⚠️ {total_errors} errors occurred during import")
        else:
            ui.success("🎉 All city imports completed successfully!")

    def _get_all_state_fips_codes(self) -> List[str]:
        """Get FIPS codes for all US states."""
        return [
            "01",
            "02",
            "04",
            "05",
            "06",
            "08",
            "09",
            "10",
            "11",
            "12",
            "13",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "30",
            "31",
            "32",
            "33",
            "34",
            "35",
            "36",
            "37",
            "38",
            "39",
            "40",
            "41",
            "42",
            "44",
            "45",
            "46",
            "47",
            "48",
            "49",
            "50",
            "51",
            "53",
            "54",
            "55",
            "56",
            "60",
            "66",
            "69",
            "72",
            "78",
        ]

    def _get_default_user(self) -> User:
        """Get or create a default user for the import."""
        try:
            return User.objects.first()
        except:
            return User.objects.create_user(
                username="import_user",
                email="import@example.com",
                password="temp_password_123",
            )

    def _import_city_enhanced(
        self,
        state_fips: str,
        year: int,
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Import cities for a specific state with enhanced UI."""
        ui = ColoredUI()

        ui.step(f"Processing state FIPS: {state_fips}")

        # Download city data
        ui.info("Downloading city shapefile...")
        zip_path = self._download_city_enhanced(state_fips, year)

        # Extract and process
        ui.info("Extracting and processing city data...")
        imported_count = 0
        error_count = 0

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_ref.extractall(temp_dir)

                # Find the shapefile
                shapefile_path = None
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(".shp"):
                            shapefile_path = os.path.join(root, file)
                            break
                    if shapefile_path:
                        break

                if not shapefile_path:
                    ui.error(f"No shapefile found in {zip_path}")
                    return 0, 1

                ui.info(
                    f"Found shapefile: {os.path.basename(shapefile_path)} ({os.path.getsize(shapefile_path):,} bytes)"
                )

                # Convert to GeoJSON
                ui.info("Converting shapefile to GeoJSON...")
                geojson_path = self._convert_to_geojson_enhanced(shapefile_path)

                # Import city data
                ui.info("Importing city data...")
                imported_count, error_count = self._process_city_geojson_enhanced(
                    geojson_path, state_fips, default_user, update_existing
                )

        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)

        ui.success(
            f"Successfully imported {imported_count} cities for state {state_fips}"
        )
        if error_count > 0:
            ui.warning(f"Encountered {error_count} errors for state {state_fips}")

        return imported_count, error_count

    def _download_city_enhanced(self, state_fips: str, year: int) -> str:
        """Download city shapefile with progress bar."""
        ui = ColoredUI()

        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/PLACE/tl_{year}_{state_fips}_place.zip"
        filename = f"tl_{year}_{state_fips}_place.zip"

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_path = temp_file.name
        temp_file.close()

        # Download with progress bar
        try:
            with urllib.request.urlopen(url) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                with open(temp_path, "wb") as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            ui.progress(
                                f"Downloading {filename}", downloaded_size, total_size
                            )

                ui.success(f"Download completed! ({downloaded_size:,} bytes)")
                return temp_path

        except Exception as e:
            ui.error(f"Download failed: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _convert_to_geojson_enhanced(self, shapefile_path: str) -> str:
        """Convert shapefile to GeoJSON with enhanced output."""
        ui = ColoredUI()

        # Create temporary file for GeoJSON output
        import uuid

        geojson_path = os.path.join(
            tempfile.gettempdir(), f"city_import_{uuid.uuid4().hex}.geojson"
        )

        # Run ogr2ogr command
        cmd = f'ogr2ogr -f GeoJSON -t_srs EPSG:4326 "{geojson_path}" "{shapefile_path}"'
        ui.info(f"Running: {cmd}")

        result = os.system(cmd)
        if result == 0:
            ui.success("Shapefile converted successfully")
            return geojson_path
        else:
            ui.error("Shapefile conversion failed")
            raise Exception("ogr2ogr conversion failed")

    def _process_city_geojson_enhanced(
        self,
        geojson_path: str,
        state_fips: str,
        default_user: User,
        update_existing: bool,
    ) -> Tuple[int, int]:
        """Process city GeoJSON data with enhanced UI."""
        ui = ColoredUI()

        imported_count = 0
        error_count = 0

        try:
            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)

            features = geojson_data.get("features", [])
            ui.info(f"Processing {len(features)} city features...")

            # Use tqdm for progress bar if available
            if TQDM_AVAILABLE:
                feature_iter = tqdm(features, desc="Processing cities")
            else:
                feature_iter = features

            for i, feature in enumerate(feature_iter):
                try:
                    properties = feature.get("properties", {})
                    geometry = feature.get("geometry")

                    if not geometry or not properties:
                        continue

                    # Extract city information
                    city_name = properties.get("NAME", "Unknown City")
                    place_fips = properties.get("PLACEFP", "")

                    if not place_fips:
                        continue

                    # Check if city already exists
                    existing_city = CoverageArea.objects.filter(
                        kind="CITY",
                        ext_ids__place_fips=place_fips,
                        ext_ids__state_fips=state_fips,
                    ).first()

                    # Create or update city
                    geom_obj = GEOSGeometry(json.dumps(geometry))

                    # Convert single polygon to multipolygon if needed
                    if geom_obj.geom_type == "Polygon":
                        from django.contrib.gis.geos import MultiPolygon

                        geom_obj = MultiPolygon([geom_obj])

                    if existing_city and update_existing:
                        existing_city.name = city_name
                        existing_city.geom = geom_obj
                        existing_city.updated_by = default_user
                        existing_city.save()
                    else:
                        CoverageArea.objects.create(
                            kind="CITY",
                            name=city_name,
                            geom=geom_obj,
                            ext_ids={
                                "state_fips": state_fips,
                                "place_fips": place_fips,
                            },
                            created_by=default_user,
                            updated_by=default_user,
                        )

                    imported_count += 1

                except Exception as e:
                    ui.error(f"Error importing city feature: {str(e)}")
                    error_count += 1
                    continue

            # Cleanup
            if os.path.exists(geojson_path):
                os.remove(geojson_path)

            return imported_count, error_count

        except Exception as e:
            ui.error(f"Error processing GeoJSON: {str(e)}")
            return 0, 1

    def _process_all_cities_enhanced(
        self,
        shapefile_path: str,
        state_fips_codes: List[str],
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Process all cities from a single shapefile using enhanced approach."""
        if not getattr(settings, "GIS_ENABLED", False):
            ui = ColoredUI()
            ui.error("GIS is not enabled. Cannot process shapefiles.")
            return 0, 1

        try:
            # Use ogr2ogr for processing
            ui = ColoredUI()
            ui.progress("Converting shapefile to GeoJSON...")

            import subprocess
            import tempfile

            # Create temporary file for GeoJSON output
            import uuid

            geojson_path = os.path.join(
                tempfile.gettempdir(), f"all_cities_import_{uuid.uuid4().hex}.geojson"
            )

            # Run ogr2ogr command
            cmd = [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                "-t_srs",
                "EPSG:4326",
                geojson_path,
                shapefile_path,
            ]

            ui.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                ui.error(f"ogr2ogr failed: {result.stderr}")
                return 0, 1

            ui.success("Shapefile converted successfully")

            # Parse GeoJSON and import all cities
            ui.progress("Importing all city data...")

            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)

            imported_count = 0
            error_count = 0

            # Use tqdm for progress bar if available
            if TQDM_AVAILABLE:
                feature_iterator = tqdm(
                    geojson_data["features"], desc="Processing cities", unit="city"
                )
            else:
                feature_iterator = geojson_data["features"]

            for feature in feature_iterator:
                try:
                    properties = feature["properties"]
                    geometry = feature["geometry"]

                    # Extract city information
                    city_name = properties.get("NAME", "Unknown City")
                    place_fips = properties.get("PLACEFP", "")
                    state_fips = properties.get("STATEFP", "")

                    if not place_fips or not state_fips:
                        continue

                    # Only import cities for states in our target list
                    if state_fips not in state_fips_codes:
                        continue

                    # Check if city already exists
                    existing_city = CoverageArea.objects.filter(
                        kind="CITY",
                        ext_ids__place_fips=place_fips,
                        ext_ids__state_fips=state_fips,
                    ).first()

                    if existing_city and not update_existing:
                        if not TQDM_AVAILABLE:
                            ui.info(f"Skipping existing city: {city_name}")
                        continue  # Skip if exists and not updating

                    # Create or update city
                    geom_obj = GEOSGeometry(json.dumps(geometry))

                    # Convert single polygon to multipolygon if needed
                    if geom_obj.geom_type == "Polygon":
                        from django.contrib.gis.geos import MultiPolygon

                        geom_obj = MultiPolygon([geom_obj])

                    if existing_city and update_existing:
                        existing_city.name = city_name
                        existing_city.geom = geom_obj
                        existing_city.updated_by = default_user
                        existing_city.save()
                    else:
                        CoverageArea.objects.create(
                            kind="CITY",
                            name=city_name,
                            geom=geom_obj,
                            ext_ids={
                                "state_fips": state_fips,
                                "place_fips": place_fips,
                            },
                            created_by=default_user,
                            updated_by=default_user,
                        )

                    imported_count += 1
                    if not TQDM_AVAILABLE:
                        ui.success(f"Successfully imported city: {city_name}")

                except Exception as e:
                    error_count += 1
                    if not TQDM_AVAILABLE:
                        ui.error(f"Error importing city feature: {str(e)}")

            # Clean up temporary file
            os.unlink(geojson_path)

            return imported_count, error_count

        except Exception as e:
            ui.error(f"Error processing all cities: {str(e)}")
            return 0, 1
