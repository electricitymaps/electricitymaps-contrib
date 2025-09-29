#!/usr/bin/env python3

"""Tests for US_MISO.py"""

import json
import logging
import re
from datetime import datetime
from json import loads
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from requests_mock import GET
from testfixtures import LogCapture

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers import US_MISO

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/US_MISO")


def test_fetch_production():
    filename = "electricitymap/contrib/parsers/tests/mocks/MISO.html"
    with open(filename) as f:
        mock_data = json.load(f)
    with (
        LogCapture(),
        patch("electricitymap.contrib.parsers.US_MISO.get_json_data") as gjd,
    ):
        gjd.return_value = mock_data
        production = US_MISO.fetch_production(logger=logging.getLogger("test"))

    assert production
    assert production[0]["production"]["coal"] == 40384.0
    assert production[0]["datetime"] == datetime(
        2018, 1, 25, 4, 30, tzinfo=ZoneInfo("America/New_York")
    )
    assert production[0]["source"] == "misoenergy.org"
    assert production[0]["zoneKey"] == "US-MIDW-MISO"
    assert isinstance(production[0]["storage"], dict)

    # Make sure the unmapped Antimatter type is set to 'unknown'.
    assert production[0]["production"]["unknown"] >= 256


def test_snapshot_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock wind forecast request
    data_wind = Path(base_path_to_mock, "DataBrokerServicesgetWindForecast.asmx.json")
    adapter.register_uri(
        GET,
        "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=json",
        json=loads(data_wind.read_text()),
    )

    # Mock solar forecast request
    data_solar = Path(base_path_to_mock, "DataBrokerServicesgetSolarForecast.asmx.json")
    adapter.register_uri(
        GET,
        "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=json",
        json=loads(data_solar.read_text()),
    )

    # Run function under test
    assert snapshot == US_MISO.fetch_wind_solar_forecasts(
        zone_key=ZoneKey("US-MIDW-MISO"),
        session=session,
    )


def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot):
    # Mock load forecast request
    data = Path(base_path_to_mock, "20250310_df_al.xls")
    adapter.register_uri(
        GET,
        re.compile(r"https://docs\.misoenergy\.org/marketreports/\d+_df_al.xls"),
        content=data.read_bytes(),
    )

    # Run function under test
    assert snapshot == US_MISO.fetch_consumption_forecast(
        zone_key=ZoneKey("US-MIDW-MISO"),
        session=session,
    )
