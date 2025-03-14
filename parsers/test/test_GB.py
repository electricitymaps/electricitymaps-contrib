from datetime import datetime, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.GB import fetch_price


@pytest.mark.parametrize(
    "zone_key", ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]
)
@freeze_time("2024-04-14 15:10:57")
def test_fetch_price_live(adapter, session, snapshot, zone_key):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.GB")
        .joinpath("eco2mix_api_live.xml")
        .read_text(),
    )

    assert snapshot == fetch_price(zone_key=ZoneKey(zone_key), session=session)


def test_fetch_price_historical(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks.GB")
        .joinpath("eco2mix_api_historical_20220716.xml")
        .read_text(),
    )

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    assert snapshot == fetch_price(target_datetime=historical_datetime, session=session)
