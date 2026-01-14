from importlib import resources
from json import loads

import pytest
from freezegun import freeze_time
from requests_mock import GET

from electricitymap.contrib.parsers.ENTE import (
    DATA_URL,
    fetch_exchange,
    fetch_production,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        DATA_URL,
        json=loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.ENTE")
            .joinpath("response_generic_20240403.json")
            .read_text()
        ),
    )


@freeze_time("2024-04-03 14:37:59.999999")
def test_fetch_exchange(session, snapshot):
    assert snapshot == fetch_exchange(
        zone_key1=ZoneKey("CR"),
        zone_key2=ZoneKey("NI"),
        session=session,
    )


def test_fetch_exchange_raises_exception_on_exchange_not_implemented(session):
    with pytest.raises(NotImplementedError):
        fetch_exchange(
            zone_key1=ZoneKey("FR"),
            zone_key2=ZoneKey("GB"),
            session=session,
        )


@freeze_time("2024-04-03 14:00:59.123456")
def test_fetch_production(session, snapshot):
    assert snapshot == fetch_production(
        zone_key=ZoneKey("HN"),
        session=session,
    )
