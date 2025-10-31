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

from requests import Session
from ruamel.yaml import YAML

from electricitymap.contrib.capacity_parsers.EMBER import (
    EMBER_ZONES,
    fetch_production_capacity_all_years,
)
from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.lib.types import ZoneKey
from scripts.update_capacity_configuration import sort_config_keys

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def update_zone_with_all_years(zone_key: ZoneKey, capacity_data: dict) -> None:
    """Update a zone's capacity configuration with all years from EMBER.

    This function ONLY modifies the 'capacity' section of the zone YAML file,
    leaving all other sections (emissionFactors, parsers, etc.) completely untouched
    and preserving their original formatting.

    Args:
        zone_key: The zone key to update
        capacity_data: Dictionary with capacity per mode as lists of years
    """
    zone_file = CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml")

    if not zone_file.exists():
        raise ValueError(f"Zone file for {zone_key} does not exist")

    # Use ruamel.yaml with round-trip mode to preserve formatting
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    # Indent settings to match existing zone YAML format:
    # - mapping=2: each dict level indents 2 spaces
    # - sequence=4: list item properties indent 4 spaces from the dash
    # - offset=2: the dash itself indents 2 spaces from the key
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Read the file with formatting preserved
    with open(zone_file, encoding="utf-8") as f:
        zone_config = yaml.load(f)

    # Initialize capacity if it doesn't exist
    if "capacity" not in zone_config:
        zone_config["capacity"] = {}

    # Replace EMBER capacity data
    for mode, mode_data in capacity_data.items():
        if mode_data:  # Only update if we have data
            zone_config["capacity"][mode] = mode_data

    # Sort capacity keys
    zone_config["capacity"] = sort_config_keys(zone_config["capacity"])

    # Write back with formatting preserved
    with open(zone_file, "w", encoding="utf-8") as f:
        yaml.dump(zone_config, f)

    logger.info(f"Updated {zone_key} with {len(capacity_data)} modes")


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
        logger.info(f"Updating capacity data for all {len(EMBER_ZONES)} EMBER zones...")

        success_count = 0
        fail_count = 0

        for zone_key in sorted(EMBER_ZONES):
            try:
                logger.info(f"Processing {zone_key}...")
                capacity_data = fetch_production_capacity_all_years(zone_key, session)

                if capacity_data:
                    update_zone_with_all_years(zone_key, capacity_data)
                    logger.info(f"✓ Updated {zone_key}")
                    success_count += 1
                else:
                    logger.warning(f"⚠ No capacity data found for {zone_key}")
                    fail_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to update {zone_key}: {e}")
                fail_count += 1
                continue

        logger.info("\n=== Summary ===")
        logger.info(f"Successfully updated: {success_count}/{len(EMBER_ZONES)}")
        logger.info(f"Failed: {fail_count}/{len(EMBER_ZONES)}")

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
