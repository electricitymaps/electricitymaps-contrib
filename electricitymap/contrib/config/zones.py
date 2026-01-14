"""This module contains functions for working with zones configs."""

from collections import defaultdict
from typing import Any

from electricitymap.contrib.types import BoundingBox, ZoneKey


def zone_bounding_boxes(zones_config: dict[ZoneKey, Any]) -> dict[ZoneKey, BoundingBox]:
    """Returns a dict mapping each zone to its bounding box."""
    bounding_boxes = {}
    for zone_id, zone_config in zones_config.items():
        if "bounding_box" in zone_config:
            bounding_boxes[zone_id] = zone_config["bounding_box"]
    return bounding_boxes


def zone_parents(zones_config: dict[ZoneKey, Any]) -> dict[ZoneKey, ZoneKey]:
    """Returns a dict mapping each zone to its parent zone."""
    zone_parents = {}
    for zone_id, zone_config in zones_config.items():
        if "subZoneNames" in zone_config:
            for sub_zone_id in zone_config["subZoneNames"]:
                zone_parents[sub_zone_id] = zone_id
    return zone_parents


def generate_zone_neighbours(
    zones_config: dict[ZoneKey, Any], exchanges_config: dict[ZoneKey, Any]
) -> dict[ZoneKey, list[ZoneKey]]:
    """Returns a dict mapping each zone to its neighbours.

    Neighbours are defined as zones that are connected by an exchange.
    This represents the edges of the flow-tracing graph.
    """
    zone_neighbours = defaultdict(set)
    for k, v in exchanges_config.items():
        if not v.get("parsers", {}).get("exchange", None):
            # Interconnector config has no parser, and will therefore not be part
            # of the flowtracing graph.
            continue
        try:
            zone_1, zone_2 = k.split("->")
            zone_1 = ZoneKey(zone_1)
            zone_2 = ZoneKey(zone_2)
            if zones_config[zone_1].get("subZoneNames") or zones_config[zone_2].get(
                "subZoneNames"
            ):
                # Both zones must not have subzones.
                continue
            pairs = [(zone_1, zone_2), (zone_2, zone_1)]
            for zone_name_1, zone_name_2 in pairs:
                zone_neighbours[zone_name_1].add(zone_name_2)
        except Exception:
            continue
    # Sort the lists of neighbours for each zone.
    return {k: sorted(v) for k, v in zone_neighbours.items()}


def generate_all_neighbours(
    exchanges_config: dict[ZoneKey, Any],
) -> dict[ZoneKey, list[ZoneKey]]:
    """This object represents all neighbours regardless of granularity."""
    zone_neighbours = defaultdict(set)
    for k in exchanges_config:
        zone_1, zone_2 = k.split("->")
        pairs = [(zone_1, zone_2), (zone_2, zone_1)]
        for zone_name_1, zone_name_2 in pairs:
            zone_neighbours[zone_name_1].add(zone_name_2)
    # Sort the lists of neighbours for each zone.
    return {k: sorted(v) for k, v in zone_neighbours.items()}
