import json
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CEB import fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.CEB")
            .joinpath("response.text")
            .read_text()
        ),
    )


def test_production(session, snapshot):
    assert snapshot == fetch_production(ZoneKey("LK"), session=session)
