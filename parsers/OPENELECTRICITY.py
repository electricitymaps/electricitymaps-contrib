from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException
from parsers.lib.utils import get_token

"""
OpenElectricity Parser for fetching production and exchange data from OpenElectricity API.
This parser fetches production data for different zones in Australia and parses it into a structured format.
"""
# TODO: Switch to using the Python package https://github.com/opennem/openelectricity-python once it's stable.

SOURCE = "openelectricity.org.au"

@dataclass
class ZoneData:
    region: str
    network: str


# Direct mapping dictionary
ZONE_MAPPING: dict[ZoneKey, ZoneData] = {
    ZoneKey("AU-NSW"): ZoneData(region="NSW1", network="NEM"),
    ZoneKey("AU-QLD"): ZoneData(region="QLD1", network="NEM"),
    ZoneKey("AU-SA"): ZoneData(region="SA1", network="NEM"),
    ZoneKey("AU-TAS"): ZoneData(region="TAS1", network="NEM"),
    ZoneKey("AU-VIC"): ZoneData(region="VIC1", network="NEM"),
    ZoneKey("AU-WA"): ZoneData(region="WEM", network="WEM"),
}

# Reverse lookup dictionary (pre-computed)
REGION_TO_ZONE = {data.region: zone_key for zone_key, data in ZONE_MAPPING.items()}


def get_zone_info(zone_key: ZoneKey) -> ZoneData:
    """Get zone information from zone key."""
    if zone_key not in ZONE_MAPPING:
        raise KeyError(f"Unknown zone key: {zone_key}")
    return ZONE_MAPPING[zone_key]


def get_zone_from_region(region: str) -> ZoneKey:
    """Get zone key from region."""
    if region not in REGION_TO_ZONE:
        raise KeyError(f"Unknown region: {region}")
    return REGION_TO_ZONE[region]


OPENNEM_PRODUCTION_CATEGORIES = {
    "coal": ["coal_black", "coal_brown"],
    "gas": ["gas_ccgt", "gas_ocgt", "gas_recip", "gas_steam"],
    "oil": ["distillate"],
    "hydro": ["hydro"],
    "wind": ["wind"],
    "biomass": ["bioenergy_biogas", "bioenergy_biomass"],
    "solar": ["solar_utility", "solar_rooftop"],
}
OPENNEM_STORAGE_CATEGORIES = {
    # Storage
    "battery": ["battery_discharging", "battery_charging"],
    "hydro": ["pumps"],
}

# Reversed mappings from specific types to general category
FUEL_TYPE_TO_CATEGORY = {
    fuel_tech: category
    for category, fuel_techs in OPENNEM_PRODUCTION_CATEGORIES.items()
    for fuel_tech in fuel_techs
}

STORAGE_TYPE_TO_CATEGORY = {
    storage_tech: category
    for category, storage_techs in OPENNEM_STORAGE_CATEGORIES.items()
    for storage_tech in storage_techs
}


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetch production data for a given zone key.

    Args:
        zone_key (ZoneKey): The zone key for which to fetch production data.
        session (Session, optional): The requests session to use. Defaults to None.
        target_datetime (datetime, optional): The target datetime for the data. Defaults to None.
        logger (Logger, optional): The logger to use. Defaults to the module logger.

    Returns:
        list: A list of production data.
    """
    session = session or Session()
    target_datetime = target_datetime or datetime.now(timezone.utc).replace(
        second=0, microsecond=0
    )

    network = get_zone_info(zone_key).network

    # Define the URL for the API endpoint
    url = f"https://api.openelectricity.org.au/v4/data/network/{network}"
    params = {
        "start": target_datetime.isoformat(),
        "end": (target_datetime - timedelta(days=3)).isoformat(),
        "interval": "5m",
        "metrics": "power",
        "secondary_grouping": "fueltech",
        "primary_grouping": "network_region",
    }
    headers = {"Authorization": f"Bearer {get_token('OPENELECTRICITY_TOKEN')}"}

    # Make the API request
    response = session.get(url, params=params, headers=headers)
    # Check if the request was successful
    if not response.ok:
        raise ParserException(
            "OPENELECTRICITY",
            f"Failed to fetch production data for {zone_key}: {response.status_code} {response.text}",
            zone_key=zone_key,
        )
    # Parse the JSON response
    data = response.json()

    production_breakdown_list = parse_production(
        zone_key=zone_key,
        logger=logger,
        data=data,
    )

    return production_breakdown_list.to_list()


def parse_production(
    zone_key: ZoneKey,
    logger: Logger,
    data: dict[Any, Any],
) -> ProductionBreakdownList:
    """
    Parse the production data from the API response.
    Args:
        logger (Logger): The logger to use.
        data (dict): The API response data.
    Returns:
        ProductionBreakdownList: A list of production breakdown data.
    """
    production_breakdown_lists: list[ProductionBreakdownList] = []
    expected_region = get_zone_info(zone_key).region
    data = data.get("data", [])
    if not data:
        raise ParserException(
            "OPENELECTRICITY",
            "No data found in the API response.",
        )
    for result in data:
        data = result.get("results", [])
        if not data:
            raise ParserException(
                "OPENELECTRICITY",
                "No results found in the API response.",
            )
        for result in data:
            region = result.get("columns", {}).get("region")
            if region != expected_region:
                continue
            fuel = result.get("columns", {}).get("fueltech")
            production_breakdown_list = ProductionBreakdownList(logger=logger)
            result_data = result.get("data", [])
            for entry in result_data:
                production_mix = ProductionMix()
                storage_mix = StorageMix()
                if fuel in FUEL_TYPE_TO_CATEGORY:
                    production_mix.add_value(
                        FUEL_TYPE_TO_CATEGORY[fuel],
                        entry[1],
                    )
                elif fuel in STORAGE_TYPE_TO_CATEGORY:
                    storage_mix.add_value(
                        STORAGE_TYPE_TO_CATEGORY[fuel],
                        entry[1],
                    )
                else:
                    logger.warning(
                        f"Unknown fuel type: {fuel} in region: {region}. Skipping this entry."
                    )
                    continue
                production_breakdown_list.append(
                    zoneKey=get_zone_from_region(region),
                    datetime=datetime.fromisoformat(entry[0]),
                    production=production_mix,
                    storage=storage_mix,
                    source=SOURCE,
                )
            production_breakdown_lists.append(production_breakdown_list)
    return ProductionBreakdownList.merge_production_breakdowns(
        production_breakdown_lists, logger=logger
    )


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    raise NotImplementedError(
        "The OPENELECTRICITY exchange parser is not implemented yet. Please check the documentation if they have added the API for exchage flows."
    )
