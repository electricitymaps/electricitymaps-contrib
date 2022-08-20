import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, NewType, Tuple

ZoneKey = NewType("ZoneKey", str)
Point = NewType("Point", Tuple[float, float])
BoundingBox = NewType("BoundingBox", List[Point])

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

# Read JSON files
ZONES_CONFIG = json.load(open(CONFIG_DIR.joinpath("zones.json"), encoding="utf-8"))
EXCHANGES_CONFIG = json.load(
    open(CONFIG_DIR.joinpath("exchanges.json"), encoding="utf-8")
)
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

# This object represents the edges of the flow-tracing graph
ZONE_NEIGHBOURS: Dict[ZoneKey, List[ZoneKey]] = {}
for k, v in EXCHANGES_CONFIG.items():
    if not v.get('parsers', {}).get('exchange', None):
        # Interconnector config has no parser, and will therefore not be part
        # of the flowtracing graph
        continue
    zone_names = k.split("->")
    pairs = [(zone_names[0], zone_names[1]), (zone_names[1], zone_names[0])]
    for zone_name_1, zone_name_2 in pairs:
        if zone_name_1 not in ZONE_NEIGHBOURS:
            ZONE_NEIGHBOURS[zone_name_1] = set()
        ZONE_NEIGHBOURS[zone_name_1].add(zone_name_2)
# Sort
ZONE_NEIGHBOURS = {k: sorted(v) for k, v in ZONE_NEIGHBOURS.items()}


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
