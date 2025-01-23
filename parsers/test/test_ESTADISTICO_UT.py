from datetime import datetime
from importlib import resources

from requests_mock import GET, POST

from parsers.ESTADISTICO_UT import DAILY_OPERATION_URL, ZONE_INFO, fetch_production


def test_fetch_production_live(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("get_live.html")
        .read_text(),
    )
    adapter.register_uri(
        POST,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("post_live.html")
        .read_text(),
    )
    assert snapshot == fetch_production(session=session)


def test_fetch_production_historical(adapter, session, snapshot):
    dt = datetime.fromisoformat("2025-01-01").replace(tzinfo=ZONE_INFO)

    adapter.register_uri(
        GET,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("get_historical.html")
        .read_text(),
    )
    adapter.register_uri(
        POST,
        DAILY_OPERATION_URL,
        text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
        .joinpath("post_historical.html")
        .read_text(),
    )

    assert snapshot == fetch_production(session=session, target_datetime=dt)
