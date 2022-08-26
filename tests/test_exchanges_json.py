import unittest

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG

ZONE_KEYS = ZONES_CONFIG.keys()


class ExchangeJsonTestcase(unittest.TestCase):
    def test_all_zones_in_zones_json(self):
        for zone_key, values in EXCHANGES_CONFIG.items():
            self.assertIn("->", zone_key)
            for zone in zone_key.split("->"):
                if zone == "US":
                    # Old US zone that we ignore
                    continue
                self.assertIn(zone, ZONE_KEYS)


if __name__ == "__main__":
    unittest.main(buffer=True)
