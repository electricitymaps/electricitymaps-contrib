import json
import logging
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from testfixtures import LogCapture

from electricitymap.contrib.parsers import US_ERCOT


def test_fetch_production():
    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT.json") as f:
        fake_data = json.load(f)
    with LogCapture(), patch("electricitymap.contrib.parsers.US_ERCOT.get_data") as gjd:
        gjd.return_value = fake_data
        data = US_ERCOT.fetch_production(logger=logging.getLogger("test"))

    assert data
    assert data[0]["production"]["coal"] == 5067.958333
    assert data[-1]["datetime"] == datetime(
        2024, 11, 24, 8, 0, tzinfo=ZoneInfo("US/Central")
    )
    assert data[-1]["source"] == "ercot.com"
    assert data[-1]["zoneKey"] == "US-TEX-ERCO"
    assert isinstance(data[-1]["storage"], dict)


def test_fetch_consumption():
    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_demand.json") as f:
        fake_data = json.load(f)
    with LogCapture(), patch("electricitymap.contrib.parsers.US_ERCOT.get_data") as gjd:
        gjd.return_value = fake_data
        data = US_ERCOT.fetch_consumption(logger=logging.getLogger("test"))

        assert data
        assert data[0]["consumption"] == 42015.44
        assert data[0]["datetime"] == datetime(
            2024, 11, 24, 0, 0, tzinfo=ZoneInfo("US/Central")
        )
        assert data[0]["source"] == "ercot.com"
        assert data[0]["zoneKey"] == "US-TEX-ERCO"
