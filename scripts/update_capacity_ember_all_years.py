#!/usr/bin/env python3
"""
Script to update capacity data from EMBER for all available years at once.

This script is specifically designed for EMBER data which provides all years
in a single API call. It updates the zone configuration files with all available
years from EMBER in one go, rather than year-by-year.

Usage:
    # Update a single zone with all years:
    poetry run python scripts/update_capacity_ember_all_years.py FR

    # Update all EMBER zones with all years (many API calls!):
    poetry run python scripts/update_capacity_ember_all_years.py --all
"""

import argparse
import logging
from copy import deepcopy

from requests import Session

from electricitymap.contrib.capacity_parsers.EMBER import (
    EMBER_ZONES,
    fetch_production_capacity_all_years,
    fetch_production_capacity_for_all_zones_all_years,
)
from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey
from scripts.update_capacity_configuration import sort_config_keys
from scripts.utils import write_zone_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

ZONES_CONFIG = read_zones_config(CONFIG_DIR)


def update_zone_with_all_years(zone_key: ZoneKey, capacity_data: dict) -> None:
    """Update a zone's capacity configuration with all years from EMBER.

    Args:
        zone_key: The zone key to update
        capacity_data: Dictionary with capacity per mode as lists of years
    """
    if zone_key not in ZONES_CONFIG:
        raise ValueError(f"Zone {zone_key} does not exist in the zones config")

    _new_zone_config = deepcopy(ZONES_CONFIG[zone_key])

    # Initialize capacity if it doesn't exist
    if "capacity" not in _new_zone_config:
        _new_zone_config["capacity"] = {}

    # For EMBER data, we replace existing data with the complete dataset from EMBER
    # This ensures we have the most up-to-date data for all years
    for mode, mode_data in capacity_data.items():
        if mode_data:  # Only update if we have data
            _new_zone_config["capacity"][mode] = mode_data

    # Sort keys
    _new_zone_config["capacity"] = sort_config_keys(_new_zone_config["capacity"])

    logger.info(f"Updating {zone_key} with {len(capacity_data)} modes")
    write_zone_config(zone_key, _new_zone_config)


def main():
    parser = argparse.ArgumentParser(
        description="Update capacity data from EMBER for all available years"
    )
    parser.add_argument(
        "zone_key",
        nargs="?",
        help="Zone key to update (e.g., FR). If not provided, use --all to update all zones.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all EMBER zones (WARNING: This will make many API calls!)",
    )

    args = parser.parse_args()

    session = Session()

    if args.all:
        logger.info(f"Fetching capacity data for all {len(EMBER_ZONES)} EMBER zones...")
        all_capacity = fetch_production_capacity_for_all_zones_all_years(session)

        for zone_key, capacity_data in all_capacity.items():
            try:
                update_zone_with_all_years(zone_key, capacity_data)
                logger.info(f"✓ Updated {zone_key}")
            except Exception as e:
                logger.error(f"✗ Failed to update {zone_key}: {e}")

    elif args.zone_key:
        zone_key = args.zone_key
        if zone_key not in EMBER_ZONES:
            logger.error(
                f"Zone {zone_key} is not in EMBER_ZONES. Available zones: {EMBER_ZONES}"
            )
            return

        logger.info(f"Fetching capacity data for {zone_key}...")
        capacity_data = fetch_production_capacity_all_years(zone_key, session)

        update_zone_with_all_years(zone_key, capacity_data)
        logger.info(f"✓ Successfully updated {zone_key}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
