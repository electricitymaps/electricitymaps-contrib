import re
from json import loads
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.US_ERCOT import (
    ReportTypeID,
    fetch_consumption_forecast,
    fetch_wind_solar_forecasts,
)

US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "host=https://www.ercot.com"
BASE_PATH_TO_MOCK = Path("parsers/test/mocks/US_ERCOT")


def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot):
    # Mock load forecast request
    data = Path(BASE_PATH_TO_MOCK, "load_forecast_by_forecast_zone.json")
    adapter.register_uri(
        GET,
        re.compile(
            rf"{US_PROXY}/misapp/servlets/IceDocListJsonWS\?reportTypeId={ReportTypeID.LOAD_FORECAST_REPORTID.value}&_\d+\&{HOST_PARAMETER}"
        ),
        json=loads(data.read_text()),
    )

    # Mock specific report id request
    data_zip_file = Path(BASE_PATH_TO_MOCK, "load_forecast_specific_reportid.zip")
    with open(data_zip_file, "rb") as zip_file:
        zip_content = zip_file.read()

    adapter.register_uri(
        GET,
        re.compile(
            rf"{US_PROXY}/misdownload/servlets/mirDownload\?doclookupId=\d+\&{HOST_PARAMETER}"
        ),
        content=zip_content,
    )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("US-TEX-ERCO"),
        session=session,
    )


def test_snapshot_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock wind forecast request
    data_wind = Path(
        BASE_PATH_TO_MOCK,
        "wind_power_production_hourly_averaged_actual_and_forecasted_values_rtid.json",
    )
    adapter.register_uri(
        GET,
        re.compile(
            rf"{US_PROXY}/misapp/servlets/IceDocListJsonWS\?reportTypeId={ReportTypeID.WIND_POWER_PRODUCTION_REPORTID.value}&_\d+\&{HOST_PARAMETER}"
        ),
        json=loads(data_wind.read_text()),
    )

    # Mock solar forecast request
    data_solar = Path(
        BASE_PATH_TO_MOCK,
        "solar_power_production_hourly_averaged_actual_and_forecasted_values_rtid.json",
    )
    adapter.register_uri(
        GET,
        re.compile(
            rf"{US_PROXY}/misapp/servlets/IceDocListJsonWS\?reportTypeId={ReportTypeID.SOLAR_POWER_PRODUCTION_REPORTID.value}&_\d+\&{HOST_PARAMETER}"
        ),
        json=loads(data_solar.read_text()),
    )

    # Wind specific report id
    data_wind_zip_file = Path(BASE_PATH_TO_MOCK, "wind_specific_reportid.zip")
    with open(data_wind_zip_file, "rb") as zip_file:
        wind_zip_content = zip_file.read()

    # Solar specific report id
    data_solar_zip_file = Path(BASE_PATH_TO_MOCK, "solar_specific_reportid.zip")
    with open(data_solar_zip_file, "rb") as zip_file:
        solar_zip_content = zip_file.read()

    request_count = 0  # Global counter to track requests

    def download_callback(request, context):
        nonlocal request_count
        request_count += 1  # Increment on each request
        if request_count == 1:
            return wind_zip_content  # First request: Wind ZIP data
        elif request_count == 2:
            return solar_zip_content  # Second request: Solar ZIP data
        return None  # Fail for unexpected calls

    # Mock the wind or solar report request
    adapter.register_uri(
        GET,
        re.compile(
            rf"{US_PROXY}/misdownload/servlets/mirDownload\?doclookupId=\d+\&{HOST_PARAMETER}"
        ),
        content=download_callback,
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("US-TEX-ERCO"),
        session=session,
    )
