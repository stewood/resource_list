"""Enhanced management command to import state boundaries from TIGER/Line data.

This command provides a better user experience with progress bars, colored output,
and clear status messages.

Usage:
    python manage.py import_states_enhanced --states KY

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

from directory.models import CoverageArea
from directory.utils.tiger_cache import TigerFileCache

# Import tqdm for progress bars
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedUI:
    """Provides enhanced output with colors and progress indicators."""

    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
    }

    def __init__(self, use_colors: bool = True):
        """Initialize the UI system."""
        self.use_colors = use_colors and self._supports_colors()

    def _supports_colors(self) -> bool:
        """Check if the terminal supports colored output."""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text if colors are enabled."""
        if self.use_colors and color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
        return text

    def header(self, text: str) -> None:
        """Print a header with visual separator."""
        separator = "=" * 60
        print(f"\n{self._colorize(separator, 'cyan')}")
        print(f"{self._colorize(text, 'bold')}")
        print(f"{self._colorize(separator, 'cyan')}\n")

    def step(self, text: str) -> None:
        """Print a step header."""
        print(f"\n{self._colorize('▶', 'blue')} {self._colorize(text, 'bold')}")
        print(f"{self._colorize('─' * 50, 'blue')}")

    def success(self, text: str) -> None:
        """Print a success message."""
        print(f"{self._colorize('✅', 'green')} {text}")

    def warning(self, text: str) -> None:
        """Print a warning message."""
        print(f"{self._colorize('⚠️', 'yellow')} {text}")

    def error(self, text: str) -> None:
        """Print an error message."""
        print(f"{self._colorize('❌', 'red')} {text}")

    def info(self, text: str) -> None:
        """Print an info message."""
        print(f"{self._colorize('ℹ️', 'blue')} {text}")

    def progress(self, text: str) -> None:
        """Print a progress message."""
        print(f"{self._colorize('🔄', 'cyan')} {text}")

    def download_progress(self, current: int, total: int, filename: str) -> None:
        """Show download progress."""
        if total > 0:
            percent = (current / total) * 100
            bar_length = 30
            filled_length = int(bar_length * current // total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(
                f"\r{self._colorize('📥', 'cyan')} Downloading {filename}: [{bar}] {percent:.1f}% ({current:,}/{total:,} bytes)",
                end="",
                flush=True,
            )
        else:
            print(
                f"\r{self._colorize('📥', 'cyan')} Downloading {filename}: {current:,} bytes",
                end="",
                flush=True,
            )

    def clear_progress(self) -> None:
        """Clear the current progress line."""
        print("\r" + " " * 80 + "\r", end="", flush=True)


class Command(BaseCommand):
    """Import state boundaries using enhanced approach with better UI."""

    help = "Import state boundaries with enhanced UI and progress tracking"

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
            help="Import all US states",
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
            "--update-existing",
            action="store_true",
            help="Update existing state records with new data",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        year = options["year"]
        clear_existing = options["clear_existing"]
        update_existing = options.get("update_existing", False)

        # Initialize enhanced UI and cache
        self.ui = EnhancedUI()
        self.cache = TigerFileCache()

        self.ui.header("🗺️ STATE BOUNDARY IMPORT")

        # Show configuration
        config_items = [
            ("Year", str(year)),
            ("Clear Existing", "Yes" if clear_existing else "No"),
            ("Update Existing", "Yes" if update_existing else "No"),
        ]

        # Check if GIS is enabled
        if not getattr(settings, "GIS_ENABLED", False):
            self.ui.error("GIS is not enabled. Set GIS_ENABLED=1 in your environment.")
            return

        # Get or create default user for importing
        default_user, created = User.objects.get_or_create(
            username="tiger_importer_enhanced",
            defaults={
                "email": "tiger_enhanced@example.com",
                "first_name": "TIGER",
                "last_name": "Importer Enhanced",
            },
        )

        # Determine which states to process
        if options["all_states"]:
            state_fips_codes = self._get_all_state_fips_codes()
            self.ui.info(f"Importing all {len(state_fips_codes)} US states/territories")
            config_items.append(("Mode", "All US States"))
        elif options["states"]:
            state_fips_codes = [code.strip() for code in options["states"].split(",")]
            self.ui.info(
                f"Importing {len(state_fips_codes)} states: {', '.join(state_fips_codes)}"
            )
            config_items.append(("Mode", f"Selected States ({len(state_fips_codes)})"))
        else:
            self.ui.error("Please specify --states or --all-states")
            return

        # Show configuration
        print(f"\n{self.ui._colorize('Configuration', 'bold')}")
        print(f"{self.ui._colorize('─' * 40, 'cyan')}")
        for label, value in config_items:
            print(f"  {label}: {self.ui._colorize(str(value), 'green')}")

        # Clear existing state data if requested
        if clear_existing:
            self.ui.step("Clearing Existing Data")
            self.ui.progress("Removing existing state coverage areas...")
            deleted_count = CoverageArea.objects.filter(kind="STATE").delete()[0]
            self.ui.success(f"Deleted {deleted_count} existing state coverage areas")

        # Process each state with progress tracking
        self.ui.step("Importing State Boundaries")

        total_imported = 0
        total_errors = 0

        # Optimized approach: Download file once and process all states
        if options["all_states"]:
            # Get file from cache or download
            self.ui.progress("Getting US states shapefile from cache or downloading...")
            try:
                shapefile_path = self.cache.extract_shapefile("STATE", year)
                self.ui.success("Using cached state data")
            except Exception as e:
                self.ui.error(f"Failed to get states shapefile: {str(e)}")
                return
            
            # Process all states from the single file
            self.ui.progress("Processing all states from cached file...")
            imported, errors = self._process_all_states_enhanced(
                shapefile_path, state_fips_codes, default_user, update_existing
            )
            total_imported = imported
            total_errors = errors
            
        else:
            # For individual states, use the original approach
            # Use tqdm for progress bar if available
            if TQDM_AVAILABLE:
                state_iterator = tqdm(
                    state_fips_codes, desc="Processing states", unit="state"
                )
            else:
                state_iterator = state_fips_codes

            # Get file from cache or download once for all states
            try:
                shapefile_path = self.cache.extract_shapefile("STATE", year)
                self.ui.success("Using cached state data")
            except Exception as e:
                self.ui.error(f"Failed to get states shapefile: {str(e)}")
                return
            
            # Process each state from the cached file
            for state_fips in state_iterator:
                try:
                    if not TQDM_AVAILABLE:
                        self.ui.progress(f"Processing state {state_fips}...")

                    imported, errors = self._process_state_from_file(
                        shapefile_path, state_fips, default_user, update_existing
                    )
                    total_imported += imported
                    total_errors += errors

                    if not TQDM_AVAILABLE and imported > 0:
                        self.ui.success(f"State {state_fips}: Imported {imported} states")

                except Exception as e:
                    self.ui.error(f"Error processing state {state_fips}: {str(e)}")
                    total_errors += 1

        # Summary
        self.ui.step("Import Summary")

        summary_items = [
            ("States Imported", total_imported),
            ("Errors Encountered", total_errors),
            (
                "Success Rate",
                (
                    f"{(total_imported/(total_imported+total_errors)*100):.1f}%"
                    if (total_imported + total_errors) > 0
                    else "0%"
                ),
            ),
        ]

        print(f"\n{self.ui._colorize('Results', 'bold')}")
        print(f"{self.ui._colorize('─' * 40, 'cyan')}")
        for label, value in summary_items:
            color = (
                "green"
                if label == "States Imported" and value > 0
                else "red" if label == "Errors Encountered" and value > 0 else "green"
            )
            print(f"  {label}: {self.ui._colorize(str(value), color)}")

        if total_errors == 0:
            self.ui.success("🎉 All state imports completed successfully!")
        else:
            self.ui.warning(f"⚠️ {total_errors} errors occurred during import")

    def _get_all_state_fips_codes(self) -> List[str]:
        """Get all US state FIPS codes."""
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

    def _import_state_enhanced(
        self,
        state_fips: str,
        year: int,
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Import a specific state using enhanced approach."""

        # Download and extract shapefile
        shapefile_path = self._download_state_enhanced(state_fips, year)
        if not shapefile_path:
            return 0, 1

        try:
            # Process the shapefile using alternative method
            imported, errors = self._process_state_enhanced(
                shapefile_path, state_fips, default_user, update_existing
            )

            return imported, errors

        except Exception as e:
            self.ui.error(f"Error processing state {state_fips}: {str(e)}")
            # Clean up on error
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)
            return 0, 1

    def _download_state_enhanced(self, state_fips: str, year: int) -> Optional[str]:
        """Download state shapefile using enhanced approach."""
        # TIGER/Line URL format for states (single file for all states)
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/STATE/tl_{year}_us_state.zip"
        filename = f"tl_{year}_us_state.zip"

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, filename)
        extract_path = os.path.join(temp_dir, f"tl_{year}_us_state")

        try:
            # Download the file with progress tracking
            self.ui.progress(f"Downloading {filename}...")

            import requests
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.ui.download_progress(downloaded, total_size, filename)

            self.ui.clear_progress()
            self.ui.success(f"Download completed! ({downloaded:,} bytes)")

            # Extract the zip file
            self.ui.progress("Extracting files...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            # Find the .shp file
            shp_files = [f for f in os.listdir(extract_path) if f.endswith(".shp")]
            if not shp_files:
                self.ui.error(f"No shapefile found in {extract_path}")
                return None

            shapefile_path = os.path.join(extract_path, shp_files[0])
            file_size = os.path.getsize(shapefile_path)
            self.ui.info(f"Found shapefile: {shp_files[0]} ({file_size:,} bytes)")

            return shapefile_path

        except Exception as e:
            self.ui.error(f"Error downloading/extracting {url}: {str(e)}")
            return None

    def _process_state_enhanced(
        self,
        shapefile_path: str,
        state_fips: str,
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Process state shapefile using enhanced approach."""
        if not getattr(settings, "GIS_ENABLED", False):
            self.ui.error("GIS is not enabled. Cannot process shapefiles.")
            return 0, 1

        try:
            # Use ogr2ogr for processing
            self.ui.progress("Converting shapefile to GeoJSON...")

            import subprocess
            import tempfile

            # Create temporary file for GeoJSON output
            import uuid

            geojson_path = os.path.join(
                tempfile.gettempdir(), f"state_import_{uuid.uuid4().hex}.geojson"
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

            self.ui.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.ui.error(f"ogr2ogr failed: {result.stderr}")
                return 0, 1

            self.ui.success("Shapefile converted successfully")

            # Parse GeoJSON and import states
            self.ui.progress("Importing state data...")

            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)

            imported_count = 0
            error_count = 0

            for feature in geojson_data["features"]:
                try:
                    properties = feature["properties"]
                    geometry = feature["geometry"]

                    # Extract state information
                    state_name = properties.get("NAME", "Unknown State")
                    state_fips_code = properties.get("STATEFP", "00")

                    # Only import the requested state
                    if state_fips_code == state_fips:
                        # Check if state already exists
                        existing_state = CoverageArea.objects.filter(
                            kind="STATE", ext_ids__state_fips=state_fips_code
                        ).first()

                        if existing_state and not update_existing:
                            continue  # Skip if exists and not updating

                        # Create or update state
                        geom_obj = GEOSGeometry(json.dumps(geometry))

                        # Convert single polygon to multipolygon if needed
                        if geom_obj.geom_type == "Polygon":
                            from django.contrib.gis.geos import MultiPolygon

                            geom_obj = MultiPolygon([geom_obj])

                        if existing_state and update_existing:
                            existing_state.name = state_name
                            existing_state.geom = geom_obj
                            existing_state.updated_by = default_user
                            existing_state.save()
                        else:
                            CoverageArea.objects.create(
                                kind="STATE",
                                name=state_name,
                                geom=geom_obj,
                                ext_ids={"state_fips": state_fips_code},
                                created_by=default_user,
                                updated_by=default_user,
                            )

                        imported_count += 1
                        self.ui.success(f"Successfully imported state: {state_name}")

                except Exception as e:
                    error_count += 1
                    self.ui.error(f"Error importing state feature: {str(e)}")

            # Clean up temporary file
            os.unlink(geojson_path)

            return imported_count, error_count

        except Exception as e:
            self.ui.error(f"Error processing state {state_fips}: {str(e)}")
            return 0, 1

    def _process_state_from_file(
        self,
        shapefile_path: str,
        state_fips: str,
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Process a specific state from a cached shapefile."""
        if not getattr(settings, "GIS_ENABLED", False):
            self.ui.error("GIS is not enabled. Cannot process shapefiles.")
            return 0, 1

        try:
            # Use ogr2ogr for processing
            self.ui.progress("Converting shapefile to GeoJSON...")

            import subprocess
            import tempfile

            # Create temporary file for GeoJSON output
            import uuid

            geojson_path = os.path.join(
                tempfile.gettempdir(), f"state_import_{uuid.uuid4().hex}.geojson"
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

            self.ui.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.ui.error(f"ogr2ogr failed: {result.stderr}")
                return 0, 1

            self.ui.success("Shapefile converted successfully")

            # Parse GeoJSON and import states
            self.ui.progress("Importing state data...")

            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)

            imported_count = 0
            error_count = 0

            for feature in geojson_data["features"]:
                try:
                    properties = feature["properties"]
                    geometry = feature["geometry"]

                    # Extract state information
                    state_name = properties.get("NAME", "Unknown State")
                    state_fips_code = properties.get("STATEFP", "00")

                    # Only import the requested state
                    if state_fips_code == state_fips:
                        # Check if state already exists
                        existing_state = CoverageArea.objects.filter(
                            kind="STATE", ext_ids__state_fips=state_fips_code
                        ).first()

                        if existing_state and not update_existing:
                            continue  # Skip if exists and not updating

                        # Create or update state
                        geom_obj = GEOSGeometry(json.dumps(geometry))

                        # Convert single polygon to multipolygon if needed
                        if geom_obj.geom_type == "Polygon":
                            from django.contrib.gis.geos import MultiPolygon

                            geom_obj = MultiPolygon([geom_obj])

                        if existing_state and update_existing:
                            existing_state.name = state_name
                            existing_state.geom = geom_obj
                            existing_state.updated_by = default_user
                            existing_state.save()
                        else:
                            CoverageArea.objects.create(
                                kind="STATE",
                                name=state_name,
                                geom=geom_obj,
                                ext_ids={"state_fips": state_fips_code},
                                created_by=default_user,
                                updated_by=default_user,
                            )

                        imported_count += 1
                        self.ui.success(f"Successfully imported state: {state_name}")

                except Exception as e:
                    error_count += 1
                    self.ui.error(f"Error importing state feature: {str(e)}")

            # Clean up temporary file
            os.unlink(geojson_path)

            return imported_count, error_count

        except Exception as e:
            self.ui.error(f"Error processing state {state_fips}: {str(e)}")
            return 0, 1

    def _process_all_states_enhanced(
        self,
        shapefile_path: str,
        state_fips_codes: List[str],
        default_user: User,
        update_existing: bool = False,
    ) -> Tuple[int, int]:
        """Process all states from a single shapefile using enhanced approach."""
        if not getattr(settings, "GIS_ENABLED", False):
            self.ui.error("GIS is not enabled. Cannot process shapefiles.")
            return 0, 1

        try:
            # Use ogr2ogr for processing
            self.ui.progress("Converting shapefile to GeoJSON...")

            import subprocess
            import tempfile

            # Create temporary file for GeoJSON output
            import uuid

            geojson_path = os.path.join(
                tempfile.gettempdir(), f"all_states_import_{uuid.uuid4().hex}.geojson"
            )

            # Run ogr2ogr command
            cmd = [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                "-t_srs",
                "EPSG:4326",
                geojson_path,
                str(shapefile_path),
            ]

            self.ui.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.ui.error(f"ogr2ogr failed: {result.stderr}")
                return 0, 1

            self.ui.success("Shapefile converted successfully")

            # Parse GeoJSON and import all states
            self.ui.progress("Importing all state data...")

            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)

            imported_count = 0
            error_count = 0

            # Use tqdm for progress bar if available
            if TQDM_AVAILABLE:
                feature_iterator = tqdm(
                    geojson_data["features"], desc="Processing states", unit="state"
                )
            else:
                feature_iterator = geojson_data["features"]

            for feature in feature_iterator:
                try:
                    properties = feature["properties"]
                    geometry = feature["geometry"]

                    # Extract state information
                    state_name = properties.get("NAME", "Unknown State")
                    state_fips_code = properties.get("STATEFP", "00")

                    # Only import states that are in our target list
                    if state_fips_code not in state_fips_codes:
                        continue

                    # Check if state already exists
                    existing_state = CoverageArea.objects.filter(
                        kind="STATE", ext_ids__state_fips=state_fips_code
                    ).first()

                    if existing_state and not update_existing:
                        if not TQDM_AVAILABLE:
                            self.ui.info(f"Skipping existing state: {state_name}")
                        continue  # Skip if exists and not updating

                    # Create or update state
                    geom_obj = GEOSGeometry(json.dumps(geometry))

                    # Convert single polygon to multipolygon if needed
                    if geom_obj.geom_type == "Polygon":
                        from django.contrib.gis.geos import MultiPolygon

                        geom_obj = MultiPolygon([geom_obj])

                    if existing_state and update_existing:
                        existing_state.name = state_name
                        existing_state.geom = geom_obj
                        existing_state.updated_by = default_user
                        existing_state.save()
                    else:
                        CoverageArea.objects.create(
                            kind="STATE",
                            name=state_name,
                            geom=geom_obj,
                            ext_ids={"state_fips": state_fips_code},
                            created_by=default_user,
                            updated_by=default_user,
                        )

                    imported_count += 1
                    if not TQDM_AVAILABLE:
                        self.ui.success(f"Successfully imported state: {state_name}")

                except Exception as e:
                    error_count += 1
                    if not TQDM_AVAILABLE:
                        self.ui.error(f"Error importing state feature: {str(e)}")

            # Clean up temporary file
            os.unlink(geojson_path)

            return imported_count, error_count

        except Exception as e:
            self.ui.error(f"Error processing all states: {str(e)}")
            return 0, 1
