from json import loads

import pytest
from pkg_resources import resource_string
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.BORNHOLM_POWERLAB import LATEST_DATA_URL, fetch_exchange, fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    realtime = resource_string(
        "parsers.test.mocks.Bornholm_Powerlab", "latest_data.json"
    )
    adapter.register_uri(
        GET,
        LATEST_DATA_URL,
        json=loads(realtime.decode("utf-8")),
    )


def test_fetch_production(session, snapshot):
    production = fetch_production(zone_key=ZoneKey("DK-BHM"), session=session)

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


def test_fetch_exchange(session, snapshot):
    exchange = fetch_exchange(session=session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "netFlow": element["netFlow"],
            "source": element["source"],
            "sortedZoneKeys": element["sortedZoneKeys"],
            "sourceType": element["sourceType"].value,
        }
        for element in exchange
    ]
