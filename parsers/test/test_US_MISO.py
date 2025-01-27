#!/usr/bin/env python3

"""Tests for US_MISO.py"""

import json
import logging
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from testfixtures import LogCapture

from parsers import US_MISO


def test_fetch_production():
    filename = "parsers/test/mocks/MISO.html"
    with open(filename) as f:
        mock_data = json.load(f)
    with LogCapture(), patch("parsers.US_MISO.get_json_data") as gjd:
        gjd.return_value = mock_data
        production = US_MISO.fetch_production(logger=logging.getLogger("test"))

    assert production
    assert production[0]["production"]["coal"] == 40384.0
    assert production[0]["datetime"] == datetime(
        2018, 1, 25, 4, 30, tzinfo=ZoneInfo("America/New_York")
    )
    assert production[0]["source"] == "misoenergy.org"
    assert production[0]["zoneKey"] == "US-MIDW-MISO"
    assert isinstance(production[0]["storage"], dict)

    # Make sure the unmapped Antimatter type is set to 'unknown'.
    assert production[0]["production"]["unknown"] >= 256
