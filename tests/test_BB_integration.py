import unittest
from datetime import datetime

from electricitymap.contrib.lib.types import ZoneKey
from parsers.BB import fetch_consumption, fetch_production


class TestBBIntegration(unittest.TestCase):
    def test_fetch_production_integration(self):
        # Test the integration of fetch_production with the actual data source
        result = fetch_production(
            zone_key=ZoneKey("BB"), target_datetime=datetime(2025, 4, 20)
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("production", result[0])

    def test_fetch_consumption_integration(self):
        # Test the integration of fetch_consumption with the actual data source
        result = fetch_consumption(
            zone_key=ZoneKey("BB"), target_datetime=datetime(2025, 4, 20)
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("consumption", result[0])


if __name__ == "__main__":
    unittest.main()
