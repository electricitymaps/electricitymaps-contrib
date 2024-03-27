#!/usr/bin/env python3

"""Tests for US_MISO.py"""

import json
import logging
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from testfixtures import LogCapture

from parsers import US_MISO


class TestUSMISO(unittest.TestCase):
    """Patches in a fake response from the data source to allow repeatable testing."""

    def test_fetch_production(self):
        filename = "parsers/test/mocks/MISO.html"
        with open(filename) as f:
            fake_data = json.load(f)

        with LogCapture(), patch("parsers.US_MISO.get_json_data") as gjd:
            gjd.return_value = fake_data
            data = US_MISO.fetch_production(logger=logging.getLogger("test"))

        with self.subTest():
            self.assertIsNotNone(data)
        with self.subTest():
            self.assertEqual(data[0]["production"]["coal"], 40384.0)
        with self.subTest():
            expected_dt = datetime(
                2018, 1, 25, 4, 30, tzinfo=ZoneInfo("America/New_York")
            )
            self.assertEqual(data[0]["datetime"], expected_dt)
        with self.subTest():
            self.assertEqual(data[0]["source"], "misoenergy.org")
        with self.subTest():
            self.assertEqual(data[0]["zoneKey"], "US-MIDW-MISO")
        with self.subTest():
            self.assertIsInstance(data[0]["storage"], dict)

        # Make sure the unmapped Antimatter type is set to 'unknown'.
        with self.subTest():
            self.assertGreaterEqual(data[0]["production"]["unknown"], 256.0)


if __name__ == "__main__":
    unittest.main(buffer=True)
