import json
import os
from importlib import resources

from requests_mock import ANY

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ESIOS


def test_fetch_exchange(adapter, session):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks")
            .joinpath("ESIOS_ES_MA.json")
            .read_text()
        ),
    )
    os.environ["ESIOS_TOKEN"] = "token"
    data_list = ESIOS.fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), session)
    assert data_list is not None
    for data in data_list:
        assert data["sortedZoneKeys"] == "ES->MA"
        assert data["source"] == "api.esios.ree.es"
        assert data["datetime"] is not None
        assert data["netFlow"] is not None


def test_exchange_with_snapshot(session, adapter, snapshot):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks")
            .joinpath("ESIOS_ES_MA.json")
            .read_text()
        ),
    )
    os.environ["ESIOS_TOKEN"] = "token"
    exchange = ESIOS.fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), session)

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
