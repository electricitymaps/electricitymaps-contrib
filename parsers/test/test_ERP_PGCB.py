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

    assert snapshot == fetch_consumption(zone_key=ZoneKey("BD"), session=session)


def test_exchanges(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.ERP_PGCB")
        .joinpath("latest.html")
        .read_text(),
    )

    assert snapshot == fetch_exchange(
        zone_key1=ZoneKey("BD"),
        zone_key2=ZoneKey("IN-NE"),
        session=session,
    )


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.ERP_PGCB")
        .joinpath("latest.html")
        .read_text(),
    )
    assert snapshot == fetch_production(
        zone_key=ZoneKey("BD"),
        session=session,
    )
