import unittest
from datetime import datetime

import pandas as pd

from electricitymap.contrib.capacity_parsers.EMBER import map_variable_to_mode

test_df = pd.DataFrame(
    [
        {"zone_key": "TR", "mode": "Other Fossil", "value": 1},
        {"zone_key": "TR", "mode": "Other Renewables", "value": 1},
        {"zone_key": "CO", "mode": "Other Fossil", "value": 1},
        {"zone_key": "BO", "mode": "Solar", "value": 1},
    ]
)


class testEmber(unittest.TestCase):
    def test_map_variable_to_mode(self):
        expected_df = pd.DataFrame(
            [
                {"zone_key": "TR", "mode": "oil", "value": 1},
                {"zone_key": "TR", "mode": "geothermal", "value": 1},
                {"zone_key": "CO", "mode": "oil", "value": 1},
                {"zone_key": "BO", "mode": "solar", "value": 1},
            ]
        )
        mapped_df = test_df.apply(map_variable_to_mode, axis=1)
        pd.testing.assert_frame_equal(expected_df, mapped_df)


if __name__ == "__main__":
    unittest.main()
