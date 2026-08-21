import json
import logging
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from testfixtures import LogCapture

from electricitymap.contrib.parsers import US_ERCOT


def test_fetch_production():
    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_generation.json") as f:
        fake_generation_data = json.load(f)

    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_storage.json") as f:
        fake_storage_data = json.load(f)

    def mock_get_data(url, **kwargs):
        if "energy-storage-resources" in url:
            return fake_storage_data
        else:
            return fake_generation_data

    with patch("electricitymap.contrib.parsers.US_ERCOT.get_data") as gjd:
        gjd.side_effect = mock_get_data
        data = US_ERCOT.fetch_production(logger=logging.getLogger("test"))
    assert data

    assert data[-1]["source"] == "ercot.com"
    assert data[-1]["zoneKey"] == "US-TEX-ERCO"

    # Check that storage data is present and contains battery
    assert isinstance(data[-1]["storage"], dict)
    assert "battery" in data[-1]["storage"]
    assert isinstance(data[-1]["storage"]["battery"], int | float)

    # Verify that there are data points from 2 days (previousDay and currentDay)
    dates = {item["datetime"].date() for item in data}
    assert len(dates) == 2, (
        f"Expected data from exactly 2 days, but got {len(dates)} days: {dates}"
    )


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


def test_fetch_production_with_target_datetime_raises_not_implemented():
    """Test that fetch_production raises NotImplementedError when target_datetime is provided."""
    target_datetime = datetime(2024, 1, 1, 12, 0, tzinfo=ZoneInfo("US/Central"))

    with pytest.raises(
        NotImplementedError, match="This parser is not yet able to parse past dates."
    ):
        US_ERCOT.fetch_production(
            target_datetime=target_datetime, logger=logging.getLogger("test")
        )
