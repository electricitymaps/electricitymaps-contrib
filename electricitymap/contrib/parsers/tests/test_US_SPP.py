import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from pandas import read_pickle
from requests_mock import GET
from testfixtures import LogCapture

from electricitymap.contrib.parsers import US_SPP
from electricitymap.contrib.types import ZoneKey


def test_fetch_production():
    filename = "electricitymap/contrib/parsers/tests/mocks/US_SPP_Gen_Mix.pkl"
    mock_data = read_pickle(filename)
    # Suppress log messages to prevent interfering with test formatting.
    with LogCapture(), patch("electricitymap.contrib.parsers.US_SPP.get_data") as gd:
        gd.return_value = mock_data
        data = US_SPP.fetch_production(
            zone_key=ZoneKey("US-SW-AZPS"), logger=logging.getLogger("test")
        )
        datapoint = data[-1]

    assert isinstance(data, list)
    assert len(data) == 23

    # Unknown keys must be assigned and summed.
    assert round(datapoint["production"]["unknown"], 2) == 33.1
    assert datapoint["datetime"] == datetime(2018, 7, 27, 11, 45, tzinfo=timezone.utc)
    assert datapoint["source"] == "spp.org"
    assert datapoint["zoneKey"] == "US-SW-AZPS"
    assert isinstance(datapoint["storage"], dict)


def test_SPP_logging():
    """Make sure that new generation types are logged properly."""
    filename = "electricitymap/contrib/parsers/tests/mocks/US_SPP_Gen_Mix.pkl"
    mock_data = read_pickle(filename)

    with LogCapture() as log:
        with patch("electricitymap.contrib.parsers.US_SPP.get_data") as gd:
            gd.return_value = mock_data
            US_SPP.fetch_production(
                zone_key=ZoneKey("US-SW-AZPS"), logger=logging.getLogger("test")
            )
        log.check(
            (
                "test",
                "WARNING",
                """New column 'Flux Capacitor' present in US-SPP data source.""",
            )
        )


def test_fetch_realtime_locational_marginal_price(adapter, session, snapshot):
    # Mock 8 consecutive 5-minute intervals of LMP data
    base_url = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app/file-browser-api/download/rtbm-lmp-by-location?host=https://portal.spp.org&path=/2025/03/By_Interval/31/RTBM-LMP-SL-{}.csv"
    times = [
        "202503310910",
        "202503310905",
        "202503310900",
        "202503310855",
        "202503310850",
        "202503310845",
        "202503310840",
    ]

    for time in times:
        mock_csv = Path(
            f"electricitymap/contrib/parsers/tests/mocks/US_SPP/RTBM-LMP-SL-{time}.csv"
        )
        adapter.register_uri(GET, base_url.format(time), text=mock_csv.read_text())

    realtime_LMP = US_SPP.fetch_realtime_locational_marginal_price(
        zone_key=ZoneKey("US-CENT-SWPP"),
        session=session,
        target_datetime=datetime(
            2025, 3, 31, 9, 10, tzinfo=ZoneInfo("America/Chicago")
        ),
    )

    assert snapshot == realtime_LMP


def test_fetch_dayahead_locational_marginal_price(adapter, session, snapshot):
    mock_csv = Path(
        "electricitymap/contrib/parsers/tests/mocks/US_SPP/DA-LMP-SL-202503190100.csv"
    )
    base_url = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app/file-browser-api/download/da-lmp-by-location?host=https://portal.spp.org&path=/2025/03/By_Day/DA-LMP-SL-202503190100.csv"

    adapter.register_uri(GET, base_url, text=mock_csv.read_text())

    dayahead_LMP = US_SPP.fetch_dayahead_locational_marginal_price(
        zone_key=ZoneKey("US-CENT-SWPP"),
        session=session,
        target_datetime=datetime(2025, 3, 19, 1, 0, tzinfo=ZoneInfo("America/Chicago")),
    )

    assert snapshot == dayahead_LMP
