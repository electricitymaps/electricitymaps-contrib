import re
from datetime import datetime
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.parsers.CA_ON import (
    TIMEZONE,
    fetch_consumption_forecast,
    fetch_price,
    fetch_wind_solar_forecasts,
)
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/CA_ON")


def test_fetch_wind_solar_forecasts(requests_mock, session, snapshot):
    # Mock VG Forecast Summary report request
    var_gen_forecast_summary_report = Path(
        base_path_to_mock, "var_gen_forecast_summary_report_20250228.xml"
    )
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/VGForecastSummary/PUB_VGForecastSummary_\d{8}\.xml"
        ),
        text=var_gen_forecast_summary_report.read_text(),
    )

    # Mock Adequacy report request
    adequacy_report = Path(base_path_to_mock, "adequacy_report_20250228.xml")
    requests_mock.register_uri(
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


def test_fetch_consumption_forecast(requests_mock, session, snapshot):
    # Mock Adequacy report request
    adequacy_report = Path(base_path_to_mock, "adequacy_report_20250228.xml")
    requests_mock.register_uri(
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


def test_fetch_price(requests_mock, session, snapshot):
    # Mock the Day-Ahead Hourly Ontario Zonal Price report request. This report
    # replaced the discontinued DispUnconsHOEP (HOEP) report when IESO launched
    # its two-settlement Market Renewal market structure on 2025-05-01.
    da_hourly_ontario_zonal_price_report = Path(
        base_path_to_mock, "da_hourly_ontario_zonal_price_report_20260528.xml"
    )
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/DAHourlyOntarioZonalPrice/PUB_DAHourlyOntarioZonalPrice_\d{8}\.xml"
        ),
        text=da_hourly_ontario_zonal_price_report.read_text(),
    )

    # Pass an explicit target_datetime so a single day is fetched, keeping the
    # snapshot deterministic (the real-time path would fetch the last two days).
    assert snapshot == fetch_price(
        zone_key=ZoneKey("CA-ON"),
        session=session,
        target_datetime=datetime(2026, 5, 28, tzinfo=TIMEZONE),
    )
