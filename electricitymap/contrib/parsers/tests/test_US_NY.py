#!/usr/bin/env python3

"""Tests for US_NY.py"""

import datetime as dt
from pathlib import Path

from freezegun import freeze_time

from electricitymap.contrib.parsers import US_NY
from electricitymap.contrib.types import ZoneKey


def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot):
    adapter.register_uri(
        "GET",
        "http://mis.nyiso.com/public/csv/isolf/20250219isolf.csv",
        content=Path(
            "electricitymap/contrib/parsers/tests/mocks/US_NY/20250219isolf.csv"
        ).read_bytes(),
    )

    with freeze_time("2025-02-20 00:00:00"):
        result = US_NY.fetch_consumption_forecast(
            zone_key=ZoneKey("US-NY-NYIS"),
            session=session,
        )

    assert snapshot == result


def test_snapshot_fetch_production_more_than_9_days_in_past(adapter, session, snapshot):
    adapter.register_uri(
        "GET",
        "http://mis.nyiso.com/public/csv/rtfuelmix/20250201rtfuelmix_csv.zip",
        content=Path(
            "electricitymap/contrib/parsers/tests/mocks/US_NY/20250201rtfuelmix_csv.zip"
        ).read_bytes(),
    )

    result = US_NY.fetch_production(
        zone_key=ZoneKey("US-NY-NYIS"),
        session=session,
        target_datetime=dt.datetime.fromisoformat("2025-02-20 00:00:00"),
    )

    assert snapshot == result
