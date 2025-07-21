import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from requests_mock import ANY, GET

from electricitymap.contrib.capacity_parsers.OPENELECTRICITY import (
    fetch_production_capacity,
    filter_capacity_data_by_datetime,
)
from electricitymap.contrib.config import ZoneKey

base_path_to_mock = Path("capacity_parsers/tests/mocks/OPENELECTRICITY")


test_df = pd.DataFrame(
    [
        {"datetime": datetime(2021, 1, 1), "value": 1},
        {"datetime": datetime(2022, 1, 20), "value": 1},
        {"datetime": datetime(2022, 4, 12), "value": 1},
        {"datetime": datetime(2022, 10, 3), "value": 1},
        {"datetime": datetime(2023, 3, 1), "value": 1},
    ]
)


def test_filter_capacity_data_by_datetime():
    target_datetime_1 = datetime(2022, 3, 1)
    filtered_df_1 = filter_capacity_data_by_datetime(test_df, target_datetime_1)
    target_datetime_2 = datetime(2023, 10, 1)
    filtered_df_2 = filter_capacity_data_by_datetime(test_df, target_datetime_2)
    target_datetime_3 = datetime(2020, 10, 1)
    filtered_df_3 = filter_capacity_data_by_datetime(test_df, target_datetime_3)

    assert filtered_df_1.equals(test_df.loc[test_df["datetime"] <= target_datetime_1])
    assert filtered_df_2.equals(test_df)
    assert filtered_df_3.equals(
        test_df.loc[test_df["datetime"] <= datetime(2021, 1, 1)]
    )


def openelectricity_token_env():
    os.environ["OPENELECTRICITY_TOKEN"] = "token"


def test_fetch_capacities(adapter, session, snapshot):
    data = Path(base_path_to_mock, "AU-QLD_capacities.json")
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_text(),
    )

    assert snapshot == fetch_production_capacity(ZoneKey("AU-QLD"), session)
