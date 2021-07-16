import unittest

from electricitymap.contrib.config.model import load_model


class ConfigModelTestcase(unittest.TestCase):
    def test_pydantic_model(self):
        config = load_model()

        self.assertIn("DK-BHM->SE", config.exchanges.keys())
        self.assertIn("US-NW-PSCO", config.zones.keys())
        self.assertIsNotNone(
            config.zones["US-NW-PSCO"].parsers.get_function("production")
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
