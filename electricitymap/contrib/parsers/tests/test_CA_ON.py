import re
from datetime import datetime
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.parsers.CA_ON import (
    TIMEZONE,
    fetch_consumption_forecast,
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
    # Mock Adequacy report request. fetch_consumption_forecast walks 8 days and
    # fetches one report per date; the real IESO endpoint returns a distinct
    # report per date, each stamped with its own DeliveryDate. Mirror that by
    # rewriting the fixture's DeliveryDate to the requested date so the loop
    # yields distinct (non-duplicate) datetimes instead of 8 copies of one day.
    fixture_text = Path(base_path_to_mock, "adequacy_report_20250228.xml").read_text()

    def adequacy_response(request, context):
        requested_date = datetime.strptime(
            re.search(r"PUB_Adequacy2_(\d{8})\.xml", request.url).group(1), "%Y%m%d"
        ).strftime("%Y-%m-%d")
        return fixture_text.replace(
            "<ns0:DeliveryDate>2025-02-28</ns0:DeliveryDate>",
            f"<ns0:DeliveryDate>{requested_date}</ns0:DeliveryDate>",
        )

    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://reports-public\.ieso\.ca/public/Adequacy2/PUB_Adequacy2_\d{8}\.xml"
        ),
        text=adequacy_response,
    )

    # Run function under test. Anchor the 8-day walk to a fixed date so the
    # snapshot is deterministic — without target_datetime the parser starts at
    # datetime.now() and the snapshot only matches on the day it was recorded.
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("CA-ON"),
        session=session,
        target_datetime=datetime(2025, 2, 28, 12, 0, tzinfo=TIMEZONE),
    )
