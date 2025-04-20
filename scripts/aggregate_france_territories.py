#!/usr/bin/env python3

import glob
import importlib.util
import os
from datetime import datetime
from logging import INFO, basicConfig, getLogger
from typing import Any, Dict, List

import yaml
from requests import Session

# Configure logging
basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

# Base directory path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_DIR = os.path.join(BASE_DIR, "config", "zones")
PARSERS_DIR = os.path.join(BASE_DIR, "parsers")


def load_yaml_file(file_path: str) -> dict:
    """Load YAML file and return as dictionary."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_french_territories() -> List[str]:
    """Return a predefined list of French territories."""
    return [
        "FR",  # Mainland France
        "FR-COR",  # Corsica
        "GF",  # French Guiana
        "GY",  # Guadeloupe
        "RE",  # Réunion
        "YT",  # Mayotte
        "PM",  # Saint Pierre and Miquelon
        "PF",  # French Polynesia
        "NC",  # New Caledonia
    ]


def import_parser_function(parser_path: str) -> Any:
    """Dynamically import parser function from path."""
    module_name, function_name = parser_path.split(".")

    # Try to import from main parsers directory
    try:
        module = __import__(f"parsers.{module_name}", fromlist=[function_name])
        return getattr(module, function_name)
    except (ImportError, AttributeError):
        logger.error(f"Could not import {parser_path}")
        return None


def fetch_territory_production(territory: str) -> Dict[str, Any]:
    """Fetch production data for a specific territory."""
    yaml_file = os.path.join(ZONES_DIR, f"{territory}.yaml")
    config = load_yaml_file(yaml_file)

    production_parser_path = config.get("parsers", {}).get("production")
    if not production_parser_path:
        logger.warning(f"No production parser defined for {territory}")
        return None

    parser_func = import_parser_function(production_parser_path)
    if not parser_func:
        return None

    try:
        session = Session()
        production_data = parser_func(zone_key=territory, session=session)
        logger.info(f"Successfully fetched production data for {territory}")
        return production_data
    except Exception as e:
        logger.error(f"Error fetching data for {territory}: {str(e)}")
        return None


def aggregate_production_data(production_data_list: List[Dict]) -> Dict:
    """Aggregate production data from multiple territories by averaging values."""
    if not production_data_list:
        return {}

    # Extract the most recent data point from each territory
    latest_data_points = []
    for data in production_data_list:
        if isinstance(data, list):
            # If data is a list, take the most recent entry
            sorted_data = sorted(
                data, key=lambda x: x.get("datetime", ""), reverse=True
            )
            if sorted_data:
                latest_data_points.append(sorted_data[0])
        elif isinstance(data, dict):
            # If data is already a single point
            latest_data_points.append(data)

    # Combine production values
    combined_production = {}
    territory_count = len(latest_data_points)

    if territory_count == 0:
        return {}

    # Get all production types across all territories
    all_production_types = set()
    for data_point in latest_data_points:
        if "production" in data_point:
            all_production_types.update(data_point["production"].keys())

    # Average each production type
    aggregated = {
        "datetime": datetime.utcnow().isoformat(),
        "production": {},
        "source": "electricitymaps-script",
        "zoneKey": "FR",
    }

    for prod_type in all_production_types:
        values = [
            data_point["production"].get(prod_type, 0)
            for data_point in latest_data_points
            if "production" in data_point
        ]

        # Filter out None values
        valid_values = [v for v in values if v is not None]

        if valid_values:
            aggregated["production"][prod_type] = sum(valid_values) / len(
                valid_values
            )  # Calculate average

    return aggregated


def main():
    """Main function to run the script."""
    french_territories = get_french_territories()

    # Fetch production data for each territory
    production_data_list = []
    for territory in french_territories:
        data = fetch_territory_production(territory)
        if data:
            production_data_list.append(data)

    # Aggregate the data
    aggregated_data = aggregate_production_data(production_data_list)

    if aggregated_data:
        logger.info("Aggregated production data:")
        logger.info(f"Timestamp: {aggregated_data['datetime']}")
        for prod_type, value in aggregated_data["production"].items():
            logger.info(f"  {prod_type}: {value} MW")
    else:
        logger.error("Failed to aggregate production data")


if __name__ == "__main__":
    main()
