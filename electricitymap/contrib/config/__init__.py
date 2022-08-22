import json
from copy import deepcopy
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, NewType, Set, Tuple

ZoneKey = NewType("ZoneKey", str)
Point = NewType("Point", Tuple[float, float])
BoundingBox = NewType("BoundingBox", List[Point])

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

# Read JSON files
ZONES_CONFIG = json.load(open(CONFIG_DIR.joinpath("zones.json"), encoding="utf-8"))


def _get_base_zone_key(zone_key: ZoneKey) -> ZoneKey:
    return zone_key.split("-")[0]


def _get_zone_keys_for_all_granularities(
    zone_key: str, zones: Dict[str, Any]
) -> List[str]:
    """
    From a given zone key return all zone keys that relate to that zone at different geographic granularities.
    Ex: From SE-SE1 -> [SE, SE-SE1]
    """
    zone_keys = [zone_key]
    base = _get_base_zone_key(zone_key)
    if zone_key in zones.get(base, {}).get("subZoneNames", []):
        zone_keys.append(base)
    zone_keys.sort()
    return zone_keys


def generate_exchanges(
    exchanges_config: Dict[str, Any], zones: Dict[str, Any]
) -> Dict[str, Any]:
    exchanges = deepcopy(exchanges_config)
    # Add the other levels of exchanges
    # For now, we only generate the keys - position of the exchanges will be determined later
    # Same for capacities
    for k, _ in exchanges_config.items():
        zone_keys = k.split("->")
        all_zone_keys = [
            _get_zone_keys_for_all_granularities(z_k, zones) for z_k in zone_keys
        ]
        # Generate exchanges at other granularities
        # For now it's only at the base
        def _should_exchange_be_added(z_k_1: ZoneKey, z_k_2: ZoneKey) -> bool:
            base_z_k_1 = _get_base_zone_key(z_k_1)
            base_z_k_2 = _get_base_zone_key(z_k_2)
            if base_z_k_1 != base_z_k_2 and (
                z_k_1 == base_z_k_1 and z_k_2 == base_z_k_2
            ):
                return True
            return False

        pairs = list(product(*all_zone_keys))
        all_zone_keys.reverse()
        pairs.extend(list(product(*all_zone_keys)))
        for pair in pairs:
            if _should_exchange_be_added(*pair):
                exchange_key = "->".join(sorted(pair))
                if exchange_key not in exchanges:
                    exchanges[exchange_key] = {}

    return exchanges


EXCHANGES_CONFIG = generate_exchanges(
    json.load(open(CONFIG_DIR.joinpath("exchanges.json"), encoding="utf-8")),
    ZONES_CONFIG,
)


def generate_zone_to_exchanges(exhanges: Dict[str, Any]) -> Dict[str, Any]:
    zone_to_exchanges = {}
    for k, _ in exhanges.items():
        zone_key_1, zone_key_2 = k.split("->")
        if zone_key_1 not in zone_to_exchanges:
            zone_to_exchanges[zone_key_1] = [k]
        else:
            zone_to_exchanges[zone_key_1].append(k)
        if zone_key_2 not in zone_to_exchanges:
            zone_to_exchanges[zone_key_2] = [k]
        else:
            zone_to_exchanges[zone_key_2].append(k)

    # we want exchanges to always be in the same order
    for z, ex in zone_to_exchanges.items():
        zone_to_exchanges[z] = sorted(ex)

    return zone_to_exchanges


ZONES_TO_EXCHANGES = generate_zone_to_exchanges(EXCHANGES_CONFIG)


# Prepare zone neighbours
def generate_zone_neighbours(
    exchanges: Dict[str, Any], zones: Dict[str, Any]
) -> Dict[ZoneKey, List[ZoneKey]]:
    zone_neighbours = {}
    for k, _ in exchanges.items():
        zone_keys = k.split("->")
        all_zone_keys = [
            _get_zone_keys_for_all_granularities(z_k, zones) for z_k in zone_keys
        ]

        def _can_zones_be_neighbours(
            z_k_1: ZoneKey, z_k_2: ZoneKey, zones: Dict[str, Any]
        ) -> bool:
            # If we have an exchange between two subzones, we don't want to say that the parent zone is
            # a neighbour of the subzone.
            # That only happens when one is declared as subzone of the other.
            if _get_base_zone_key(z_k_1) == z_k_2:
                if z_k_1 in zones.get(z_k_2, {}).get("subZoneNames", []):
                    return False
            if _get_base_zone_key(z_k_2) == z_k_1:
                if z_k_2 in zones.get(z_k_1, {}).get("subZoneNames", []):
                    return False
            # Twice the same zone is not a neighbour
            if z_k_1 == z_k_2:
                return False
            return True

        pairs = list(product(*all_zone_keys))
        all_zone_keys.reverse()
        pairs.extend(list(product(*all_zone_keys)))
        for zone_key_1, zone_key_2 in pairs:
            if _can_zones_be_neighbours(zone_key_1, zone_key_2, zones):
                if zone_key_1 not in zone_neighbours:
                    zone_neighbours[zone_key_1] = set()
                zone_neighbours[zone_key_1].add(zone_key_2)

    # we want neighbors to always be in the same order
    for zone, neighbors in zone_neighbours.items():
        zone_neighbours[zone] = sorted(neighbors)

    return zone_neighbours


ZONE_NEIGHBOURS = generate_zone_neighbours(EXCHANGES_CONFIG, ZONES_CONFIG)

CO2EQ_PARAMETERS_ALL = json.load(
    open(CONFIG_DIR.joinpath("co2eq_parameters_all.json"), encoding="utf-8")
)
CO2EQ_PARAMETERS_LIFECYCLE = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(
        open(CONFIG_DIR.joinpath("co2eq_parameters_lifecycle.json"), encoding="utf-8")
    ),
}
CO2EQ_PARAMETERS_DIRECT = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(
        open(CONFIG_DIR.joinpath("co2eq_parameters_direct.json"), encoding="utf-8")
    ),
}
CO2EQ_PARAMETERS = CO2EQ_PARAMETERS_LIFECYCLE  # Global LCA is the default

# Prepare zone bounding boxes
ZONE_BOUNDING_BOXES: Dict[ZoneKey, BoundingBox] = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if "bounding_box" in zone_config:
        ZONE_BOUNDING_BOXES[zone_id] = zone_config["bounding_box"]

# Add link from subzone to the full zone
ZONE_PARENT: Dict[ZoneKey, ZoneKey] = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if "subZoneNames" in zone_config:
        for sub_zone_id in zone_config["subZoneNames"]:
            ZONE_PARENT[sub_zone_id] = zone_id


def emission_factors(zone_key: ZoneKey) -> Dict[str, float]:
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
