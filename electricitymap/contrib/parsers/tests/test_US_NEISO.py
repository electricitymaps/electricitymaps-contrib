import re
from pathlib import Path

import pytest
from requests_mock import ANY, GET, POST

from electricitymap.contrib.parsers.US_NEISO import (
    fetch_consumption_forecast,
    fetch_exchange,
    fetch_wind_solar_forecasts,
)
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/US_NEISO")


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


@pytest.mark.parametrize(
    ("zone_key1, zone_key2"),
    [
        (ZoneKey("CA-NB"), ZoneKey("US-NE-ISNE")),
        (ZoneKey("CA-QC"), ZoneKey("US-NE-ISNE")),
        (ZoneKey("US-NE-ISNE"), ZoneKey("US-NY-NYIS")),
    ],
)
def test_fetch_exchange(adapter, session, snapshot, zone_key1, zone_key2):
    data = Path(base_path_to_mock, f"exchange_{zone_key1}_{zone_key2}.json")
    adapter.register_uri(
        POST,
        ANY,
        text=data.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_exchange(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
    )
