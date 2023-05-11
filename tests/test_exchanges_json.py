import unittest

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG


class ExchangeJsonTestcase(unittest.TestCase):
    def test_all_zones_in_zones_json(self):
        zone_keys = ZONES_CONFIG.keys()
        for zone_key, values in EXCHANGES_CONFIG.items():
            self.assertIn("->", zone_key)
            for zone in zone_key.split("->"):
                if zone == "US":
                    # Old US zone that we ignore.
                    continue
                self.assertIn(zone, zone_keys)


if __name__ == "__main__":
    unittest.main(buffer=True)
