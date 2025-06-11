import json
from datetime import datetime, timedelta, timezone
from importlib import resources

import numpy as np
import pandas as pd
import pytest
from requests_mock import ANY

from parsers.OPENNEM import (
    fetch_price,
    fetch_production,
    filter_production_objs,
    sum_vector,
)


def test_sum_vector():
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
    sum_solar_ignore_nans = sum_vector(row, emap_to_parser["solar"], ignore_nans=True)
    sum_wind = sum_vector(row, emap_to_parser["wind"])

    assert sum_coal == sum(values_coal)
    assert sum_solar is None
    assert sum_solar_ignore_nans == sum(values_solar[:1])
    assert sum_wind == sum(values_wind)


def test_filter_production_objs():
    now = datetime.now(timezone.utc)
    objs = [
        {
            "datetime": now - timedelta(hours=1),
            "production": {
                "coal": 12,
                "solar": 1.0,
            },
            "capacity": {
                "coal": 12,
            },
        },
        {
            "datetime": now - timedelta(hours=2),
            "production": {
                "coal": 12,
                "solar": None,
            },
            "capacity": {
                "coal": 12,
            },
        },
        {
            "datetime": now - timedelta(hours=3),
            "production": {
                "coal": None,
                "solar": 0,
            },
        },
    ]
    filtered_objs = filter_production_objs(objs)
    # 2nd entry should be filtered out because solar is None
    # 3rd entry should be filtered out because it's only 0 values for solar
    assert len(filtered_objs) == 1


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.OPENNEM")
            .joinpath("OPENNEM.json")
            .read_text()
        ),
    )


def test_production(adapter, session, snapshot):
    assert snapshot == fetch_production(
        "AU-VIC", session, datetime.fromisoformat("2025-03-23")
    )


def test_price(adapter, session, snapshot):
    assert snapshot == fetch_price(
        "AU-VIC", session, datetime.fromisoformat("2025-03-23")
    )
