import json
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CAMMESA import (
    CAMMESA_DEMANDA_ENDPOINT,
    CAMMESA_RENEWABLES_ENDPOINT,
    fetch_exchange,
    fetch_production,
)


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.Cammesa")
            .joinpath("exchanges.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        CAMMESA_DEMANDA_ENDPOINT,
        json=json.loads(
            resources.files("parsers.test.mocks.Cammesa")
            .joinpath("conventional_production.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        CAMMESA_RENEWABLES_ENDPOINT,
        json=json.loads(
            resources.files("parsers.test.mocks.Cammesa")
            .joinpath("renewable_production.json")
            .read_text()
        ),
    )


def test_exchanges_AR_CL_SEN(session, snapshot):
    exchange = fetch_exchange(ZoneKey("AR"), ZoneKey("CL-SEN"), session=session)

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


def test_exchanges_AR_BAS_AR_COM(session, snapshot):
    exchange = fetch_exchange(ZoneKey("AR-BAS"), ZoneKey("AR-COM"), session=session)

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


def test_fetch_production(session, snapshot):
    production = fetch_production(ZoneKey("AR"), session=session)

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
