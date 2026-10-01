import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import POST
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import TR
from electricitymap.contrib.types import DayAheadAuction, ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/TR")


@pytest.fixture(autouse=True)
def tr_credentials_env():
    os.environ["TR_USERNAME"] = "test_username"
    os.environ["TR_PASSWORD"] = "test_password"


@pytest.mark.parametrize(
    "target_datetime",
    [
        None,
        datetime(2025, 7, 28, 10, 0),
    ],
)
def test_fetch_production(requests_mock, session, snapshot, target_datetime):
    # Mock the TGT ticket fetch - return a simple ticket string without newlines
    requests_mock.register_uri(
        POST,
        "https://giris.epias.com.tr/cas/v1/tickets",
        text="TGT-1234567890-abcdefghijklmnop-cas",
    )

    # Load mock production data from raw API response
    raw_response = json.loads(
        (base_path_to_mock / "raw_production_response.json").read_text()
    )

    # Mock the production data API response with empty items to end pagination
    requests_mock.register_uri(
        POST,
        "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/realtime-generation",
        [
            {"json": raw_response},
            {"json": {"items": []}},  # Empty response to end pagination
        ],
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == TR.fetch_production(ZoneKey("TR"), session, target_datetime=target_datetime)


MCP_URL = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"


def _register_mcp(requests_mock):
    requests_mock.register_uri(
        POST,
        "https://giris.epias.com.tr/cas/v1/tickets",
        text="TGT-1234567890-abcdefghijklmnop-cas",
    )
    requests_mock.register_uri(
        POST,
        MCP_URL,
        [
            {"json": json.loads((base_path_to_mock / "mcp_response.json").read_text())},
            {"json": {"items": []}},  # Empty response to end pagination
        ],
    )


def _mcp_request_window(requests_mock) -> tuple[str, str]:
    body = next(
        request.json()
        for request in requests_mock.request_history
        if request.url == MCP_URL
    )
    return body["startDate"], body["endDate"]


def test_fetch_price_day_ahead(requests_mock, session, snapshot):
    _register_mcp(requests_mock)

    rows = TR.fetch_price_day_ahead(
        ZoneKey("TR"),
        session,
        target_datetime=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == rows
    assert len(rows) == 48
    # 2026-10-01T00:00:00+03:00 is emitted as 2026-09-30T21:00Z.
    assert rows[24]["datetime"] == datetime(2026, 9, 30, 21, tzinfo=timezone.utc)
    for row in rows:
        assert row["end_datetime"] - row["datetime"] == timedelta(hours=1)
        assert row["datetime"].utcoffset() == timedelta(0)
        assert row["end_datetime"].utcoffset() == timedelta(0)
        assert row["auction"] == DayAheadAuction.EPIAS_DA
        assert row["currency"] == "TRY"
        assert row["publishedAt"] is None


@freeze_time("2026-10-01 09:00:00")
def test_fetch_price_day_ahead_live_requests_tomorrow(requests_mock, session):
    _register_mcp(requests_mock)

    TR.fetch_price_day_ahead(ZoneKey("TR"), session)

    assert _mcp_request_window(requests_mock) == (
        "2026-10-01T12:00:00+03:00",
        "2026-10-02T12:00:00+03:00",
    )


@pytest.mark.parametrize(
    "target_datetime",
    [
        datetime(2026, 9, 30, 22, 30, tzinfo=timezone.utc),
        datetime(2026, 9, 30, 22, 30),  # Naive targets are UTC.
    ],
)
def test_fetch_price_day_ahead_converts_target_to_tr_time(
    requests_mock, session, target_datetime
):
    """22:30 UTC is already 2026-10-01 in Turkey, so the window ends on that day."""
    _register_mcp(requests_mock)

    TR.fetch_price_day_ahead(ZoneKey("TR"), session, target_datetime=target_datetime)

    assert _mcp_request_window(requests_mock) == (
        "2026-09-30T01:30:00+03:00",
        "2026-10-01T01:30:00+03:00",
    )
