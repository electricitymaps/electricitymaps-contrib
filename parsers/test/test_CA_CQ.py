import json
from importlib import resources

from requests_mock import ANY, GET

from parsers.CA_QC import fetch_consumption, fetch_production


def test_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.Hydroquebec")
            .joinpath("production.json")
            .read_text()
        ),
    )

    production = fetch_production(session=session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "production": element["production"],
            "source": element["source"],
            "zoneKey": element["zoneKey"],
            "storage": element["storage"],
            "sourceType": element["sourceType"].value,
        }
        for element in production
    ]


def test_consumption(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.Hydroquebec")
            .joinpath("consumption.json")
            .read_text()
        ),
    )

    consumption = fetch_consumption(session=session)
    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "consumption": element["consumption"],
            "source": element["source"],
            "zoneKey": element["zoneKey"],
            "sourceType": element["sourceType"].value,
        }
        for element in consumption
    ]
