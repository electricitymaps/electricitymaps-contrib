import json
from datetime import datetime, timezone
from importlib import resources

import pytest
import requests
from freezegun import freeze_time
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.MD import (
    fetch_consumption,
    fetch_exchange,
    fetch_exchange_forecast,
    fetch_price,
    fetch_production,
)

# the datetime corresponding to our mock live API response
frozen_live_time = freeze_time("2024-04-11 06:32:00")

# the target datetime corresponding to our mock historical API response
historical_datetime = datetime(2021, 7, 25, 12, tzinfo=timezone.utc)


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, Adapter]:
    adapter = Adapter()
    session = requests.Session()
    session.mount("https://", adapter)
    return session, adapter


@frozen_live_time
def test_fetch_consumption_live(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    consumption = fetch_consumption(session=session)

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "consumption": element["consumption"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in consumption
        ]
    )


def test_fetch_consumption_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    consumption = fetch_consumption(
        target_datetime=historical_datetime, session=session
    )

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "consumption": element["consumption"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in consumption
        ]
    )


@pytest.mark.parametrize("neighbour", ["RO", "UA"])
@frozen_live_time
def test_fetch_exchange_live(snapshot, fixture_session_mock, neighbour):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    exchanges = fetch_exchange(ZoneKey("MD"), ZoneKey(neighbour), session=session)

    snapshot.assert_match(
        [
            {
                "datetime": exchange["datetime"].isoformat(),
                "sortedZoneKeys": exchange["sortedZoneKeys"],
                "netFlow": exchange["netFlow"],
                "source": exchange["source"],
                "sourceType": exchange["sourceType"].value,
            }
            for exchange in exchanges
        ]
    )


@pytest.mark.parametrize("neighbour", ["RO", "UA"])
def test_fetch_exchange_historical(snapshot, fixture_session_mock, neighbour):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    exchanges = fetch_exchange(
        ZoneKey("MD"),
        ZoneKey(neighbour),
        target_datetime=historical_datetime,
        session=session,
    )

    snapshot.assert_match(
        [
            {
                "datetime": exchange["datetime"].isoformat(),
                "sortedZoneKeys": exchange["sortedZoneKeys"],
                "netFlow": exchange["netFlow"],
                "source": exchange["source"],
                "sourceType": exchange["sourceType"].value,
            }
            for exchange in exchanges
        ]
    )


@pytest.mark.parametrize("neighbour", ["RO", "UA"])
@frozen_live_time
def test_fetch_exchange_forecast_live(snapshot, fixture_session_mock, neighbour):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    exchange_forecasts = fetch_exchange_forecast(
        ZoneKey("MD"), ZoneKey(neighbour), session=session
    )

    snapshot.assert_match(
        [
            {
                "datetime": exchange["datetime"].isoformat(),
                "sortedZoneKeys": exchange["sortedZoneKeys"],
                "netFlow": exchange["netFlow"],
                "source": exchange["source"],
                "sourceType": exchange["sourceType"].value,
            }
            for exchange in exchange_forecasts
        ]
    )


@pytest.mark.parametrize("neighbour", ["RO", "UA"])
def test_fetch_exchange_forecast_historical(snapshot, fixture_session_mock, neighbour):
    session, adapter = fixture_session_mock
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    exchange_forecasts = fetch_exchange_forecast(
        ZoneKey("MD"),
        ZoneKey(neighbour),
        target_datetime=historical_datetime,
        session=session,
    )

    snapshot.assert_match(
        [
            {
                "datetime": exchange["datetime"].isoformat(),
                "sortedZoneKeys": exchange["sortedZoneKeys"],
                "netFlow": exchange["netFlow"],
                "source": exchange["source"],
                "sourceType": exchange["sourceType"].value,
            }
            for exchange in exchange_forecasts
        ]
    )


@frozen_live_time
def test_fetch_price_live(snapshot):
    prices = fetch_price()

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "currency": element["currency"],
                "price": element["price"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in prices
        ]
    )


@pytest.mark.parametrize(
    "historical_datetime",
    [
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2000, 4, 1, tzinfo=timezone.utc),
        datetime(2001, 10, 1, tzinfo=timezone.utc),
        datetime(2002, 9, 1, tzinfo=timezone.utc),
        datetime(2005, 9, 1, tzinfo=timezone.utc),
        datetime(2007, 8, 3, tzinfo=timezone.utc),
        datetime(2010, 1, 19, tzinfo=timezone.utc),
        datetime(2012, 5, 11, tzinfo=timezone.utc),
        datetime(2015, 7, 31, tzinfo=timezone.utc),
        datetime(2023, 12, 31, tzinfo=timezone.utc),
        datetime(2024, 3, 21, tzinfo=timezone.utc),
    ],
)
def test_fetch_price_historical(snapshot, historical_datetime):
    prices = fetch_price(target_datetime=historical_datetime)

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "currency": element["currency"],
                "price": element["price"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in prices
        ]
    )


@frozen_live_time
def test_fetch_production_live(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    production = fetch_production(session=session)

    snapshot.assert_match(
        [
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
    )


def test_fetch_production_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    production = fetch_production(target_datetime=historical_datetime, session=session)

    snapshot.assert_match(
        [
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
    )
