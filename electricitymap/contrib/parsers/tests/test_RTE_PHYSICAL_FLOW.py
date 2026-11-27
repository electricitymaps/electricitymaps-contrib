import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import GET, POST
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.parsers import RTE_PHYSICAL_FLOW
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.RTE_PHYSICAL_FLOW import (
    BORDER_EICS,
    PHYSICAL_FLOW_URL,
    TOKEN_URL,
    fetch_exchange,
)

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/RTE_PHYSICAL_FLOW")

# Real captures of the API for the Paris day of 2026-11-11, trimmed to 07:30-08:15 and
# 10:15-10:45 Paris time. RTE published nothing in between, on every border.
TARGET_DATETIME = datetime(2026, 11, 11, 12, tzinfo=UTC)
GAP_START = datetime(2026, 11, 11, 7, 30, tzinfo=UTC)
GAP_END = datetime(2026, 11, 11, 9, 15, tzinfo=UTC)

BORDERS = [
    ("BE", "FR", "BE"),
    ("ES", "FR", "ES"),
    ("FR", "IT-NO", "IT-NO"),
]


@pytest.fixture(autouse=True)
def rte_credentials(monkeypatch):
    monkeypatch.setenv("RTE_PHYSICAL_FLOW_CLIENT_ID", "dummy-id")
    monkeypatch.setenv("RTE_PHYSICAL_FLOW_CLIENT_SECRET", "dummy-secret")


@pytest.fixture(autouse=True)
def fresh_token_cache():
    RTE_PHYSICAL_FLOW._token_cache.clear()
    yield
    RTE_PHYSICAL_FLOW._token_cache.clear()


def _capture(name: str) -> dict:
    return json.loads((BASE_MOCK_PATH / f"{name}.json").read_text())


def _mock_api(requests_mock) -> None:
    captures = {BORDER_EICS[name]: _capture(name) for name in ("BE", "ES", "IT-NO")}
    requests_mock.register_uri(
        POST, TOKEN_URL, json={"access_token": "dummy-token", "expires_in": 3600}
    )
    requests_mock.register_uri(
        GET,
        PHYSICAL_FLOW_URL,
        json=lambda request, _context: captures[
            request.qs["country_eic_code"][0].upper()
        ],
    )


def _raw_values(name: str) -> dict[str, dict[datetime, int]]:
    """The API's value per sender EIC and interval start (UTC), straight from the file."""
    raw: dict[str, dict[datetime, int]] = {}
    for flow in _capture(name)["physical_flows"]:
        raw[flow["sender_country_eic_code"]] = {
            datetime.fromisoformat(v["start_date"]).astimezone(UTC): v["value"]
            for v in flow["values"]
        }
    return raw


def test_fetch_exchange_publishes_every_quarter_hour_as_rte_gives_it(
    requests_mock, session, snapshot
):
    """Three borders, in both directions. The points are RTE's raw values, one per
    15 minutes, and the hole RTE leaves is not filled."""
    _mock_api(requests_mock)

    results = {}
    for zone_key1, zone_key2, other in BORDERS:
        result = fetch_exchange(
            ZoneKey(zone_key1),
            ZoneKey(zone_key2),
            session=session,
            target_datetime=TARGET_DATETIME,
        )
        results[f"{zone_key1}->{zone_key2}"] = result

        # Net flow is first zone sending minus second zone sending: the raw values,
        # untouched, with no averaging, rounding or interpolation.
        sent = _raw_values(other)
        sender_eic = {"FR": "10YFR-RTE------C", other: BORDER_EICS[other]}
        raw_first, raw_second = (sent[sender_eic[z]] for z in (zone_key1, zone_key2))
        assert {e["datetime"]: e["netFlow"] for e in result} == {
            start: raw_first[start] - raw_second[start] for start in raw_first
        }

        datetimes = [e["datetime"] for e in result]
        assert len(datetimes) == len(set(raw_first)) == 7
        assert {e["source"] for e in result} == {"rte-france.com"}
        assert {e["sortedZoneKeys"] for e in result} == {f"{zone_key1}->{zone_key2}"}
        # Every step is 15 minutes, except across the hole, which stays empty.
        steps = {b - a for a, b in zip(datetimes, datetimes[1:], strict=False)}
        assert steps == {timedelta(minutes=15), GAP_END - datetimes[3]}
        assert not [d for d in datetimes if GAP_START <= d < GAP_END]
        # Each point lasts one 15-minute step, not the hour RTE's end_date claims,
        # including the one before the hole and the last one.
        assert all(
            e["end_datetime"] == e["datetime"] + timedelta(minutes=15) for e in result
        )

    # France exports to BE (negative BE->FR) and IT-NO, and imports from ES.
    assert results["BE->FR"][0]["netFlow"] == -2103
    assert results["ES->FR"][0]["netFlow"] == 546
    assert results["FR->IT-NO"][0]["netFlow"] == 3921

    # One token serves all three borders, and the window runs from the Paris midnight
    # a week before the target to the Paris midnight after it (the API only returns
    # whole days).
    assert [r.method for r in requests_mock.request_history].count("POST") == 1
    queries = [r.qs for r in requests_mock.request_history if r.method == "GET"]
    assert {q["start_date"][0] for q in queries} == {"2026-11-04t00:00:00+01:00"}
    assert {q["end_date"][0] for q in queries} == {"2026-11-12t00:00:00+01:00"}
    assert [q["country_eic_code"][0].upper() for q in queries] == [
        BORDER_EICS[other] for *_, other in BORDERS
    ]
    assert (
        requests_mock.request_history[1].headers["Authorization"]
        == "Bearer dummy-token"
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == results


def test_fetch_exchange_window_for_naive_target_and_live_fetch(
    requests_mock, session, monkeypatch
):
    """A naive target is UTC, whatever the machine's timezone: it asks for the same
    Paris days as the aware target. At UTC+14, reading it as local time would put
    the target on the previous Paris day. The live fetch, with no target, keeps a
    one-day lookback instead of the refetch's week."""
    _mock_api(requests_mock)

    try:
        with monkeypatch.context() as patched:
            patched.setenv("TZ", "Pacific/Kiritimati")
            time.tzset()
            fetch_exchange(
                ZoneKey("BE"),
                ZoneKey("FR"),
                session=session,
                target_datetime=TARGET_DATETIME.replace(tzinfo=None),
            )
    finally:
        time.tzset()

    with freeze_time(TARGET_DATETIME):
        fetch_exchange(ZoneKey("BE"), ZoneKey("FR"), session=session)

    refetch, live = [r.qs for r in requests_mock.request_history if r.method == "GET"]
    assert refetch["start_date"] == ["2026-11-04t00:00:00+01:00"]
    assert refetch["end_date"] == ["2026-11-12t00:00:00+01:00"]
    assert live["start_date"] == ["2026-11-10t00:00:00+01:00"]
    assert live["end_date"] == ["2026-11-12t00:00:00+01:00"]


def test_fetch_exchange_unsupported_border_raises(requests_mock, session):
    """FR->GB (Elexon), FR->LU, DE->FR (RTE's German series is off) and other pairs
    are not served by this parser: refuse them rather than return another border's flow."""
    _mock_api(requests_mock)

    for pair in [
        ("DE", "FR"),
        ("FR", "GB"),
        ("FR", "LU"),
        ("BE", "DE"),
        ("FR-COR", "IT-SAR"),
    ]:
        with pytest.raises(ParserException, match="not a supported border"):
            fetch_exchange(ZoneKey(pair[0]), ZoneKey(pair[1]), session=session)

    assert requests_mock.request_history == []


def test_fetch_exchange_api_error_surfaces_rte_body(requests_mock, session):
    """RTE explains a refusal in the body (here F04, an end_date too far ahead)."""
    requests_mock.register_uri(
        POST, TOKEN_URL, json={"access_token": "dummy-token", "expires_in": 3600}
    )
    requests_mock.register_uri(
        GET,
        PHYSICAL_FLOW_URL,
        status_code=400,
        json={
            "error": "PHYSIFLOW_PHFLO_F04",
            "error_description": "end_date incorrect",
        },
    )

    with pytest.raises(ParserException, match="PHYSIFLOW_PHFLO_F04") as error:
        fetch_exchange(ZoneKey("BE"), ZoneKey("FR"), session=session)

    assert "dummy-secret" not in str(error.value)
    assert "dummy-token" not in str(error.value)


def test_hourly_points_keep_their_hour_next_to_quarter_hour_data():
    """A window across the spring 2023 switch holds hourly then 15-minute data:
    each point lasts its own step, not the smallest one in the window."""
    values = [
        {"start_date": start, "end_date": end, "value": 100}
        for start, end in [
            ("2023-04-01T22:00:00+02:00", "2023-04-01T23:00:00+02:00"),
            ("2023-04-01T23:00:00+02:00", "2023-04-02T00:00:00+02:00"),
            ("2023-04-02T00:00:00+02:00", "2023-04-02T01:00:00+02:00"),
            ("2023-04-02T00:15:00+02:00", "2023-04-02T01:15:00+02:00"),
        ]
    ]
    result = RTE_PHYSICAL_FLOW._direction_exchanges(
        values, 1, ZoneKey("BE->FR"), RTE_PHYSICAL_FLOW.getLogger()
    ).to_list()

    assert [e["end_datetime"] - e["datetime"] for e in result] == [
        timedelta(hours=1),
        timedelta(hours=1),
        timedelta(minutes=15),
        timedelta(minutes=15),
    ]
