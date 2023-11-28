from datetime import datetime

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey

ZONES_CONFIG = read_zones_config(CONFIG_DIR)


def get_capacity_data(capacity_config: dict, dt: datetime) -> dict[str, float]:
    """Gets the capacity data for a given zone and datetime from ZONES_CONFIG."""
    capacity = {}
    for mode, capacity_value in capacity_config.items():
        if isinstance(capacity_value, (int, float)):
            # TODO: This part is used for the old capacity format. It shoud be removed once all capacity configs are updated
            capacity[mode] = capacity_value
        else:
            capacity[mode] = get_capacity_value_with_datetime(capacity_value, dt)
    return capacity


def get_capacity_value_with_datetime(
    mode_capacity: list | dict, dt: datetime, key: str = "value"
) -> float | None:
    if isinstance(mode_capacity, dict):
        return mode_capacity[key]
    elif isinstance(mode_capacity, list):
        capacity_tuples = [(d["datetime"], d[key]) for d in mode_capacity]

        if dt.isoformat() <= min(capacity_tuples)[0]:
            return min(capacity_tuples)[1]
        else:
            # valid datetime is the max datetime that is lower than the given datetime
            # In other words, it is the most recent value that is valid for the given dt
            return max([(d, v) for d, v in capacity_tuples if d <= dt.isoformat()])[1]


def get_capacity_sources(capacity_config: dict, dt: datetime) -> list[str]:
    """Gets the capacity sources for a given zone and datetime from ZONES_CONFIG."""
    capacity_sources = {}
    for mode, capacity_value in capacity_config.items():
        if not isinstance(capacity_value, (int, float)):
            capacity_sources[mode] = get_capacity_value_with_datetime(
                capacity_value, dt, key="source"
            )
    return capacity_sources


def get_capacity_sources(zone: ZoneKey, dt: datetime) -> list[str]:
    """Gets the capacity sources for a given zone and datetime from ZONES_CONFIG."""
    capacity_config = ZONES_CONFIG[zone].get("capacity", {})
    capacity_sources = {}
    for mode, capacity_value in capacity_config.items():
        if not isinstance(capacity_value, (int, float)):
            capacity_sources[mode] = get_capacity_value_with_datetime(
                capacity_value, dt, key="source"
            )
    return capacity_sources
