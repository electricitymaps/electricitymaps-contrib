#!/usr/bin/env python3

"""Tests for US_MISO.py"""

import json
import logging
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from testfixtures import LogCapture

from parsers import US_ERCOT


class TestUSERCOT(unittest.TestCase):
    """Patches in a fake response from the data source to allow repeatable testing."""

    def test_fetch_production(self):
        filename = "parsers/test/mocks/ERCOT.json"
        with open(filename) as f:
            fake_data = json.load(f)

        with LogCapture(), patch("parsers.US_ERCOT.get_data") as gjd:
            gjd.return_value = fake_data
            data = US_ERCOT.fetch_production(logger=logging.getLogger("test"))

        with self.subTest():
            self.assertIsNotNone(data)
        with self.subTest():
            self.assertEqual(data[0]["production"]["coal"], 5067.958333333333)
        with self.subTest():
            expected_dt = datetime(2024, 11, 24, 8, 0, tzinfo=ZoneInfo("US/Central"))
            self.assertEqual(data[-1]["datetime"], expected_dt)
        with self.subTest():
            self.assertEqual(data[-1]["source"], "ercot.com")
        with self.subTest():
            self.assertEqual(data[-1]["zoneKey"], "US-TEX-ERCO")
        with self.subTest():
            self.assertIsInstance(data[-1]["storage"], dict)

    def test_fetch_consumption(self):
        filename = "parsers/test/mocks/ERCOT_demand.json"
        with open(filename) as f:
            fake_data = json.load(f)

        with LogCapture(), patch("parsers.US_ERCOT.get_data") as gjd:
            gjd.return_value = fake_data
            data = US_ERCOT.fetch_consumption(logger=logging.getLogger("test"))

        with self.subTest():
            self.assertIsNotNone(data)
        with self.subTest():
            self.assertEqual(data[0]["consumption"], 42015.44)
        with self.subTest():
            expected_dt = datetime(2024, 11, 24, 0, 0, tzinfo=ZoneInfo("US/Central"))
            self.assertEqual(data[0]["datetime"], expected_dt)
        with self.subTest():
            self.assertEqual(data[0]["source"], "ercot.com")
        with self.subTest():
            self.assertEqual(data[0]["zoneKey"], "US-TEX-ERCO")


if __name__ == "__main__":
    unittest.main(buffer=True)
