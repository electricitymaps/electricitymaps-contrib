import unittest
from pathlib import Path

from electricitymap.contrib.config import (
    generate_zone_neighbours,
    EXCHANGES_CONFIG,
    ZONES_CONFIG,
)


class ConfigTestcase(unittest.TestCase):
    def test_ZONE_NEIGHBOURS(self):
        zone_neighbours = generate_zone_neighbours(ZONES_CONFIG, EXCHANGES_CONFIG)
        self.assertIn("DK-DK1", zone_neighbours.keys())
        dk_neighbours = zone_neighbours["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )
        self.assertEqual(
            sorted(dk_neighbours), dk_neighbours, "neighbours should be sorted"
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
