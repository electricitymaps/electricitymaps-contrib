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
import re

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

    This function REPLACES THE ENTIRE 'capacity' section with EMBER data only.
    All existing capacity data from other sources (ENTSOE, manual entries, etc.)
    will be removed. Other sections (emissionFactors, parsers, etc.) remain
    completely untouched with EXACT original formatting preserved.

    Args:
        zone_key: The zone key to update
        capacity_data: Dictionary with capacity per mode as lists of years
    """
    zone_file = CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml")

    if not zone_file.exists():
        raise ValueError(f"Zone file for {zone_key} does not exist")

    # Read the entire file as text
    with open(zone_file, encoding="utf-8") as f:
        original_content = f.read()

    # Sort capacity keys
    sorted_capacity = sort_config_keys(capacity_data)

    # Generate just the capacity section using ruamel.yaml
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Create a minimal dict with just capacity for serialization
    from io import StringIO

    capacity_stream = StringIO()
    yaml.dump({"capacity": sorted_capacity}, capacity_stream)
    new_capacity_yaml = capacity_stream.getvalue()

    # Extract just the capacity section (remove the trailing newline and get content)
    # The output will be "capacity:\n  biomass:\n  ..."

    # Find and replace the capacity section in the original file
    # Pattern: match from "capacity:" to the next top-level key (or end of file)
    pattern = r"^capacity:.*?(?=^[a-zA-Z]|\Z)"

    # Replace the capacity section
    updated_content = re.sub(
        pattern,
        new_capacity_yaml.rstrip() + "\n",
        original_content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Write back
    with open(zone_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

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

        success_zones = []
        failed_zones = []

        for zone_key in sorted(EMBER_ZONES):
            try:
                logger.info(f"Processing {zone_key}...")
                capacity_data = fetch_production_capacity_all_years(zone_key, session)

                if capacity_data:
                    update_zone_with_all_years(zone_key, capacity_data)
                    logger.info(f"✓ Updated {zone_key}")
                    success_zones.append(zone_key)
                else:
                    logger.warning(f"⚠ No capacity data found for {zone_key}")
                    failed_zones.append(zone_key)
            except Exception as e:
                logger.error(f"✗ Failed to update {zone_key}: {e}")
                failed_zones.append(zone_key)
                continue

        logger.info("\n=== Summary ===")
        logger.info(f"Successfully updated: {len(success_zones)}/{len(EMBER_ZONES)}")
        logger.info(f"Failed: {len(failed_zones)}/{len(EMBER_ZONES)}")

        if failed_zones:
            logger.info(f"\nFailed zones: {', '.join(failed_zones)}")

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
