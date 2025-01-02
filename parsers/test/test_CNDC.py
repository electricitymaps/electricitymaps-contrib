import json
from datetime import datetime
from importlib import resources

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CNDC import (
    DATA_URL,
    INDEX_URL,
    fetch_generation_forecast,
    fetch_production,
    tz_bo,
)


@pytest.fixture(autouse=True)
def target_datetime():
    yield datetime(2023, 12, 20, tzinfo=tz_bo)


@pytest.fixture(autouse=True)
def mock_response(adapter, target_datetime):
    adapter.register_uri(
        GET,
        INDEX_URL,
        text=resources.files("parsers.test.mocks.CNDC")
        .joinpath("index.html")
        .read_text(),
    )

    adapter.register_uri(
        GET,
        DATA_URL.format(target_datetime.strftime("%Y-%m-%d")),
        json=json.loads(
            resources.files("parsers.test.mocks.CNDC").joinpath("data.json").read_text()
        ),
    )


def test_fetch_generation_forecast(session, snapshot, target_datetime):
    generation_forecast = fetch_generation_forecast(
        ZoneKey("BO"),
        session=session,
        target_datetime=target_datetime,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "generation": element["generation"],
            "zoneKey": element["zoneKey"],
            "source": element["source"],
        }
        for element in generation_forecast
    ]


def test_fetch_production(session, snapshot, target_datetime):
    production = fetch_production(
        ZoneKey("BO"),
        session=session,
        target_datetime=target_datetime,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "zoneKey": element["zoneKey"],
        }
        for element in production
    ]
