import unittest
from pathlib import Path

from electricitymap.contrib import config


class ConfigTestcase(unittest.TestCase):
    def test_ZONE_NEIGHBOURS(self):
        self.assertIn("DK-DK1", config.ZONE_NEIGHBOURS.keys())
        dk_neighbours = config.ZONE_NEIGHBOURS["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )
        self.assertEqual(
            sorted(dk_neighbours), dk_neighbours, "neighbours should be sorted"
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
