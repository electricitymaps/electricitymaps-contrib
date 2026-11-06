import logging
from datetime import datetime, timezone

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.SEMO import API_URL as SEMO_API_URL
from electricitymap.contrib.parsers.SEMOxSMARTGRID import fetch_production
from electricitymap.contrib.parsers.SMARTGRIDDASHBOARD import URL as SMARTGRID_URL
from electricitymap.contrib.parsers.tests.test_SEMO import _bm086, _register_mapping
from electricitymap.contrib.types import ZoneKey

# SEMO fixture (IE) is at 00:00 and 00:30 UTC on 2026-09-20.
# SmartGrid is 15-min in Dublin local time (UTC+1 in September), so 01:00 Dublin
# == 00:00 UTC. The 30-min value is labelled at the end of its window, so 00:30
# averages the 00:15 and 00:30 readings.
WIND_ROWS = [
    ("20-Sep-2026 01:00:00", 300.0),  # UTC 00:00 -> label 00:00
    ("20-Sep-2026 01:15:00", 340.0),  # UTC 00:15 -> label 00:30
    ("20-Sep-2026 01:30:00", 400.0),  # UTC 00:30 -> label 00:30 (mean = 370)
    ("20-Sep-2026 01:45:00", 360.0),  # UTC 00:45 -> label 01:00
]
SOLAR_ROWS = [
    ("20-Sep-2026 01:00:00", 10.0),  # label 00:00
    ("20-Sep-2026 01:15:00", 30.0),  # label 00:30
    ("20-Sep-2026 01:30:00", 40.0),  # label 00:30 (mean = 35)
    ("20-Sep-2026 01:45:00", 60.0),  # label 01:00
]


def _rows(pairs):
    return {"Rows": [{"EffectiveTime": t, "Value": v} for t, v in pairs]}


def _register_smartgrid(
    requests_mock, wind=WIND_ROWS, solar=SOLAR_ROWS, generation=None
):
    requests_mock.register_uri(
        GET, f"{SMARTGRID_URL}?areas=windactual", json=_rows(wind)
    )
    requests_mock.register_uri(
        GET, f"{SMARTGRID_URL}?areas=solaractual", json=_rows(solar)
    )
    if generation is not None:
        requests_mock.register_uri(
            GET, f"{SMARTGRID_URL}?areas=generationactual", json=_rows(generation)
        )


def _ie(requests_mock, session):
    return fetch_production(
        zone_key=ZoneKey("IE"),
        session=session,
        target_datetime=datetime(2026, 9, 20, tzinfo=timezone.utc),
    )


def test_merge_uses_smartgrid_wind_solar_and_semo_rest(requests_mock, session):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    _register_smartgrid(requests_mock)

    events = _ie(requests_mock, session)
    first = next(
        e for e in events if e["datetime"] == datetime(2026, 9, 20, tzinfo=timezone.utc)
    )
    p = first["production"]
    # wind/solar come from SmartGrid (resampled), not SEMO's 100/50.
    # At 00:00 only the 00:00 reading is in-window.
    assert p["wind"] == 300
    assert p["solar"] == 10
    # everything else comes from SEMO.
    assert p["gas"] == 240
    assert p["oil"] == 15
    # SEMO coal (80) is mapped to unknown, joining the unmatched-unit 12.
    assert p.get("coal") is None
    assert p["unknown"] == 92
    assert first["storage"] == {"battery": 20.0, "hydro": -25.0}


def test_merge_omits_wind_solar_when_smartgrid_timestamp_missing(
    requests_mock, session
):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    # SmartGrid only has the 00:00 reading, so nothing lands in the 00:30 window.
    _register_smartgrid(
        requests_mock,
        wind=[("20-Sep-2026 01:00:00", 300.0)],
        solar=[("20-Sep-2026 01:00:00", 10.0)],
    )

    events = _ie(requests_mock, session)
    at_0030 = next(
        e
        for e in events
        if e["datetime"] == datetime(2026, 9, 20, 0, 30, tzinfo=timezone.utc)
    )
    p = at_0030["production"]
    # No SmartGrid data at this timestamp -> wind/solar unset (no SEMO fallback).
    assert p.get("wind") is None
    assert p.get("solar") is None
    assert p["gas"] == 190  # SEMO mode still present


def test_merge_includes_smartgrid_only_timestamps(requests_mock, session):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    # Extra SmartGrid readings at UTC 01:45 + 02:00 (02:45/03:00 Dublin) both fall
    # in the 02:00 window, beyond SEMO's data.
    _register_smartgrid(
        requests_mock,
        wind=WIND_ROWS
        + [("20-Sep-2026 02:45:00", 500.0), ("20-Sep-2026 03:00:00", 500.0)],
        solar=SOLAR_ROWS
        + [("20-Sep-2026 02:45:00", 70.0), ("20-Sep-2026 03:00:00", 90.0)],
    )

    events = _ie(requests_mock, session)
    at_0200 = next(
        e
        for e in events
        if e["datetime"] == datetime(2026, 9, 20, 2, 0, tzinfo=timezone.utc)
    )
    p = at_0200["production"]
    # Newest SmartGrid wind/solar are kept even though SEMO has no data here.
    assert p["wind"] == 500
    assert p["solar"] == 80
    assert p.get("gas") is None


def test_smartgrid_outside_target_window_is_excluded(requests_mock, session):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    # SmartGridDashboard always returns up-to-now data; here it also serves
    # 22-Oct readings, far outside the 20-Sep target window. They must be dropped
    # so the output stays on the surrounding days.
    _register_smartgrid(
        requests_mock,
        wind=WIND_ROWS
        + [("22-Oct-2026 01:00:00", 999.0), ("22-Oct-2026 01:15:00", 999.0)],
        solar=SOLAR_ROWS
        + [("22-Oct-2026 01:00:00", 99.0), ("22-Oct-2026 01:15:00", 99.0)],
    )

    events = _ie(requests_mock, session)
    assert events
    assert all(
        e["datetime"] < datetime(2026, 10, 1, tzinfo=timezone.utc) for e in events
    )


def test_semo_breakdown_without_wind_solar_when_smartgrid_unavailable(
    requests_mock, session, caplog
):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    # SmartGrid endpoints are not registered -> unavailable.
    with caplog.at_level(logging.WARNING):
        events = _ie(requests_mock, session)
    first = events[0]
    # Wind/solar are never taken from SEMO, so they are unset here.
    assert first["production"].get("wind") is None
    assert first["production"].get("solar") is None
    assert first["production"]["gas"] == 240  # SEMO breakdown still present
    assert any("SmartGridDashboard" in r.message for r in caplog.records)


def test_raises_when_semo_unavailable(requests_mock, session):
    # SEMO mapping page/API not registered -> SEMO errors. We must not fall back
    # to a wind/solar-only result.
    _register_smartgrid(
        requests_mock,
        wind=[("20-Sep-2026 01:00:00", 300.0)],
        solar=[("20-Sep-2026 01:00:00", 50.0)],
    )
    with pytest.raises(ParserException):
        _ie(requests_mock, session)


def test_returns_nothing_when_semo_beyond_retention(requests_mock, session, caplog):
    # SEMO is reachable but has no data for the target (older than BM-086's
    # ~3-month retention): the parser must return no data, not SmartGrid-only.
    _register_mapping(requests_mock)
    empty = {"pagination": {"totalItems": 0}, "items": []}
    requests_mock.register_uri(GET, SEMO_API_URL, json=empty)
    _register_smartgrid(requests_mock)
    with caplog.at_level(logging.WARNING):
        events = _ie(requests_mock, session)
    assert events == []
    assert any("retention" in r.message for r in caplog.records)


def test_raises_when_both_sources_unavailable(requests_mock, session):
    with pytest.raises(ParserException):
        _ie(requests_mock, session)
