from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.BORNHOLM_POWERLAB import (
    LATEST_DATA_URL,
    fetch_exchange,
    fetch_production,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    realtime = (
        resources.files("electricitymap.contrib.parsers.tests.mocks.Bornholm_Powerlab")
        .joinpath("latest_data.json")
        .read_text()
    )
    adapter.register_uri(GET, LATEST_DATA_URL, json=loads(realtime))


def test_fetch_production(session, snapshot):
    assert snapshot == fetch_production(zone_key=ZoneKey("DK-BHM"), session=session)


def test_fetch_exchange(session, snapshot):
    assert snapshot == fetch_exchange(session=session)
