import unittest
from datetime import datetime

import pandas as pd

from electricitymap.contrib.capacity_parsers.ONS import filter_data_by_date


class TestONS(unittest.TestCase):
    def test_filter_data_by_date(self):

        datetime_tuple1 = (datetime(1980, 1, 1), datetime(2015, 1, 1))
        datetime_tuple2 = (datetime(2018, 10, 1), datetime(2023, 10, 1))
        datetime_tuple3 = (datetime(2023, 7, 1), None)
        datetime_tuple4 = (datetime(2010, 1, 1), datetime(2024, 10, 1))

        test_df = pd.DataFrame(
            [
                {"start": datetime_tuple1[0], "end": datetime_tuple1[1], "value": 1},
                {"start": datetime_tuple2[0], "end": datetime_tuple2[1], "value": 1},
                {"start": datetime_tuple3[0], "end": datetime_tuple3[1], "value": 1},
                {"start": datetime_tuple4[0], "end": datetime_tuple4[1], "value": 1},
            ]
        )

        dt_1 = datetime(2019, 1, 1)
        dt_2 = datetime(2015, 1, 1)
        dt_3 = datetime(2023, 10, 31)

        df_1 = filter_data_by_date(test_df, dt_1)
        df_2 = filter_data_by_date(test_df, dt_2)
        df_3 = filter_data_by_date(test_df, dt_3)

        filtered_test_df_1 = test_df.loc[
            (test_df["start"].isin([datetime_tuple2[0], datetime_tuple4[0]]))
        ]

        filtered_test_df_2 = test_df.loc[
            (test_df["start"].isin([datetime_tuple1[0], datetime_tuple4[0]]))
        ]
        filtered_test_df_3 = test_df.loc[
            (test_df["start"].isin([datetime_tuple3[0], datetime_tuple4[0]]))
        ]

        assert df_1.equals(filtered_test_df_1)

        assert df_2.equals(filtered_test_df_2)

        assert df_3.equals(filtered_test_df_3)


if __name__ == "__main__":
    unittest.main()
