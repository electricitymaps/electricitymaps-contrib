from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from electricitymap.contrib.parsers.ID import TZ, fetch_price
from electricitymap.contrib.types import ZoneKey


def test_fetch_price_returns_pln_residential_tariff():
    [event] = fetch_price(
        target_datetime=datetime(2020, 10, 1, 5, 34, tzinfo=timezone.utc)
    )

    assert event["zoneKey"] == ZoneKey("ID")
    assert event["datetime"].tzinfo is TZ
    assert event["datetime"] == datetime(2020, 10, 1, 12, tzinfo=TZ)
    assert event["currency"] == "IDR"
    assert event["price"] == 1_444_700
    assert event["source"] == "pln.co.id"


def test_fetch_price_rejects_dates_before_official_tariff_period():
    with pytest.raises(NotImplementedError, match="before 2020-10-01"):
        fetch_price(target_datetime=datetime(2020, 9, 30, 16, 59, tzinfo=timezone.utc))


def test_fetch_price_accepts_start_of_official_tariff_period():
    [event] = fetch_price(
        target_datetime=datetime(2020, 9, 30, 17, tzinfo=timezone.utc)
    )

    assert event["datetime"].tzinfo is TZ
    assert event["datetime"] == datetime(2020, 10, 1, tzinfo=TZ)


@freeze_time("2026-08-15 05:34:00+00:00")
def test_fetch_price_defaults_to_current_jakarta_hour():
    [event] = fetch_price()

    assert event["datetime"].tzinfo is TZ
    assert event["datetime"] == datetime(2026, 8, 15, 12, tzinfo=TZ)


def test_fetch_price_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        fetch_price(target_datetime=datetime(2026, 8, 15))
