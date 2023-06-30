import unittest

import arrow
import numpy as np
import pandas as pd

from parsers.OPENNEM import filter_production_objs, process_solar_rooftop, sum_vector


class TestOPENNEM(unittest.TestCase):
    def test_process_solar_rooftop(self):
        idx = pd.date_range(
            start="2021-01-01 00:00:00+00:00",
            end="2021-01-01 01:00:00+00:00",
            freq="5T",
            inclusive="left",
        )
        df = pd.DataFrame(index=idx)
        rdn_any_column = np.random.rand(len(idx)).astype(float)
        df.loc[:, "any_column"] = rdn_any_column
        # No solar rooftop, nothing
        processed_df = process_solar_rooftop(df)
        pd.testing.assert_frame_equal(processed_df, df)

        # Solar rooftop, resampling
        df.loc[:, "SOLAR_ROOFTOP"] = np.nan
        df.loc[:, "SOLAR_ROOFTOP"].iloc[0] = 84.0
        processed_df = process_solar_rooftop(df)
        assert processed_df.index.equals(
            pd.date_range(
                start="2021-01-01 00:00:00+00:00",
                end="2021-01-01 01:00:00+00:00",
                freq="30T",
                inclusive="left",
            )
        )
        assert processed_df.loc[:, "SOLAR_ROOFTOP"].iloc[0] == 84.0
        assert np.isnan(processed_df.loc[:, "SOLAR_ROOFTOP"].iloc[1])
        assert round(processed_df.loc[:, "any_column"].iloc[0], 6) == round(
            rdn_any_column[:6].mean(), 6
        )

    def test_sum_vector(self):
        emap_to_parser = {
            "coal": ["COAL_a", "COAL_b"],
            "solar": ["SOLAR_1", "SOLAR_2"],
            "wind": ["WIND"],
        }
        values_coal = [1, 2]
        values_solar = [4, np.nan]
        values_wind = [1]
        all_values = [*values_coal, *values_solar, *values_wind]
        idx = emap_to_parser["coal"] + emap_to_parser["solar"] + emap_to_parser["wind"]
        row = pd.Series(all_values, index=idx)

        sum_coal = sum_vector(row, emap_to_parser["coal"])
        sum_solar = sum_vector(row, emap_to_parser["solar"])
        sum_solar_ignore_nans = sum_vector(
            row, emap_to_parser["solar"], ignore_nans=True
        )
        sum_wind = sum_vector(row, emap_to_parser["wind"])

        assert sum_coal == sum(values_coal)
        assert sum_solar is None
        assert sum_solar_ignore_nans == sum(values_solar[:1])
        assert sum_wind == sum(values_wind)

    def test_filter_production_objs(self):
        now = arrow.utcnow()
        objs = [
            {
                "datetime": now.shift(hours=-1).datetime,
                "production": {
                    "coal": 12,
                    "solar": 1.0,
                },
                "capacity": {
                    "coal": 12,
                },
            },
            {
                "datetime": now.shift(hours=-2).datetime,
                "production": {
                    "coal": 12,
                    "solar": None,
                },
                "capacity": {
                    "coal": 12,
                },
            },
        ]
        filtered_objs = filter_production_objs(objs)
        # 2nd entry should be filtered out because solar is None
        assert len(filtered_objs) == 1


if __name__ == "__main__":
    unittest.main()
