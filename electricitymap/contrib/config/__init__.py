"""Global config variables with data read from the config directory."""

from operator import itemgetter
from pathlib import Path
from typing import Any

from electricitymap.contrib.config.co2eq_parameters import generate_co2eq_parameters
from electricitymap.contrib.config.reading import (
    read_data_centers_config,
    read_defaults,
    read_exchanges_config,
    read_geojson_config,
    read_zones_config,
)
from electricitymap.contrib.config.types import BoundingBox
from electricitymap.contrib.config.zones import (
    generate_all_neighbours,
    generate_zone_neighbours,
    zone_bounding_boxes,
    zone_parents,
)
from electricitymap.contrib.lib.types import ZoneKey

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

ZONES_CONFIG = read_zones_config(CONFIG_DIR)
RETIRED_ZONES_CONFIG = read_zones_config(CONFIG_DIR, retired=True)
EXCHANGES_CONFIG = read_exchanges_config(CONFIG_DIR)
DATA_CENTERS_CONFIG = read_data_centers_config(CONFIG_DIR)
GEOJSON_CONFIG = read_geojson_config()

EU_ZONES = [
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK-DK1",
    "DK-DK2",
    "DK-BHM",
    "EE",
    "ES",
    "ES-IB-ME",
    "ES-IB-MA",
    "ES-IB-IZ",
    "ES-IB-FO",
    "ES-CN-FV",
    "ES-CN-LZ",
    "ES-CN-GC",
    "ES-CN-TE",
    "ES-CN-LP",
    "ES-CN-IG",
    "ES-CN-HI",
    "ES-CE",
    "ES-ML",
    "FI",
    "FR",
    "FR-COR",
    "PF",
    "NC",
    "RE",
    "GF",
    "GP",
    "MQ",
    "PM",
    "GR",
    "HR",
    "HU",
    "IE",
    "IT-SAR",
    "IT-SIC",
    "IT-NO",
    "IT-CNO",
    "IT-CSO",
    "IT-SO",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "PT-AC",
    "PT-MA",
    "RO",
    "SE-SE1",
    "SE-SE2",
    "SE-SE3",
    "SE-SE4",
    "AX",
    "SI",
    "SK",
]
EU_ZONES_CONFIG = {k: v for k, v in ZONES_CONFIG.items() if k in EU_ZONES}

# Prepare the CO2eq parameters config dicts.
defaults = read_defaults(CONFIG_DIR)
(
    co2eq_parameters_all,
    co2eq_parameters_direct,
    co2eq_parameters_lifecycle,
) = generate_co2eq_parameters(defaults, ZONES_CONFIG)
CO2EQ_PARAMETERS_DIRECT = {**co2eq_parameters_all, **co2eq_parameters_direct}
CO2EQ_PARAMETERS_LIFECYCLE = {**co2eq_parameters_all, **co2eq_parameters_lifecycle}
CO2EQ_PARAMETERS = CO2EQ_PARAMETERS_LIFECYCLE  # Global LCA is the default

# Make a dict mapping each zone to its bounding box.
ZONE_BOUNDING_BOXES: dict[ZoneKey, BoundingBox] = zone_bounding_boxes(ZONES_CONFIG)

# Make a mapping from subzone to the parent zone (full zone).
ZONE_PARENT: dict[ZoneKey, ZoneKey] = zone_parents(ZONES_CONFIG)

# Zone neighbours are zones that are connected by exchanges.
ZONE_NEIGHBOURS: dict[ZoneKey, list[ZoneKey]] = generate_zone_neighbours(
    ZONES_CONFIG, EXCHANGES_CONFIG
)

ALL_NEIGHBOURS: dict[ZoneKey, list[ZoneKey]] = generate_all_neighbours(EXCHANGES_CONFIG)


def _get_most_recent_value(emission_factors: dict) -> dict[dict, Any]:
    return {
        k: max(v, key=itemgetter("datetime")) if isinstance(v, list) else v
        for k, v in emission_factors.items()
    }


def emission_factors(zone_key: ZoneKey) -> dict[str, float]:
    """Looks up the emission factors for a given zone."""
    override = CO2EQ_PARAMETERS["emissionFactors"]["zoneOverrides"].get(zone_key, {})
    defaults = CO2EQ_PARAMETERS["emissionFactors"]["defaults"]

    # Only use most recent yearly numbers from defaults & overrides
    defaults = _get_most_recent_value(defaults)
    override = _get_most_recent_value(override)

    merged = {**defaults, **override}
    return {k: (v or {}).get("value") for (k, v) in merged.items()}
