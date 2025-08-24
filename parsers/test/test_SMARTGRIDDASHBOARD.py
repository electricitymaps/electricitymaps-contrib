import json
from importlib import resources

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.SMARTGRIDDASHBOARD import (
    URL,
    fetch_consumption,
    fetch_consumption_forecast,
    fetch_exchange,
    fetch_production,
    fetch_total_generation,
    fetch_wind_solar_forecasts,
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
    assert snapshot == fetch_consumption(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
    )


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
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("IE"),
        session=session,
    )


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
    assert snapshot == fetch_exchange(
        zone_key1=ZoneKey("GB"),
        zone_key2=ZoneKey("GB-NIR"),
        session=session,
    )


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

    assert snapshot == fetch_total_generation(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
    )


def test_fetch_wind_solar_forecasts(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        f"{URL}?areas=windforecast",
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("windForecast.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        f"{URL}?areas=solarforecast",
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("solarForecast.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("IE"),
        session=session,
    )


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        f"{URL}?areas=solaractual",
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("solarProduction.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        f"{URL}?areas=windactual",
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("windProduction.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        f"{URL}?areas=generationactual",
        json=json.loads(
            resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
            .joinpath("generation.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("IE"),
        session=session,
    )
