from datetime import datetime

import pytest

from electricitymap.contrib.config.capacity import (
    get_capacity_data,
    get_capacity_sources,
    get_capacity_value_with_datetime,
)


def test_get_capacity_data():
    capacity_data = {}
    capacity_data_1 = {"solar": 3, "wind": 4}
    capacity_data_2 = {
        "coal": {"datetime": "2022-01-01", "value": 5},
        "gas": {"datetime": "2022-01-01", "value": 6},
    }
    capacity_data_3 = {
        "coal": [
            {"datetime": "2022-01-01", "value": 5},
            {"datetime": "2023-06-01", "value": 8},
        ],
        "gas": [
            {"datetime": "2022-01-01", "value": 6},
            {"datetime": "2023-06-01", "value": 7},
        ],
    }
    assert get_capacity_data(capacity_data, datetime(2023, 1, 1)) == {}
    assert get_capacity_data(capacity_data_1, datetime(2023, 1, 1)) == {
        "solar": 3,
        "wind": 4,
    }
    assert get_capacity_data(capacity_data_2, datetime(2022, 6, 1)) == {
        "coal": 5,
        "gas": 6,
    }
    assert get_capacity_data(capacity_data_3, datetime(2023, 6, 1)) == {
        "coal": 8,
        "gas": 7,
    }

    with pytest.raises(ValueError):
        get_capacity_data(capacity_data_2, datetime(2023, 0, 1))


def test_get_capacity_from_list():
    mode_capacity = [
        {"datetime": "2022-01-01", "value": 3, "source": "abc"},
        {"datetime": "2023-01-01", "value": 4, "source": "abc"},
    ]

    capacity_dt = datetime(2022, 1, 1)
    for item in mode_capacity:
        if datetime.fromisoformat(item["datetime"]).date() == capacity_dt.date():
            capacity = item["value"]

    assert capacity == 3


def test_get_capacity_sources_with_dt():
    mode_capacity = [
        {"datetime": "2022-01-01", "value": 3, "source": "abc"},
        {"datetime": "2023-01-01", "value": 4, "source": "abc"},
    ]

    capacity_dt = datetime(2022, 1, 1)
    assert (
        get_capacity_value_with_datetime(mode_capacity, capacity_dt, key="source")
        == "abc"
    )


def test_get_capacity_sources():
    def _test_get_capacity_sources(capacity, dt):
        capacity_sources = {}
        for mode, capacity_value in capacity.items():
            if not isinstance(capacity_value, (int, float)):
                capacity_sources[mode] = get_capacity_value_with_datetime(
                    capacity_value, dt, key="source"
                )
        return capacity_sources

    capacity = {
        "coal": [
            {"datetime": "2022-01-01", "value": 5, "source": "abc"},
            {"datetime": "2023-01-01", "value": 8, "source": "xyz"},
        ],
        "gas": {"datetime": "2022-01-01", "value": 6, "source": "def"},
    }

    assert _test_get_capacity_sources(capacity, datetime(2022, 1, 1)) == {
        "coal": "abc",
        "gas": "def",
    }
    assert _test_get_capacity_sources(capacity, datetime(2023, 1, 1)) == {
        "coal": "xyz",
        "gas": "def",
    }
