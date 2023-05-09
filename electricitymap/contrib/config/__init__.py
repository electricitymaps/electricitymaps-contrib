"""Global config variables with data read from the config directory."""

from copy import deepcopy
from pathlib import Path
from typing import Dict, List

from electricitymap.contrib.config.co2eq_parameters import generate_co2eq_parameters
from electricitymap.contrib.config.reading import (
    read_defaults,
    read_exchanges_config,
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
EXCHANGES_CONFIG = read_exchanges_config(CONFIG_DIR)

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
ZONE_BOUNDING_BOXES: Dict[ZoneKey, BoundingBox] = zone_bounding_boxes(ZONES_CONFIG)

# Make a mapping from subzone to the parent zone (full zone).
ZONE_PARENT: Dict[ZoneKey, ZoneKey] = zone_parents(ZONES_CONFIG)

# Zone neighbours are zones that are connected by exchanges.
ZONE_NEIGHBOURS: Dict[ZoneKey, List[ZoneKey]] = generate_zone_neighbours(
    ZONES_CONFIG, EXCHANGES_CONFIG
)

ALL_NEIGHBOURS: Dict[ZoneKey, List[ZoneKey]] = generate_all_neighbours(EXCHANGES_CONFIG)


def emission_factors(zone_key: ZoneKey) -> Dict[str, float]:
    """Looks up the emission factors for a given zone."""
    override = CO2EQ_PARAMETERS["emissionFactors"]["zoneOverrides"].get(zone_key, {})
    defaults = CO2EQ_PARAMETERS["emissionFactors"]["defaults"]

    def get_most_recent_value(emission_factors: Dict) -> Dict:
        _emission_factors = deepcopy(emission_factors)
        keys_with_yearly = [
            k for (k, v) in _emission_factors.items() if isinstance(v, list)
        ]
        for k in keys_with_yearly:
            _emission_factors[k] = max(
                _emission_factors[k], key=lambda x: x["datetime"]
            )
        return _emission_factors

    # Only use most recent yearly numbers from defaults & overrides
    defaults = get_most_recent_value(defaults)
    override = get_most_recent_value(override)

    merged = {**defaults, **override}
    return dict([(k, (v or {}).get("value")) for (k, v) in merged.items()])
