import json
from datetime import datetime
from importlib import resources

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.CNDC import (
    DATA_URL,
    INDEX_URL,
    fetch_generation_forecast,
    fetch_production,
    tz_bo,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def target_datetime():
    yield datetime(2023, 12, 20, tzinfo=tz_bo)


@pytest.fixture(autouse=True)
def mock_response(adapter, target_datetime):
    adapter.register_uri(
        GET,
        INDEX_URL,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks.CNDC")
        .joinpath("index.html")
        .read_text(),
    )

    adapter.register_uri(
        GET,
        DATA_URL.format(target_datetime.strftime("%Y-%m-%d")),
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.CNDC")
            .joinpath("data.json")
            .read_text()
        ),
    )


def test_fetch_generation_forecast(session, snapshot, target_datetime):
    assert snapshot == fetch_generation_forecast(
        ZoneKey("BO"),
        session=session,
        target_datetime=target_datetime,
    )


def test_fetch_production(session, snapshot, target_datetime):
    assert snapshot == fetch_production(
        ZoneKey("BO"),
        session=session,
        target_datetime=target_datetime,
    )
