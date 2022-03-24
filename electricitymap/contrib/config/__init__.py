import json
from pathlib import Path
from typing import Dict, List, NewType, Tuple

ZoneKey = NewType("ZoneKey", str)
Point = NewType("Point", Tuple[float, float])
BoundingBox = NewType("BoundingBox", List[Point])

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

# Read JOSN files
ZONES_CONFIG = json.load(open(CONFIG_DIR.joinpath("zones.json")))
EXCHANGES_CONFIG = json.load(open(CONFIG_DIR.joinpath("exchanges.json")))
CO2EQ_PARAMETERS_ALL = json.load(open(CONFIG_DIR.joinpath("co2eq_parameters_all.json")))
CO2EQ_PARAMETERS_LIFECYCLE = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(open(CONFIG_DIR.joinpath("co2eq_parameters_lifecycle.json"))),
}
CO2EQ_PARAMETERS_DIRECT = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(open(CONFIG_DIR.joinpath("co2eq_parameters_direct.json"))),
}
CO2EQ_PARAMETERS = CO2EQ_PARAMETERS_LIFECYCLE  # Global LCA is the default

# Prepare zone bounding boxes
ZONE_BOUNDING_BOXES: Dict[ZoneKey, BoundingBox] = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if "bounding_box" in zone_config:
        ZONE_BOUNDING_BOXES[zone_id] = zone_config["bounding_box"]

# Prepare zone neighbours
ZONE_NEIGHBOURS: Dict[ZoneKey, List[ZoneKey]] = {}
for k, v in EXCHANGES_CONFIG.items():
    zone_names = k.split("->")
    pairs = [(zone_names[0], zone_names[1]), (zone_names[1], zone_names[0])]
    for zone_name_1, zone_name_2 in pairs:
        if zone_name_1 not in ZONE_NEIGHBOURS:
            ZONE_NEIGHBOURS[zone_name_1] = set()
        ZONE_NEIGHBOURS[zone_name_1].add(zone_name_2)
# we want neighbors to always be in the same order
for zone, neighbors in ZONE_NEIGHBOURS.items():
    ZONE_NEIGHBOURS[zone] = sorted(neighbors)


def emission_factors(zone_key: ZoneKey):
    override = CO2EQ_PARAMETERS["emissionFactors"]["zoneOverrides"].get(zone_key, {})
    defaults = CO2EQ_PARAMETERS["emissionFactors"]["defaults"]

    # Only use most recent yearly numbers from defaults
    defaults_with_yearly = [k for (k, v) in defaults.items() if isinstance(v, list)]
    for k in defaults_with_yearly:
        defaults[k] = max(defaults[k], key=lambda x: x["datetime"])

    merged = {**defaults, **override}
    return dict([(k, (v or {}).get("value")) for (k, v) in merged.items()])
