"""Tests for the configs provided by the electricitymap.contrib.config
package.

The values in these configs should be loaded from the config files in the
config/ directory. The tests in this file ensure that the values are loaded.
It doesn't check all or most values, but serves as a sanity check that the
configs are loaded correctly.
"""

import unittest
from pathlib import Path

from electricitymap.contrib import config
from electricitymap.contrib.types import ZoneKey

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()


class ConfigTestcase(unittest.TestCase):
    def test_zones_config(self):
        # ZONES_CONFIG is a dict mapping zones to their config,
        # which includes lots of keys with information about the zone.
        self.assertIn("DK-DK1", config.ZONES_CONFIG.keys())
        self.assertIn("bounding_box", config.ZONES_CONFIG[ZoneKey("DK-DK1")].keys())
        self.assertIn("capacity", config.ZONES_CONFIG[ZoneKey("DK-DK1")].keys())

    def test_zone_parent(self):
        # ZONE_PARENT is a dict mapping zones to their parent zones.
        self.assertIn("DK-DK1", config.ZONE_PARENT.keys())
        self.assertEqual(config.ZONE_PARENT[ZoneKey("DK-DK1")], "DK")

    def test_zone_bounding_box(self):
        # ZONE_BOUNDING_BOX is a dict mapping zones to their bounding box,
        # which is a list like [[12.343, 1.343], [34.4333, 23.3434]].
        self.assertIn("DK-DK1", config.ZONE_BOUNDING_BOXES.keys())
        self.assertEqual(len(config.ZONE_BOUNDING_BOXES[ZoneKey("DK-DK1")]), 2)

    def test_zone_neighbours(self):
        # ZONE_NEIGHBOURS is a dict mapping zones to their neighbours.
        self.assertIn("DK-DK1", config.ZONE_NEIGHBOURS.keys())
        dk_neighbours = config.ZONE_NEIGHBOURS[ZoneKey("DK-DK1")]
        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )

    def test_emission_factors(self):
        # The emission_factors returns a dict of emission factors for a zone.
        # The keys are the fuel types and the values are the emission factors.
        factors = config.emission_factors(ZoneKey("DK-DK1"))
        self.assertIn("biomass", factors.keys())
        self.assertIn("gas", factors.keys())
        self.assertIn("wind", factors.keys())
        self.assertGreater(factors["gas"], 0)



def test_data_centers_config(snapshot):
    assert snapshot == config.DATA_CENTERS_CONFIG.data_centers[1]

if __name__ == "__main__":
    unittest.main(buffer=True)
