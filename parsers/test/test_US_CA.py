#!/usr/bin/env python3

"""Tests for US_CA.py"""

import zipfile
from logging import getLogger
from unittest.mock import patch

import pandas as pd

from electricitymap.contrib.lib.types import ZoneKey
from parsers import US_CA


def test_snapshot_fetch_wind_solar_forecasts(snapshot):
    def _mock_get_oasis_data(*args, **kwargs) -> pd.DataFrame:
        MOCK_ZIP_FILENAME = "parsers/test/mocks/US_CA/20250204_20250211_SLD_REN_FCST_DAM_20250214_04_52_10_v1.zip"

        # Read zip and extract the csv file
        with zipfile.ZipFile(MOCK_ZIP_FILENAME, "r") as z:
            csv_filename = z.namelist()[
                0
            ]  # Get the first file in the zip (there is only one file)
            with z.open(csv_filename) as f:  # Read the CSV file into a pandas DataFrame
                df = pd.read_csv(f)
        return df

    # Mock the call to _get_oasis_data with above (with patch)
    with patch("parsers.US_CA._get_oasis_data", _mock_get_oasis_data):
        parsed_wind_solar_forecasts = US_CA.fetch_wind_solar_forecasts(
            zone_key=ZoneKey("US-CAL-CISO"), logger=getLogger("test")
        )

    snapshot.assert_match(parsed_wind_solar_forecasts)


def test_snapshot_fetch_consumption_forecast(snapshot):
    def _mock_get_oasis_data(*args, **kwargs) -> pd.DataFrame:
        MOCK_ZIP_FILENAME = "parsers/test/mocks/US_CA/20250219_20250227_SLD_FCST_7DA_20250221_01_09_58_v1.zip"

        # Read zip and extract the csv file
        with zipfile.ZipFile(MOCK_ZIP_FILENAME, "r") as z:
            csv_filename = z.namelist()[
                0
            ]  # Get the first file in the zip (there is only one file)
            with z.open(csv_filename) as f:  # Read the CSV file into a pandas DataFrame
                df = pd.read_csv(f)
        return df

    # Mock the call to _get_oasis_data with above (with patch)
    with patch("parsers.US_CA._get_oasis_data", _mock_get_oasis_data):
        result = US_CA.fetch_consumption_forecast(
            zone_key=ZoneKey("US-CAL-CISO"), logger=getLogger("test")
        )

    snapshot.assert_match(result)
