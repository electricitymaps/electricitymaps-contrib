from importlib import resources

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ESTADISTICO_UT import DAILY_OPERATION_URL, fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("get.html")
        .read_text(),
    )
    adapter.register_uri(
        POST,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("post.html")
        .read_text(),
    )


def test_fetch_production(session, snapshot):
    production = fetch_production(
        zone_key=ZoneKey("SV"),
        session=session,
    )

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
