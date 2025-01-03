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
    production = fetch_production(ZoneKey("LK"), session=session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "zoneKey": element["zoneKey"],
            "sourceType": element["sourceType"].value,
        }
        for element in production
    ]
