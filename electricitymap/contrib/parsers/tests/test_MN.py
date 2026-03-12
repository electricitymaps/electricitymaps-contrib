import json
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.parsers.MN import fetch_consumption, fetch_production
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MN")
            .joinpath("response.json")
            .read_text()
        ),
    )


def test_production(session, snapshot):
    assert snapshot == fetch_production(ZoneKey("MN"), session=session)


def test_consumption(session, snapshot):
    assert snapshot == fetch_consumption(ZoneKey("MN"), session=session)
