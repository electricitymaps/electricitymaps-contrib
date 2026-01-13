import re
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.parsers.CA_ON import (
    fetch_consumption_forecast,
    fetch_wind_solar_forecasts,
)
from electricitymap.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/CA_ON")


def test_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock VG Forecast Summary report request
    var_gen_forecast_summary_report = Path(
        base_path_to_mock, "var_gen_forecast_summary_report_20250228.xml"
    )
    adapter.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/VGForecastSummary/PUB_VGForecastSummary_\d{8}\.xml"
        ),
        text=var_gen_forecast_summary_report.read_text(),
    )

    # Mock Adequacy report request
    adequacy_report = Path(base_path_to_mock, "adequacy_report_20250228.xml")
    adapter.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/Adequacy2/PUB_Adequacy2_\d{8}\.xml"
        ),
        text=adequacy_report.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("CA-ON"),
        session=session,
    )


def test_fetch_consumption_forecast(adapter, session, snapshot):
    # Mock Adequacy report request
    adequacy_report = Path(base_path_to_mock, "adequacy_report_20250228.xml")
    adapter.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/Adequacy2/PUB_Adequacy2_\d{8}\.xml"
        ),
        text=adequacy_report.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("CA-ON"),
        session=session,
    )
