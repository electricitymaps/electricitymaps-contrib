from datetime import datetime, timezone
from importlib import resources

import pytest
import requests
from freezegun import freeze_time
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.GB import fetch_price


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, Adapter]:
    adapter = Adapter()
    session = requests.Session()
    session.mount("http://", adapter)
    return session, adapter


@pytest.mark.parametrize(
    "zone_key", ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]
)
@freeze_time("2024-04-14 15:10:57")
def test_fetch_price_live(snapshot, fixture_session_mock, zone_key):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.GB")
        .joinpath("eco2mix_api_live.xml")
        .read_text(),
    )

    prices = fetch_price(zone_key=ZoneKey(zone_key), session=session)

    snapshot.assert_match(
        [
            {
                "datetime": price["datetime"].isoformat(),
                "zoneKey": price["zoneKey"],
                "currency": price["currency"],
                "price": price["price"],
                "source": price["source"],
                "sourceType": price["sourceType"].value,
            }
            for price in prices
        ]
    )


def test_fetch_price_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.GB")
        .joinpath("eco2mix_api_historical_20220716.xml")
        .read_text(),
    )

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    prices = fetch_price(target_datetime=historical_datetime, session=session)

    snapshot.assert_match(
        [
            {
                "datetime": price["datetime"].isoformat(),
                "zoneKey": price["zoneKey"],
                "currency": price["currency"],
                "price": price["price"],
                "source": price["source"],
                "sourceType": price["sourceType"].value,
            }
            for price in prices
        ]
    )
