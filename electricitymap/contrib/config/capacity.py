from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.types import ZoneKey

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

ZONES_CONFIG = read_zones_config(CONFIG_DIR)
# Get productionCapacity source to zones mapping
CAPACITY_PARSER_SOURCE_TO_ZONES: dict[str, list[ZoneKey]] = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if zone_config.get("parsers", {}).get("productionCapacity") is None:
        continue
    source = zone_config.get("parsers", {}).get("productionCapacity").split(".")[0]
    if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
        CAPACITY_PARSER_SOURCE_TO_ZONES[source] = []
    CAPACITY_PARSER_SOURCE_TO_ZONES[source].append(zone_id)

ZONE_TO_CAPACITY_PARSER_SOURCE = {
    zone: source
    for source, zones in CAPACITY_PARSER_SOURCE_TO_ZONES.items()
    for zone in zones
}


@dataclass
class CapacityData:
    value: float | None
    source: str | None = None


def get_capacity_data(capacity_config: dict, dt: datetime) -> dict[str, float | None]:
    """Gets the capacity data for a given zone and datetime from ZONES_CONFIG."""
    capacity = {}
    for mode, capacity_value in capacity_config.items():
        if isinstance(capacity_value, int | float | None):
            # TODO: This part is used for the old capacity format. It shoud be removed once all capacity configs are updated
            capacity[mode] = capacity_value
        else:
            capacity[mode] = _get_capacity_from_dict_or_list(capacity_value, dt).value
    return capacity


def get_capacity_data_with_source(
    capacity_config: dict, dt: datetime
) -> dict[str, CapacityData]:
    """Gets the capacity data for a given zone and datetime from ZONES_CONFIG."""
    capacity = {}
    for mode, capacity_value in capacity_config.items():
        if isinstance(capacity_value, int | float):
            # TODO: This part is used for the old capacity format. It shoud be removed once all capacity configs are updated
            capacity[mode] = CapacityData(capacity_value)
        else:
            capacity[mode] = _get_capacity_from_dict_or_list(capacity_value, dt)

    return capacity


def _get_capacity_from_dict_or_list(
    mode_capacity: list | dict, dt: datetime
) -> CapacityData:
    if isinstance(mode_capacity, dict):
        # TODO: To be removed as eventually we should only have lists.
        return CapacityData(mode_capacity["value"], mode_capacity.get("source"))
    elif isinstance(mode_capacity, list):
        capacity_tuples = [
            (d["datetime"], d["value"], d.get("source")) for d in mode_capacity
        ]

        if dt.isoformat() <= min(capacity_tuples)[0]:
            return CapacityData(min(capacity_tuples)[1], min(capacity_tuples)[2])
        else:
            # valid datetime is the max datetime that is lower than the given datetime
            # In other words, it is the most recent value that is valid for the given dt
            max_tuple = max(
                [(d, v, s) for d, v, s in capacity_tuples if d <= dt.isoformat()]
            )
            return CapacityData(max_tuple[1], max_tuple[2])
