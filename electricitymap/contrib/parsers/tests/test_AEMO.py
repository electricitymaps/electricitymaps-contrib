"""Tests for AEMO.py"""

import re
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.AEMO import fetch_consumption_forecast

BASE_PATH_TO_MOCK = Path("electricitymap/contrib/parsers/tests/mocks/AEMO")


@pytest.mark.parametrize("zone_key", ["AU-NSW", "AU-VIC", "AU-QLD", "AU-SA", "AU-TAS"])
# "AU-WA" is not implemented in the zones here

def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot, zone_key):
    base_url = "http://nemweb.com.au/Reports/CURRENT/Operational_Demand/FORECAST_HH/"

    # Mock the base URL request with HTML that contains the expected link
    html_content = """
    <html>
    <body>
    <a href="PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_202504011800_20250401173353.zip">Link</a>
    </body>
    </html>
    """
    adapter.register_uri(
        GET,
        base_url,
        text=html_content,
    )

    # Mock specific document request
    data_zip_file = Path(
        BASE_PATH_TO_MOCK,
        "PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_202504011800_20250401173353.zip",
    )

    print("Mock file path:", data_zip_file.resolve())
    assert data_zip_file.exists(), "Mock zip file does not exist!"

    with open(data_zip_file, "rb") as zip_file:
        zip_content = zip_file.read()
    adapter.register_uri(
        GET,
        re.compile(rf"{base_url}PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_\d+_\d+\.zip"),
        content=zip_content,
    )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=datetime(2025, 4, 1, 18, 0),  # Mock file has this datetime
    )
