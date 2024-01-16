import unittest
from datetime import datetime

import pandas as pd

from electricitymap.contrib.capacity_parsers.OPENNEM import (
    filter_capacity_data_by_datetime,
)

test_df = pd.DataFrame(
    [
        {"datetime": datetime(2021, 1, 1), "value": 1},
        {"datetime": datetime(2022, 1, 20), "value": 1},
        {"datetime": datetime(2022, 4, 12), "value": 1},
        {"datetime": datetime(2022, 10, 3), "value": 1},
        {"datetime": datetime(2023, 3, 1), "value": 1},
    ]
)


class TestOPENNEM(unittest.TestCase):
    def test_filter_capacity_data_by_datetime(self):
        target_datetime_1 = datetime(2022, 3, 1)
        filtered_df_1 = filter_capacity_data_by_datetime(test_df, target_datetime_1)
        target_datetime_2 = datetime(2023, 10, 1)
        filtered_df_2 = filter_capacity_data_by_datetime(test_df, target_datetime_2)
        target_datetime_3 = datetime(2020, 10, 1)
        filtered_df_3 = filter_capacity_data_by_datetime(test_df, target_datetime_3)

        assert filtered_df_1.equals(
            test_df.loc[test_df["datetime"] <= target_datetime_1]
        )
        assert filtered_df_2.equals(test_df)
        assert filtered_df_3.equals(
            test_df.loc[test_df["datetime"] <= datetime(2021, 1, 1)]
        )


if __name__ == "__main__":
    unittest.main()
