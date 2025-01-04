from datetime import datetime, timezone

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CY import HISTORICAL_SOURCE, REALTIME_SOURCE, fetch_production


@pytest.fixture(autouse=True)
def target_datetime():
    yield datetime(2024, 3, 18, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def mock_response(adapter):
    with open(
        "parsers/test/mocks/CY/response_historical_20240318.html", "rb"
    ) as response:
        adapter.register_uri(
            GET, HISTORICAL_SOURCE.format("18-03-2024"), content=response.read()
        )
    with open(
        "parsers/test/mocks/CY/response_realtime_20240401.html", "rb"
    ) as response:
        adapter.register_uri(GET, REALTIME_SOURCE, content=response.read())


def test_snapshot_historical_source(session, target_datetime, snapshot):
    production = fetch_production(
        zone_key=ZoneKey("CY"),
        session=session,
        target_datetime=target_datetime,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "capacity": element["capacity"],
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
        }
        for element in production
    ]


def test_snapshot_realtime_source(session, snapshot):
    production = fetch_production(ZoneKey("CY"), session=session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "capacity": element["capacity"],
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
        }
        for element in production
    ]
