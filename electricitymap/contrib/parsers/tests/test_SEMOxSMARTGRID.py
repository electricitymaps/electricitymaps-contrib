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
# == 00:00 UTC. Two 15-min points per half hour let us check 30-min resampling.
WIND_ROWS = [
    ("20-Sep-2026 01:00:00", 300.0),
    ("20-Sep-2026 01:15:00", 340.0),  # -> 00:00 UTC bucket mean = 320
    ("20-Sep-2026 01:30:00", 400.0),
    ("20-Sep-2026 01:45:00", 360.0),  # -> 00:30 UTC bucket mean = 380
]
SOLAR_ROWS = [
    ("20-Sep-2026 01:00:00", 10.0),
    ("20-Sep-2026 01:15:00", 30.0),  # -> 00:00 UTC bucket mean = 20
    ("20-Sep-2026 01:30:00", 40.0),
    ("20-Sep-2026 01:45:00", 60.0),  # -> 00:30 UTC bucket mean = 50
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
    assert p["wind"] == 320
    assert p["solar"] == 20
    # everything else comes from SEMO.
    assert p["gas"] == 240
    assert p["oil"] == 15
    # SEMO coal (80) is mapped to unknown, joining the unmatched-unit 12.
    assert p.get("coal") is None
    assert p["unknown"] == 92
    assert first["storage"] == {"battery": 20.0, "hydro": -25.0}


def test_returns_semo_only_with_warning_when_smartgrid_unavailable(
    requests_mock, session, caplog
):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, SEMO_API_URL, json=_bm086())
    # SmartGrid endpoints are not registered -> unavailable.
    with caplog.at_level(logging.WARNING):
        events = _ie(requests_mock, session)
    first = events[0]
    # Falls back to SEMO's own wind/solar (100/50 at 00:00).
    assert first["production"]["wind"] == 100
    assert first["production"]["solar"] == 50
    assert any("SmartGridDashboard" in r.message for r in caplog.records)


def test_returns_smartgrid_only_with_warning_when_semo_unavailable(
    requests_mock, session, caplog
):
    # SEMO mapping page/API not registered -> SEMO unavailable.
    _register_smartgrid(
        requests_mock,
        generation=[("20-Sep-2026 01:00:00", 1000.0)],
        wind=[("20-Sep-2026 01:00:00", 300.0)],
        solar=[("20-Sep-2026 01:00:00", 50.0)],
    )
    with caplog.at_level(logging.WARNING):
        events = _ie(requests_mock, session)
    assert len(events) > 0
    assert events[0]["production"]["wind"] == 300
    assert any("SEMO" in r.message for r in caplog.records)


def test_raises_when_both_sources_unavailable(requests_mock, session):
    with pytest.raises(ParserException):
        _ie(requests_mock, session)
