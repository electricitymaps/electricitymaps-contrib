from datetime import UTC, datetime

from electricitymap.contrib.parsers import IE
from electricitymap.contrib.types import ZoneKey


def _route(monkeypatch, target: datetime) -> list:
    calls = []
    monkeypatch.setattr(
        IE.CSO,
        "fetch_production_range",
        lambda zone, s, start, end, logger: calls.append(("cso", start, end)) or [],
    )
    monkeypatch.setattr(
        IE.SEMOxSMARTGRID,
        "fetch_production",
        lambda zone, s, target, logger: calls.append(("semo", target)) or [],
    )
    IE.fetch_production(ZoneKey("IE"), target_datetime=target)
    return calls


def test_cso_years_are_served_from_cso(monkeypatch):
    assert _route(monkeypatch, datetime(2022, 5, 11, tzinfo=UTC)) == [
        (
            "cso",
            datetime(2022, 5, 9, tzinfo=UTC),
            datetime(2022, 5, 12, 23, 59, 59, tzinfo=UTC),
        )
    ]


def test_window_crossing_into_2024_stops_at_cso_end(monkeypatch):
    assert _route(monkeypatch, datetime(2024, 1, 1, tzinfo=UTC)) == [
        (
            "cso",
            datetime(2023, 12, 30, tzinfo=UTC),
            datetime(2023, 12, 31, 23, 30, tzinfo=UTC),
        )
    ]


def test_later_dates_go_to_semoxsmartgrid(monkeypatch):
    target = datetime(2026, 11, 20, tzinfo=UTC)
    assert _route(monkeypatch, target) == [("semo", target)]
