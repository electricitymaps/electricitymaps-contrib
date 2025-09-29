"""Tests for ZONE_CONFIG, config loaded from config/zones/*.yaml."""

import json
import unittest

from electricitymap.contrib.config import ZONES_CONFIG


class ZonesJsonTestcase(unittest.TestCase):
    def test_bounding_boxes(self):
        for values in ZONES_CONFIG.values():
            bbox = values.get("bounding_box")
            if bbox:
                self.assertLess(bbox[0][0], bbox[1][0])
                self.assertLess(bbox[0][1], bbox[1][1])

    def test_sub_zones(self):
        zone_keys = set(ZONES_CONFIG.keys())
        for values in ZONES_CONFIG.values():
            sub_zones = values.get("subZoneNames", [])
            for sub_zone in sub_zones:
                self.assertIn(sub_zone, zone_keys)

    def test_zones_from_geometries_exist(self):
        with open("web/geo/world.geojson") as file:
            world_geometries = json.load(file)
        world_geometries_zone_keys = set()
        for ft in world_geometries["features"]:
            world_geometries_zone_keys.add(ft["properties"]["zoneName"])
        all_zone_keys = set(ZONES_CONFIG.keys())
        non_existing_zone_keys = sorted(world_geometries_zone_keys - all_zone_keys)
        assert (
            len(non_existing_zone_keys) == 0
        ), f"{non_existing_zone_keys} are defined in world.geojson but not in zones/*.yaml"


if __name__ == "__main__":
    unittest.main(buffer=True)
