from datetime import datetime, timezone
from importlib import resources
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time
from requests_mock import GET

from electricitymap.contrib.parsers.TH import (
    MEA_BASEPRICE_URL,
    MEA_FT_URL,
    TZ,
    _as_localtime,
    fetch_price,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture
def mock_mea_pages(requests_mock):
    requests_mock.register_uri(
        GET,
        MEA_BASEPRICE_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks.TH")
        .joinpath("mea_baseprice.html")
        .read_bytes(),
    )
    requests_mock.register_uri(
        GET,
        MEA_FT_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks.TH")
        .joinpath("mea_ft.html")
        .read_bytes(),
    )


# --- _as_localtime --------------------------------------------------------


@freeze_time("2024-04-15 12:00:00+07:00")
def test_as_localtime_none_returns_bangkok_now():
    """With no input, `_as_localtime` returns the current Bangkok time."""
    result = _as_localtime(None)

    assert result.tzinfo is TZ
    assert result == datetime(2024, 4, 15, 12, 0, tzinfo=TZ)


def test_as_localtime_tz_aware_converts_to_bangkok():
    """A tz-aware UTC datetime is converted to the equivalent Bangkok time."""
    utc_dt = datetime(2024, 4, 15, 5, 0, tzinfo=timezone.utc)

    result = _as_localtime(utc_dt)

    assert result.tzinfo is TZ
    # 05:00 UTC == 12:00 Bangkok (UTC+7).
    assert result == datetime(2024, 4, 15, 12, 0, tzinfo=TZ)


def test_as_localtime_preserves_instant_across_zones():
    """Same instant expressed in two different tz-aware inputs yields the
    same Bangkok datetime — guards against accidental host-TZ leakage."""
    utc_dt = datetime(2024, 4, 15, 5, 0, tzinfo=timezone.utc)
    cest_dt = datetime(2024, 4, 15, 7, 0, tzinfo=ZoneInfo("Europe/Stockholm"))

    assert _as_localtime(utc_dt) == _as_localtime(cest_dt)


def test_as_localtime_rejects_naive_datetime():
    """Naive inputs would be silently reinterpreted as host-local time by
    `astimezone`, so the helper must fail loudly instead."""
    naive_dt = datetime(2024, 4, 15, 12, 0)

    with pytest.raises(ValueError, match="timezone-aware"):
        _as_localtime(naive_dt)


# --- fetch_price ---------------------------------------------------------


@freeze_time("2024-04-15 12:00:00+07:00")
def test_snapshot_fetch_price(session, snapshot, mock_mea_pages):
    """Snapshot the full fetch_price output. Exercises BeautifulSoup(lxml)
    parsing over both MEA HTML pages."""
    assert snapshot == fetch_price(zone_key=ZoneKey("TH"), session=session)


@freeze_time("2024-04-15 05:00:00+00:00")
def test_fetch_price_datetime_is_tz_aware_bangkok(session, mock_mea_pages):
    """The emitted price datetime must be tz-aware and anchored in Bangkok
    local time, independent of the host timezone."""
    [event] = fetch_price(zone_key=ZoneKey("TH"), session=session)

    assert event["datetime"].tzinfo is TZ
    # Frozen moment is 05:00 UTC == 12:00 Bangkok; the parser truncates to
    # the hour, so we expect 12:00 Bangkok.
    assert event["datetime"] == datetime(2024, 4, 15, 12, 0, tzinfo=TZ)
