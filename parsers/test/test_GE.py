import json
from datetime import datetime, timezone
from importlib import resources

import pytest
import requests
from freezegun import freeze_time
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.GE import fetch_exchange, fetch_production


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, Adapter]:
    adapter = Adapter()
    session = requests.Session()
    session.mount("https://", adapter)
    return session, adapter


@freeze_time("2024-04-09 17:57:00")
def test_fetch_production_live(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    mock_asset = str(
        resources.files("parsers.test.mocks.GE").joinpath("production_live.xls")
    )
    with open(mock_asset, mode="rb") as f:
        content = f.read()

    adapter.register_uri(GET, ANY, content=content)

    assert snapshot == fetch_production(session=session)


def test_fetch_production_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    mock_asset = str(
        resources.files("parsers.test.mocks.GE").joinpath("production_20200101.xls")
    )
    with open(mock_asset, mode="rb") as f:
        content = f.read()

    adapter.register_uri(GET, ANY, content=content)

    historical_datetime = datetime(2020, 1, 1, tzinfo=timezone.utc)

    assert snapshot == fetch_production(
        target_datetime=historical_datetime, session=session
    )


@pytest.mark.parametrize("neighbour", ["AM", "AZ", "RU-1", "TR"])
@freeze_time("2024-04-08 12:00:00")
def test_fetch_exchange_live(snapshot, fixture_session_mock, neighbour):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.GE")
            .joinpath("exchange_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_exchange(
        ZoneKey("GE"), ZoneKey(neighbour), session=session
    )
