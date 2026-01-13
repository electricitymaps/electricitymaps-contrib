from datetime import datetime, timezone

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.CY import (
    HISTORICAL_SOURCE,
    REALTIME_SOURCE,
    fetch_production,
)
from electricitymap.types import ZoneKey


@pytest.fixture(autouse=True)
def target_datetime():
    yield datetime(2024, 3, 18, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def mock_response(adapter):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CY/response_historical_20240318.html",
        "rb",
    ) as response:
        adapter.register_uri(
            GET, HISTORICAL_SOURCE.format("18-03-2024"), content=response.read()
        )
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CY/response_realtime_20240401.html",
        "rb",
    ) as response:
        adapter.register_uri(GET, REALTIME_SOURCE, content=response.read())


def test_snapshot_historical_source(session, target_datetime, snapshot):
    assert snapshot == fetch_production(
        zone_key=ZoneKey("CY"),
        session=session,
        target_datetime=target_datetime,
    )


def test_snapshot_realtime_source(session, snapshot):
    assert snapshot == fetch_production(ZoneKey("CY"), session=session)
