#!/usr/bin/env python3

"""Tests for US_MISO.py"""

import json
import logging
import os
import unittest
from datetime import datetime
from unittest.mock import patch

import pytz
from arrow import get
from testfixtures import LogCapture

from parsers import US_ERCOT


class TestUSERCOT(unittest.TestCase):
    """Patches in a fake response from the data source to allow repeatable testing."""

    def test_fetch_production(self):
        filename = "parsers/test/mocks/ERCOT.json"
        with open(filename) as f:
            fake_data = json.load(f)

        with LogCapture() as log:
            with patch("parsers.US_ERCOT.get_data") as gjd:
                gjd.return_value = fake_data
                data = US_ERCOT.fetch_production(logger=logging.getLogger("test"))

        with self.subTest():
            self.assertIsNotNone(data)
        with self.subTest():
            self.assertEqual(data[0]["production"]["coal"], 10461.9)
        with self.subTest():
            expected_dt = datetime(2023, 2, 2, 4, 39, 55).replace(
                tzinfo=pytz.timezone("US/Central")
            )
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

        with LogCapture() as log:
            with patch("parsers.US_ERCOT.get_data") as gjd:
                gjd.return_value = fake_data
                data = US_ERCOT.fetch_consumption(logger=logging.getLogger("test"))

        with self.subTest():
            self.assertIsNotNone(data)
        with self.subTest():
            self.assertEqual(data[0]["consumption"], 57102.55)
        with self.subTest():
            expected_dt = datetime(2023, 2, 1, 0, 0, 0).replace(
                tzinfo=pytz.timezone("US/Central")
            )
            self.assertEqual(data[0]["datetime"], expected_dt)
        with self.subTest():
            self.assertEqual(data[0]["source"], "ercot.com")
        with self.subTest():
            self.assertEqual(data[0]["zoneKey"], "US-TEX-ERCO")


if __name__ == "__main__":
    unittest.main(buffer=True)
