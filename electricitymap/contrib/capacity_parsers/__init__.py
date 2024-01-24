from pathlib import Path

from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

ZONES_CONFIG = read_zones_config(CONFIG_DIR)
# Get productionCapacity source to zones mapping
CAPACITY_PARSER_SOURCE_TO_ZONES = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if zone_config.get("parsers", {}).get("productionCapacity") is None:
        continue
    source = zone_config.get("parsers", {}).get("productionCapacity").split(".")[0]
    if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
        CAPACITY_PARSER_SOURCE_TO_ZONES[source] = []
    CAPACITY_PARSER_SOURCE_TO_ZONES[source].append(zone_id)
