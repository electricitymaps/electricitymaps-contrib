import importlib
from copy import deepcopy
from datetime import datetime
from logging import INFO, basicConfig, getLogger
from operator import itemgetter
from typing import Any

from requests import Session

from electricitymap.contrib.config import CONFIG_DIR, ZONE_PARENT
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.parsers import PARSER_KEY_TO_DICT
from scripts.utils import write_zone_config

logger = getLogger(__name__)
basicConfig(level=INFO)
ZONES_CONFIG = read_zones_config(CONFIG_DIR)
CAPACITY_MODES = PRODUCTION_MODES + [f"{mode} storage" for mode in STORAGE_MODES]


CAPACITY_PARSERS = PARSER_KEY_TO_DICT["productionCapacity"]

# Get productionCapacity source to zones mapping
CAPACITY_PARSER_SOURCE_TO_ZONES = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if zone_config.get("parsers", {}).get("productionCapacity") is None:
        continue
    source = zone_config.get("parsers", {}).get("productionCapacity").split(".")[0]
    if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
        CAPACITY_PARSER_SOURCE_TO_ZONES[source] = []
    CAPACITY_PARSER_SOURCE_TO_ZONES[source].append(zone_id)


def update_zone(
    zone: ZoneKey, target_datetime: datetime, session: Session, update_aggregate: bool
) -> None:
    """Generate capacity config and update the zone config yaml for a zone"""
    if zone not in CAPACITY_PARSERS:
        raise ValueError(f"No capacity parser developed for {zone}")
    parser = CAPACITY_PARSERS[zone]

    zone_capacity = parser(
        zone_key=zone, target_datetime=target_datetime, session=session
    )
    if not zone_capacity:
        raise ValueError(f"No capacity data for {zone} in {target_datetime.date()}")
    update_zone_capacity_config(zone, zone_capacity)

    if update_aggregate:
        zone_parent = ZONE_PARENT[zone]
        update_aggregated_capacity_config(zone_parent)


def update_source(source: str, target_datetime: datetime, session: Session) -> None:
    """Generate capacity config and update the zone config yaml for all zones included in source"""
    if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
        raise ValueError(f"No capacity parser developed for {source}")
    parser = importlib.import_module(
        f"electricitymap.contrib.capacity_parsers.{source}"
    ).fetch_production_capacity_for_all_zones
    source_capacity = parser(target_datetime=target_datetime, session=session)

    for zone in source_capacity:
        if not source_capacity[zone]:
            print(f"No capacity data for {zone} in {target_datetime.date()}")
            continue
        if zone in ZONES_CONFIG:
            update_zone_capacity_config(zone, source_capacity[zone])


def sort_config_keys(config: dict[str, Any]) -> dict[str, Any]:
    """Sort the keys of the config dict"""
    return {k: config[k] for k in sorted(config)}


def update_zone_capacity_config(zone_key: ZoneKey, data: dict) -> None:
    """Update the capacity config for a zone"""
    if zone_key not in ZONES_CONFIG:
        raise ValueError(f"Zone {zone_key} does not exist in the zones config")

    _new_zone_config = deepcopy(ZONES_CONFIG[zone_key])
    if "capacity" in _new_zone_config:
        capacity = _new_zone_config["capacity"]

        if all(isinstance(capacity[m], float | int) for m in capacity):
            # TODO: this is temporary as it handles the case of the deprecated system where capacity is a single value. It will be removed in the future
            capacity = {key: [value] for key, value in data.items()}
        else:
            capacity = generate_zone_capacity_config(capacity, data)
    else:
        capacity = {key: [value] for key, value in data.items()}

    _new_zone_config["capacity"] = capacity

    # sort keys
    _new_zone_config["capacity"] = sort_config_keys(_new_zone_config["capacity"])

    write_zone_config(zone_key, _new_zone_config)


def generate_zone_capacity_config(
    capacity_config: dict[str, Any], data: dict[str, Any]
) -> dict[str, Any]:
    """Generate capacity config depending on the type of the existing capacity data.
    If the existing capacity is simply a value, it will be overwritten with the new format.
    If the existing capacity is a list, the new data will be appended to the list.
    If the existing capacity is a dict, the new data will be add to create list if the datetime is different else the datapoint is overwritten.
    """
    existing_capacity_modes = [mode for mode in data if mode in capacity_config]
    updated_capacity_config = deepcopy(capacity_config)
    for mode in existing_capacity_modes:
        if isinstance(capacity_config[mode], float | int):
            updated_capacity_config[mode] = [data[mode]]
        elif isinstance(capacity_config[mode], list):
            updated_capacity_config[mode] = generate_zone_capacity_list(
                mode, capacity_config, data
            )
        else:
            raise ValueError(f"Invalid capacity config type for {mode}")

    new_modes = [m for m in data if m not in capacity_config]
    for mode in new_modes:
        updated_capacity_config[mode] = [data[mode]]
    return updated_capacity_config


def update_capacity_list_if_value_already_exists(
    mode: str, capacity_config: dict[str, Any], new_capacity: dict[str, Any]
) -> list[dict[str, Any]]:
    """Updates the capacity config for a zone if the capacity config is a list and the value already exists.
    This function ensures that we don't add the same value to the config over and over and that we can backfill and get the oldest value for which the capacity is valid.
    """
    existing_value_datetime = [
        item
        for item in capacity_config[mode]
        if item["value"] == new_capacity[mode]["value"]
    ][0]["datetime"]
    if new_capacity[mode]["datetime"] > existing_value_datetime:
        # if the associated datetime is more recent than the existing one, we don't add it
        return capacity_config[mode]
    else:
        # if the associated datetime is older than the existing one, we replace the datetime of the item
        return sorted(
            [
                new_capacity[mode]
                if item["value"] == new_capacity[mode]["value"]
                else item
                for item in capacity_config[mode]
            ],
            key=itemgetter("datetime"),
        )


def update_capacity_list_if_datetime_already_exists(
    mode: str, capacity_config: dict[str, Any], new_capacity: dict[str, Any]
) -> list[dict[str, Any]]:
    """Updates the capacity config for a zone if the capacity config is a list and the datetime already exists.
    If the new value is the same as the most recent previous entry, removes the redundant entry."""
    # Sort the existing capacity config by datetime
    sorted_config = sorted(capacity_config[mode], key=itemgetter("datetime"))

    # Find the index of the entry with the matching datetime
    target_index = next(i for i, item in enumerate(sorted_config) if item["datetime"] == new_capacity[mode]["datetime"])

    # Check if this is the earliest entry
    if target_index == 0:
        # If it's the earliest entry, just update it
        return sorted(
            [
                new_capacity[mode]
                if item["datetime"] == new_capacity[mode]["datetime"]
                else item
                for item in capacity_config[mode]
            ],
            key=itemgetter("datetime"),
        )

    # Check if the new value is the same as the most recent previous entry
    if new_capacity[mode]["value"] == sorted_config[target_index - 1]["value"]:
        # If it's the same, remove this entry as it's redundant
        return sorted(
            [
                item
                for item in capacity_config[mode]
                if item["datetime"] != new_capacity[mode]["datetime"]
            ],
            key=itemgetter("datetime"),
        )

    # Otherwise, update the entry with the new value
    return sorted(
        [
            new_capacity[mode]
            if item["datetime"] == new_capacity[mode]["datetime"]
            else item
            for item in capacity_config[mode]
        ],
        key=itemgetter("datetime"),
    )


def generate_zone_capacity_list(
    mode: str, capacity_config: dict[str, Any], new_capacity: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate the updated capacity config for a zone if the capacity config is a list.
    Optimizes storage by not adding redundant entries with the same value as the most recent previous entry."""
    # First check if the datetime already exists
    if new_capacity[mode]["datetime"] in [d["datetime"] for d in capacity_config[mode]]:
        return update_capacity_list_if_datetime_already_exists(
            mode, capacity_config, new_capacity
        )
    # If the datetime doesn't exist, we need to add the new capacity
    # Sort the existing capacity config by datetime to check chronological order
    sorted_config = sorted(capacity_config[mode], key=itemgetter("datetime"))

    # Find entries with datetimes before the new entry
    entries_before = [item for item in sorted_config if item["datetime"] < new_capacity[mode]["datetime"]]

    # If this is the earliest entry, we should add it
    if not entries_before:
        return sorted(
            capacity_config[mode] + [new_capacity[mode]], key=itemgetter("datetime")
        )

    # If the most recent entry before has a different value, we should add it
    if entries_before[-1]["value"] != new_capacity[mode]["value"]:
        return sorted(
            capacity_config[mode] + [new_capacity[mode]], key=itemgetter("datetime")
        )

    # If the value is the same as the most recent entry before, we don't need to add it
    return capacity_config[mode]


def check_capacity_config_type(capacity_config: list, config_type: type) -> bool:
    """Check that the capacity config is of the specified type"""
    return all(isinstance(item, config_type) for item in capacity_config)


def generate_aggregated_capacity_config(
    parent_zone: ZoneKey,
) -> dict[str, Any] | None:
    """Generate the aggregated capacity config for a parent zone"""
    zone_keys = [zone for zone in ZONE_PARENT if ZONE_PARENT[zone] == parent_zone]
    parent_capacity_config = ZONES_CONFIG[parent_zone]["capacity"]

    all_capacity_configs = [ZONES_CONFIG[zone]["capacity"] for zone in zone_keys]

    for mode in CAPACITY_MODES:
        mode_capacity_configs = [
            capacity_config[mode] for capacity_config in all_capacity_configs
        ]

        if not check_capacity_config_type(
            mode_capacity_configs, type(mode_capacity_configs[0])
        ):
            raise ValueError(
                f"{parent_zone} capacity could not be updated because all capacity configs must have the same type"
            )

        if check_capacity_config_type(mode_capacity_configs, list):
            parent_capacity_config[mode] = generate_aggregated_capacity_config_list(
                mode_capacity_configs, parent_zone
            )
        else:
            raise ValueError(
                f"{parent_zone} capacity could not be updated because all capacity configs must be  a list"
            )
    return parent_capacity_config


def generate_aggregated_capacity_config_dict(
    capacity_config: list[dict[str, Any]], parent_zone: ZoneKey
) -> dict[str, Any] | None:
    """Generate aggregated capacity config for a parent zone if the capacity config of the subzones are a dict"""
    datetime_values = {
        capacity_config["datetime"] for capacity_config in capacity_config
    }
    sources = {capacity_config["source"] for capacity_config in capacity_config}
    if len(datetime_values) != 1:
        logger.warning(
            f"{parent_zone} capacity could not be updated because all capacity configs must have the same datetime values"
        )
        return None
    else:
        updated_capacity = {}
        aggregated_value = compute_aggregated_value(capacity_config)
        updated_capacity["datetime"] = list(datetime_values)[0]
        updated_capacity["value"] = aggregated_value
        updated_capacity["source"] = ", ".join(
            [elem for elem in sources if elem is not None]
        )
        return sort_config_keys(updated_capacity)


def compute_aggregated_value(capacity_config: list[dict[str, Any]]) -> float | None:
    """Compute the aggregated capacity value as the sum of all subzone capacities"""
    if all(capacity_config["value"] is None for capacity_config in capacity_config):
        return None

    aggregated_value = sum(
        [
            0 if capacity_config["value"] is None else capacity_config["value"]
            for capacity_config in capacity_config
        ]
    )
    return aggregated_value


def generate_aggregated_capacity_config_list(
    capacity_config: list[Any], parent_zone: ZoneKey
) -> list[dict[str, Any]] | None:
    """Generate the aggregated capacity config for a parent zone if the capacity config of the subzones are a list"""
    flat_capacity_config = [item for sublist in capacity_config for item in sublist]
    datetime_values = {item["datetime"] for item in flat_capacity_config}
    updated_aggregated_capacity_config = []
    for dt in datetime_values:
        datetime_capacity_config = [
            item for item in flat_capacity_config if item["datetime"] == dt
        ]
        if len(datetime_capacity_config) == len(
            ZONES_CONFIG[ZoneKey(parent_zone)]["subZoneNames"]
        ):
            updated_aggregated_capacity_config.append(
                generate_aggregated_capacity_config_dict(
                    datetime_capacity_config, parent_zone
                )
            )
        else:
            logger.warning(
                f"{parent_zone} capacity could not be updated for {dt} because not all capacities are available"
            )
    return updated_aggregated_capacity_config


def update_aggregated_capacity_config(parent_zone: ZoneKey) -> None:
    """Update the aggregated capacity config for a parent zone"""
    if parent_zone not in ZONES_CONFIG:
        raise ValueError(f"Zone {parent_zone} does not exist in the zones config")

    _new_zone_config = deepcopy(ZONES_CONFIG[parent_zone])
    _new_zone_config["capacity"] = generate_aggregated_capacity_config(parent_zone)

    if _new_zone_config["capacity"] is not None:
        # sort keys
        _new_zone_config["capacity"] = sort_config_keys(_new_zone_config["capacity"])
        ZONES_CONFIG[parent_zone] = _new_zone_config
        write_zone_config(parent_zone, _new_zone_config)
    else:
        logger.warning(
            f"{parent_zone} capacity could not be updated because not all capacities are available"
        )

