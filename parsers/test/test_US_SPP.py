import logging
from datetime import datetime, timezone
from unittest.mock import patch

from pandas import read_pickle
from testfixtures import LogCapture

from electricitymap.contrib.lib.types import ZoneKey
from parsers import US_SPP


def test_fetch_production():
    filename = "parsers/test/mocks/US_SPP_Gen_Mix.pkl"
    mock_data = read_pickle(filename)
    # Suppress log messages to prevent interfering with test formatting.
    with LogCapture(), patch("parsers.US_SPP.get_data") as gd:
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
    filename = "parsers/test/mocks/US_SPP_Gen_Mix.pkl"
    mock_data = read_pickle(filename)

    with LogCapture() as log:
        with patch("parsers.US_SPP.get_data") as gd:
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
