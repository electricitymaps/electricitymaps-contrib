#!/usr/bin/env python3

"""Tests for US_SPP.py"""

import logging
import unittest
from datetime import datetime
from unittest.mock import patch

from arrow import get
from pandas import read_pickle
from testfixtures import LogCapture

from parsers import US_SPP


class TestUSSPP(unittest.TestCase):
    """Patches in a fake response from the data source to allow consistent testing."""

    def test_fetch_production(self):
        filename = "parsers/test/mocks/US_SPP_Gen_Mix.pkl"
        fake_data = read_pickle(filename)

        # Suppress log messages to prevent interfering with test formatting.
        with LogCapture() as log:
            with patch("parsers.US_SPP.get_data") as gd:
                gd.return_value = fake_data
                data = US_SPP.fetch_production(logger=logging.getLogger("test"))
                datapoint = data[-1]

        with self.subTest():
            self.assertIsInstance(data, list)

        with self.subTest():
            self.assertEqual(len(data), 23)

        # Unknown keys must be assigned and summed.
        with self.subTest():
            self.assertEqual(round(datapoint["production"]["unknown"], 2), 33.1)

        with self.subTest():
            expected_dt = get(datetime(2018, 7, 27, 11, 45), "UTC").datetime
            self.assertEqual(datapoint["datetime"], expected_dt)

        with self.subTest():
            self.assertEqual(datapoint["source"], "spp.org")

        with self.subTest():
            self.assertEqual(datapoint["zoneKey"], "US-SPP")

        with self.subTest():
            self.assertIsInstance(datapoint["storage"], dict)

    def test_SPP_logging(self):
        """Make sure that new generation types are logged properly."""

        filename = "parsers/test/mocks/US_SPP_Gen_Mix.pkl"
        fake_data = read_pickle(filename)

        with LogCapture() as log:
            with patch("parsers.US_SPP.get_data") as gd:
                gd.return_value = fake_data
                data = US_SPP.fetch_production(logger=logging.getLogger("test"))
            log.check(
                (
                    "test",
                    "WARNING",
                    """New column 'Flux Capacitor' present in US-SPP data source.""",
                )
            )


if __name__ == "__main__":
    unittest.main(buffer=True)
