import unittest

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG


class ExchangeJsonTestcase(unittest.TestCase):
    def test_all_zones_in_zones_json(self):
        zone_keys = ZONES_CONFIG.keys()
        for zone_key in EXCHANGES_CONFIG:
            self.assertIn("->", zone_key)
            for zone in zone_key.split("->"):
                if zone == "US":
                    # Old US zone that we ignore.
                    continue
                self.assertIn(zone, zone_keys)

    def test_de_dk_dk1_capacity(self):
        self.assertEqual(EXCHANGES_CONFIG["DE->DK-DK1"]["capacity"], [-3500, 3500])


if __name__ == "__main__":
    unittest.main(buffer=True)
