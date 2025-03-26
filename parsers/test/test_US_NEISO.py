import re
from pathlib import Path

from requests_mock import GET, POST

from electricitymap.contrib.lib.types import ZoneKey
from parsers.US_NEISO import fetch_consumption_forecast, fetch_wind_solar_forecasts

base_path_to_mock = Path("parsers/test/mocks/US_NEISO")


def test_fetch_consumption_forecast(adapter, session, snapshot):
    # Mock url request
    data = Path(base_path_to_mock, "day_ahead_load_forecast_20250317.xml")
    adapter.register_uri(
        POST,
        "https://www.iso-ne.com/ws/wsclient",
        text=data.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("US-NE-ISNE"),
        session=session,
    )


def test_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock the initial page requests that set cookies
    adapter.register_uri(
        GET,
        "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seven-day-solar-power-forecast",
        text="mock response",
    )

    adapter.register_uri(
        GET,
        "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seven-day-wind-power-forecast",
        text="mock response",
    )

    # Mock wind forecast request
    data_wind = Path(base_path_to_mock, "seven_day_wind_power_forecast_20250225.csv")
    adapter.register_uri(
        GET,
        re.compile(r"https://www\.iso-ne\.com/transform/csv/wphf\?start=\d+"),
        text=data_wind.read_text(),
    )

    # Mock solar forecast request
    data_solar = Path(base_path_to_mock, "seven_day_solar_power_forecast_20250225.csv")
    adapter.register_uri(
        GET,
        re.compile(r"https://www\.iso-ne\.com/transform/csv/sphf\?start=\d+"),
        text=data_solar.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("US-NE-ISNE"),
        session=session,
    )
