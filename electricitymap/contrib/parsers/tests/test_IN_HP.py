from importlib import resources

import pytest
from requests_mock import POST
from testfixtures import LogCapture

from electricitymap.contrib.parsers import IN_HP


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        POST,
        IN_HP.DATA_URL,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks")
        .joinpath("IN_HP.html")
        .read_text(),
    )


def test_fetch_production(session):
    with LogCapture() as log:
        data = IN_HP.fetch_production("IN-HP", session)
        assert data["zoneKey"] == "IN-HP"
        assert data["source"] == "hpsldc.com"
        assert data["datetime"]
        assert data["production"] == {"hydro": 4238.05, "unknown": 323.44}

        # Check rows that failed to parse in each table were logged correctly.
        logs = log.actual()
        assert len(logs) == 2
        assert "UNKNOWN HP PLANT" in logs[0][2]
        assert "UNKNOWN ISGS PLANT" in logs[1][2]
