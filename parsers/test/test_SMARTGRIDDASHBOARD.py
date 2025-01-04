import json
from importlib import resources

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.SMARTGRIDDASHBOARD import (
    URL,
    fetch_consumption,
    fetch_consumption_forecast,
    fetch_exchange,
    fetch_total_generation,
    fetch_wind_forecasts,
)


def test_fetch_consumption(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        URL,
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("consumption.json")
            .read_text()
        ),
    )
    consumption = fetch_consumption(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "consumption": element["consumption"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "zoneKey": element["zoneKey"],
        }
        for element in consumption
    ]


def test_fetch_consumption_forecast(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        URL,
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("consumptionForecast.json")
            .read_text()
        ),
    )
    consumption = fetch_consumption_forecast(
        zone_key=ZoneKey("IE"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "consumption": element["consumption"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "zoneKey": element["zoneKey"],
        }
        for element in consumption
    ]


def test_fetch_exchange(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        URL,
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("exchange.json")
            .read_text()
        ),
    )
    exchange = fetch_exchange(
        zone_key1=ZoneKey("GB"),
        zone_key2=ZoneKey("GB-NIR"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "netFlow": element["netFlow"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "sortedZoneKeys": element["sortedZoneKeys"],
        }
        for element in exchange
    ]


def test_fetch_generation(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        URL,
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("generation.json")
            .read_text()
        ),
    )

    generation = fetch_total_generation(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "zoneKey": element["zoneKey"],
            "generation": element["generation"],
        }
        for element in generation
    ]


def test_fetch_wind_forecasts(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        URL,
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("windForecast.json")
            .read_text()
        ),
    )

    wind_forecasts = fetch_wind_forecasts(
        zone_key=ZoneKey("IE"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "zoneKey": element["zoneKey"],
            "production": element["production"],
            "storage": element["storage"],
        }
        for element in wind_forecasts
    ]
