from importlib import resources

from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ERP_PGCB import fetch_consumption, fetch_exchange, fetch_production


def test_fetch_consumption(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.ERP_PGCB")
        .joinpath("latest.html")
        .read_text(),
    )

    consumption = fetch_consumption(zone_key=ZoneKey("BD"), session=session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "consumption": element["consumption"],
            "source": element["source"],
        }
        for element in consumption
    ]


def test_exchanges(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.ERP_PGCB")
        .joinpath("latest.html")
        .read_text(),
    )

    exchange = fetch_exchange(
        zone_key1=ZoneKey("BD"),
        zone_key2=ZoneKey("IN-NE"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "netFlow": element["netFlow"],
            "source": element["source"],
            "sortedZoneKeys": element["sortedZoneKeys"],
        }
        for element in exchange
    ]


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.ERP_PGCB")
        .joinpath("latest.html")
        .read_text(),
    )
    production = fetch_production(
        zone_key=ZoneKey("BD"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "correctedModes": element["correctedModes"],
        }
        for element in production
    ]
