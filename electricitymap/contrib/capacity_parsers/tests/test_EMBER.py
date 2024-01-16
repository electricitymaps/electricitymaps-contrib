import unittest

import pandas as pd

from electricitymap.contrib.capacity_parsers.EMBER import map_variable_to_mode

test_df = pd.DataFrame(
    [
        {"zone_key": "TR", "variable": "Other Fossil", "value": 1},
        {"zone_key": "TR", "variable": "Other Renewables", "value": 1},
        {"zone_key": "CO", "variable": "Other Fossil", "value": 1},
        {"zone_key": "BO", "variable": "Solar", "value": 1},
    ]
)


class testEmber(unittest.TestCase):
    def test_map_variable_to_mode(self):
        test_df["mode"] = test_df.apply(map_variable_to_mode, axis=1)
        self.assertEqual(
            test_df["mode"].tolist(), ["oil", "geothermal", "oil", "solar"]
        )


if __name__ == "__main__":
    unittest.main()
