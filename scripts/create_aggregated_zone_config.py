#!/usr/bin/env python3
"""
Create an aggregation zone config file by looking up sub zones based on the zone name.
Sums capacities, all contributors.
poetry run python scripts/create_aggregated_zone_config US US-Central
"""
import argparse
from copy import deepcopy
from pathlib import Path

import yaml

from electricitymap.contrib.config.model import Capacity, Zone

NAME_MAPPING = {"hydro storage": "hydro_storage", "battery storage": "battery_storage"}


def create_aggregated_config(zoneKey: str, timezone: str):
    zone = Zone(
        key=zoneKey,
        sub_zone_names=[],
        timezone=timezone,
        contributors=[],
        capacity=Capacity(),
    )
    zone.parsers = None
    for path in Path("config/zones").glob(f"{zoneKey}-*.yaml"):
        if path.is_file():
            with open(path, "r") as file:
                subzone = yaml.safe_load(file.read())
                zone.sub_zone_names.append(path.stem)
                if "contributors" in subzone.keys():
                    zone.contributors = list(
                        set(zone.contributors + subzone["contributors"])
                    )
                if "capacity" in subzone.keys():
                    capacities: dict = subzone["capacity"]
                    for key, capacity in capacities.items():
                        mapped_key = (
                            key if not key in NAME_MAPPING else NAME_MAPPING[key]
                        )
                        if capacity is not None:
                            current_capacity = zone.capacity.__getattribute__(
                                mapped_key
                            )
                            if current_capacity is None:
                                current_capacity = 0
                            zone.capacity.__setattr__(
                                mapped_key, current_capacity + capacity
                            )

    zoneDict = deepcopy(zone.__dict__)
    for key, item in zone.__dict__.items():
        if item is None:
            del zoneDict[key]

    del zoneDict["key"]
    zoneDict["subZoneNames"] = zoneDict.pop("sub_zone_names")
    zoneDict["subZoneNames"] = sorted(zoneDict["subZoneNames"])
    zoneDict["capacity"] = deepcopy(zone.capacity.__dict__)

    zoneDict["capacity"]["hydro storage"] = zoneDict["capacity"].pop("hydro_storage")
    zoneDict["capacity"]["battery storage"] = zoneDict["capacity"].pop(
        "battery_storage"
    )
    for key, value in zoneDict["capacity"].items():
        if value is not None:
            zoneDict["capacity"][key] = round(value, 1)

    with open(f"config/zones/{zoneKey}.yaml", "w") as file:
        yaml.safe_dump(zoneDict, file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zone", help="The parent zone name (e.g. US)")
    parser.add_argument("timezone", help="The timezone of the parentzone")
    args = parser.parse_args()
    zone = args.zone
    timezone = args.timezone

    print(f"Creating {zone}")
    create_aggregated_config(zone, timezone)
    print(f"Created {zone}.yaml in config/zones.")


if __name__ == "__main__":
    main()
