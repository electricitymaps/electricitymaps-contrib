import json
import unittest

from electricitymap.contrib.config import ZONES_CONFIG

ZONE_KEYS = ZONES_CONFIG.keys()


class ZonesJsonTestcase(unittest.TestCase):
    def test_bounding_boxes(self):
        for zone, values in ZONES_CONFIG.items():
            bbox = values.get("bounding_box")
            if bbox:
                self.assertLess(bbox[0][0], bbox[1][0])
                self.assertLess(bbox[0][1], bbox[1][1])

    def test_sub_zones(self):
        for zone, values in ZONES_CONFIG.items():
            sub_zones = values.get("subZoneNames", [])
            for sub_zone in sub_zones:
                self.assertIn(sub_zone, ZONE_KEYS)

    def test_zones_from_geometries_exist(self):
        world_geometries = json.load(open("web/geo/world.geojson"))
        world_geometries_zone_keys = set()
        for ft in world_geometries["features"]:
            world_geometries_zone_keys.add(ft["properties"]["zoneName"])
        all_zone_keys = set(ZONES_CONFIG.keys())
        non_existing_zone_keys = sorted(world_geometries_zone_keys - all_zone_keys)
        assert (
            len(non_existing_zone_keys) == 0
        ), f"{non_existing_zone_keys} are defined in world.geojson but not in zones.json"


if __name__ == "__main__":
    unittest.main(buffer=True)
