from datetime import datetime
from importlib import resources
from zoneinfo import ZoneInfo

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.IEX import (
    DAM_PROVISIONAL_URL,
    TZ,
    _block_bounds,
    _parse_dam_html,
    _parse_delivery_date,
    fetch_price,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

FIXTURE = (
    resources.files("electricitymap.contrib.parsers.tests.mocks.IEX")
    .joinpath("dam_provisional.html")
    .read_text(encoding="utf-8")
)


@pytest.fixture
def mock_dam_page(requests_mock):
    requests_mock.register_uri(GET, DAM_PROVISIONAL_URL, text=FIXTURE)


# --- helpers ---------------------------------------------------------------


def test_parse_delivery_date():
    assert (
        _parse_delivery_date("Unconstrained DAM Data for 23-07-2026")
        == datetime(2026, 7, 23, tzinfo=TZ).date()
    )


def test_block_bounds_midnight_rollover():
    delivery = datetime(2026, 7, 23, tzinfo=TZ).date()
    start, end = _block_bounds(delivery, "23:45 - 24:00")
    assert start == datetime(2026, 7, 23, 23, 45, tzinfo=TZ)
    assert end == datetime(2026, 7, 24, 0, 0, tzinfo=TZ)


def test_block_bounds_first_block():
    delivery = datetime(2026, 7, 23, tzinfo=TZ).date()
    start, end = _block_bounds(delivery, "00:00 - 00:15")
    assert start == datetime(2026, 7, 23, 0, 0, tzinfo=TZ)
    assert end == datetime(2026, 7, 23, 0, 15, tzinfo=TZ)


def test_parse_dam_html_yields_96_blocks():
    delivery_date, rows = _parse_dam_html(
        FIXTURE, logger=__import__("logging").getLogger()
    )
    assert delivery_date == datetime(2026, 7, 23, tzinfo=TZ).date()
    assert len(rows) == 96
    assert rows[0][0] == datetime(2026, 7, 23, 0, 0, tzinfo=TZ)
    assert rows[0][2] == 10000.0
    assert rows[-1][0] == datetime(2026, 7, 23, 23, 45, tzinfo=TZ)
    assert rows[-1][2] == 10000.0


# --- fetch_price -----------------------------------------------------------


def test_snapshot_fetch_price(session, snapshot, mock_dam_page):
    assert snapshot == fetch_price(zone_key=ZoneKey("IN"), session=session)


def test_fetch_price_datetimes_are_kolkata(session, mock_dam_page):
    events = fetch_price(zone_key=ZoneKey("IN"), session=session)
    assert len(events) == 96
    first = events[0]
    assert first["datetime"].tzinfo == TZ
    assert first["currency"] == "INR"
    assert first["source"] == "iexindia.com"
    assert first["zoneKey"] == "IN"
    assert first["price"] == 10000.0
    # 15-minute MTU
    assert first["end_datetime"] - first["datetime"] == __import__(
        "datetime"
    ).timedelta(minutes=15)


def test_fetch_price_accepts_matching_target_datetime(session, mock_dam_page):
    target = datetime(2026, 7, 23, 12, 0, tzinfo=TZ)
    events = fetch_price(
        zone_key=ZoneKey("IN"), session=session, target_datetime=target
    )
    assert len(events) == 96


def test_fetch_price_rejects_mismatched_historical(session, mock_dam_page):
    target = datetime(2024, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC"))
    with pytest.raises(ParserException, match="Historical DAM prices"):
        fetch_price(zone_key=ZoneKey("IN"), session=session, target_datetime=target)


def test_fetch_price_rejects_naive_target_datetime(session, mock_dam_page):
    with pytest.raises(ParserException, match="timezone-aware"):
        fetch_price(
            zone_key=ZoneKey("IN"),
            session=session,
            target_datetime=datetime(2026, 7, 23, 12, 0),
        )


def test_fetch_price_http_error(session, requests_mock):
    requests_mock.register_uri(GET, DAM_PROVISIONAL_URL, status_code=503)
    with pytest.raises(ParserException, match="HTTP 503"):
        fetch_price(zone_key=ZoneKey("IN"), session=session)
