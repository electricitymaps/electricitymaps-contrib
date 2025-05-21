from datetime import UTC, datetime

import pytest

from parsers.CH import get_solar_capacity_at


@pytest.mark.parametrize(
    "dt,expected",
    [
        ("2018-01-02", 2107.374),
        ("2022-01-01", 4080.415),
        ("2023-01-01", 5094.375),
        ("2024-01-01", 5108.034),
        # make sure past date for which we do not have historical capacity returns earliest available data
        ("2014-02-01", 1398.217),
        # make sure future date for which we do not have historical capacity returns latest available data
        ("2024-02-01", 5108.034),
    ],
)
def test_get_solar_capacity(dt, expected):
    target_datetime = datetime.fromisoformat(dt).replace(tzinfo=UTC)
    assert get_solar_capacity_at(target_datetime) == expected
