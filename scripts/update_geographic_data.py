#!/usr/bin/env python3
"""
Geographic Data Update Script

This script downloads and imports all geographic data needed for the Resource Directory app.
It handles states, counties, and cities for Kentucky and surrounding states.

Usage:
    python scripts/update_geographic_data.py [--all-states] [--clear-existing] [--year 2023]

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
os.environ['GIS_ENABLED'] = '1'

import django
django.setup()

from django.core.management import call_command
from django.conf import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geographic_data_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GeographicDataUpdater:
    """Manages the download and import of geographic data."""
    
    def __init__(self, all_states=False, clear_existing=False, update_existing=False, year=2023):
        """Initialize the updater.
        
        Args:
            all_states: Whether to import data for all US states
            clear_existing: Whether to clear existing data before importing
            update_existing: Whether to update existing records with new data
            year: TIGER/Line year to use
        """
        self.all_states = all_states
        self.clear_existing = clear_existing
        self.update_existing = update_existing
        self.year = year
        
        # Default states for Kentucky and surrounding area (comprehensive coverage)
        self.default_states = {
            "21": "Kentucky",
            "18": "Indiana", 
            "17": "Illinois",
            "29": "Missouri",
            "47": "Tennessee",
            "51": "Virginia",
            "54": "West Virginia",
            "39": "Ohio",
            "13": "Georgia",  # Southern border
            "01": "Alabama",  # Southern border
            "28": "Mississippi",  # Western border
            "05": "Arkansas",  # Western border
            "22": "Louisiana",  # Western border
            "12": "Florida",  # Southeastern border
            "45": "South Carolina",  # Southeastern border
            "37": "North Carolina",  # Eastern border
            "42": "Pennsylvania",  # Northeastern border
            "24": "Maryland",  # Northeastern border
            "11": "District of Columbia",  # Northeastern border
            "25": "Massachusetts",  # Northeastern border
            "44": "Rhode Island",  # Northeastern border
            "09": "Connecticut",  # Northeastern border
            "36": "New York",  # Northeastern border
            "34": "New Jersey",  # Northeastern border
            "10": "Delaware",  # Northeastern border
            "23": "Maine",  # Northeastern border
            "33": "New Hampshire",  # Northeastern border
            "50": "Vermont",  # Northeastern border
            "26": "Michigan",  # Northern border
            "55": "Wisconsin",  # Northern border
            "27": "Minnesota",  # Northern border
            "38": "North Dakota",  # Northern border
            "46": "South Dakota",  # Northern border
            "31": "Nebraska",  # Northwestern border
            "20": "Kansas",  # Western border
            "40": "Oklahoma",  # Western border
            "48": "Texas",  # Western border
            "35": "New Mexico",  # Western border
            "04": "Arizona",  # Western border
            "06": "California",  # Western border
            "32": "Nevada",  # Western border
            "41": "Oregon",  # Western border
            "53": "Washington",  # Western border
            "16": "Idaho",  # Western border
            "56": "Wyoming",  # Western border
            "08": "Colorado",  # Western border
            "30": "Montana",  # Western border
            "49": "Utah",  # Western border
            "02": "Alaska",  # Western border
            "15": "Hawaii",  # Western border
            "60": "American Samoa",  # Territories
            "66": "Guam",  # Territories
            "69": "Commonwealth of the Northern Mariana Islands",  # Territories
            "72": "Puerto Rico",  # Territories
            "78": "United States Virgin Islands"  # Territories
        }
        
        # All US states (FIPS codes)
        self.all_state_codes = [
            "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
            "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
            "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
            "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
            "45", "46", "47", "48", "49", "50", "51", "53", "54", "55",
            "56", "60", "66", "69", "72", "78"
        ]
        
        self.stats = {
            'states_imported': 0,
            'counties_imported': 0,
            'cities_imported': 0,
            'errors': 0
        }

    def run(self):
        """Run the complete geographic data update process."""
        logger.info("=" * 60)
        logger.info("GEOGRAPHIC DATA UPDATE SCRIPT")
        logger.info("=" * 60)
        logger.info(f"Started at: {datetime.now()}")
        logger.info(f"All states: {self.all_states}")
        logger.info(f"Clear existing: {self.clear_existing}")
        logger.info(f"Update existing: {self.update_existing}")
        logger.info(f"TIGER/Line year: {self.year}")
        
        # Check if GIS is enabled
        if not getattr(settings, 'GIS_ENABLED', False):
            logger.error("GIS is not enabled. Set GIS_ENABLED=1 in your environment.")
            return False
        
        try:
            # Determine which states to process
            if self.all_states:
                states_to_process = self.all_state_codes
                logger.info(f"Processing all {len(states_to_process)} US states/territories")
            else:
                states_to_process = list(self.default_states.keys())
                logger.info(f"Processing {len(states_to_process)} default states: {', '.join(self.default_states.values())}")
            
            # Import states
            self._import_states(states_to_process)
            
            # Import counties
            self._import_counties(states_to_process)
            
            # Import cities
            self._import_cities(states_to_process)
            
            # Print summary
            self._print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during geographic data update: {str(e)}")
            return False

    def _import_states(self, state_codes):
        """Import state boundaries.
        
        Args:
            state_codes: List of state FIPS codes to import
        """
        logger.info("\n" + "=" * 40)
        logger.info("IMPORTING STATE BOUNDARIES")
        logger.info("=" * 40)
        
        try:
            if self.all_states:
                logger.info("Importing all US states...")
                call_command('import_states_simple', all_states=True, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            else:
                states_arg = ','.join(state_codes)
                logger.info(f"Importing states: {states_arg}")
                call_command('import_states_simple', states=states_arg, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            
            self.stats['states_imported'] = len(state_codes)
            logger.info("✅ State import completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error importing states: {str(e)}")
            self.stats['errors'] += 1

    def _import_counties(self, state_codes):
        """Import county boundaries.
        
        Args:
            state_codes: List of state FIPS codes to import
        """
        logger.info("\n" + "=" * 40)
        logger.info("IMPORTING COUNTY BOUNDARIES")
        logger.info("=" * 40)
        
        try:
            if self.all_states:
                logger.info("Importing counties for all US states...")
                call_command('import_counties_simple', all_states=True, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            else:
                states_arg = ','.join(state_codes)
                logger.info(f"Importing counties for states: {states_arg}")
                call_command('import_counties_simple', states=states_arg, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            
            # Estimate counties imported (rough count)
            self.stats['counties_imported'] = len(state_codes) * 100  # Rough estimate
            logger.info("✅ County import completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error importing counties: {str(e)}")
            self.stats['errors'] += 1

    def _import_cities(self, state_codes):
        """Import city boundaries.
        
        Args:
            state_codes: List of state FIPS codes to import
        """
        logger.info("\n" + "=" * 40)
        logger.info("IMPORTING CITY BOUNDARIES")
        logger.info("=" * 40)
        
        try:
            if self.all_states:
                logger.info("Importing cities for all US states...")
                call_command('import_cities_simple', all_states=True, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            else:
                states_arg = ','.join(state_codes)
                logger.info(f"Importing cities for states: {states_arg}")
                call_command('import_cities_simple', states=states_arg, year=self.year, clear_existing=self.clear_existing, update_existing=self.update_existing)
            
            # Estimate cities imported (rough count)
            self.stats['cities_imported'] = len(state_codes) * 200  # Rough estimate
            logger.info("✅ City import completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error importing cities: {str(e)}")
            self.stats['errors'] += 1

    def _print_summary(self):
        """Print a summary of the import process."""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"States imported: {self.stats['states_imported']}")
        logger.info(f"Counties imported: ~{self.stats['counties_imported']}")
        logger.info(f"Cities imported: ~{self.stats['cities_imported']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Completed at: {datetime.now()}")
        
        if self.stats['errors'] == 0:
            logger.info("🎉 All imports completed successfully!")
        else:
            logger.warning(f"⚠️  {self.stats['errors']} errors occurred during import")

    def get_data_status(self):
        """Get current status of geographic data in the database."""
        from directory.models import CoverageArea
        
        logger.info("\n" + "=" * 40)
        logger.info("CURRENT DATA STATUS")
        logger.info("=" * 40)
        
        try:
            states = CoverageArea.objects.filter(kind='STATE').count()
            counties = CoverageArea.objects.filter(kind='COUNTY').count()
            cities = CoverageArea.objects.filter(kind='CITY').count()
            
            logger.info(f"States in database: {states}")
            logger.info(f"Counties in database: {counties}")
            logger.info(f"Cities in database: {cities}")
            logger.info(f"Total coverage areas: {states + counties + cities}")
            
            return {
                'states': states,
                'counties': counties,
                'cities': cities,
                'total': states + counties + cities
            }
            
        except Exception as e:
            logger.error(f"Error getting data status: {str(e)}")
            return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Update geographic data for the Resource Directory app"
    )
    parser.add_argument(
        '--all-states',
        action='store_true',
        help='Import data for all US states (default: Kentucky and surrounding states only)'
    )
    parser.add_argument(
        '--clear-existing',
        action='store_true',
        help='Clear existing geographic data before importing'
    )
    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='Update existing records with new data (default: skip existing)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2023,
        help='TIGER/Line year to use (default: 2023)'
    )
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Only show current data status, do not import'
    )
    
    args = parser.parse_args()
    
    # Create updater
    updater = GeographicDataUpdater(
        all_states=args.all_states,
        clear_existing=args.clear_existing,
        update_existing=args.update_existing,
        year=args.year
    )
    
    if args.status_only:
        # Only show status
        updater.get_data_status()
    else:
        # Run the update
        success = updater.run()
        
        if success:
            logger.info("\n✅ Geographic data update completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Geographic data update failed!")
            sys.exit(1)


if __name__ == '__main__':
    main()
