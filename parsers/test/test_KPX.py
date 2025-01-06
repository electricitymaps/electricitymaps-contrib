from datetime import datetime, timezone

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.lib.types import ZoneKey
from parsers.KPX import (
    HISTORICAL_PRODUCTION_URL,
    REAL_TIME_URL,
    fetch_consumption,
    fetch_production,
)


@pytest.fixture()
def mock_response_as_realtime(adapter):
    with open("parsers/test/mocks/KPX/realtime.html", "rb") as mock:
        adapter.register_uri(GET, REAL_TIME_URL, content=mock.read())


@pytest.fixture()
def mock_response_as_historical(adapter):
    with open("parsers/test/mocks/KPX/historical.html", "rb") as mock:
        adapter.register_uri(POST, HISTORICAL_PRODUCTION_URL, content=mock.read())
        adapter.register_uri(GET, HISTORICAL_PRODUCTION_URL, content=None)


def test_fetch_consumption_realtime(session, snapshot, mock_response_as_realtime):
    assert snapshot == fetch_consumption(ZoneKey("KR"), session)


def test_fetch_production_realtime(session, snapshot, mock_response_as_realtime):
    assert snapshot == fetch_production(ZoneKey("KR"), session)


def test_production_historical(session, snapshot, mock_response_as_historical):
    dt = datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert snapshot == fetch_production(ZoneKey("KR"), session, dt)
