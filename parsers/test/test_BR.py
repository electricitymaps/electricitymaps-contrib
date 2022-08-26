#!/usr/bin/env python3

"""Tests for BR.py"""

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from arrow import get

from parsers import BR


class ProductionTestcase(unittest.TestCase):
    """
    Tests for fetch_production.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self):
        with open("parsers/test/mocks/BR.html") as f:
            self.fake_data = json.load(f)

        with patch("parsers.BR.get_data", return_value=self.fake_data) as gd:
            self.data = BR.fetch_production("BR-CS")

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_hydro_merge(self):
        """Check that hydro keys correctly merge into one."""

        data = self.data
        self.assertEqual(data["production"]["hydro"], 35888.05363)

    def test_wind(self):
        data = self.data
        self.assertEqual(data["production"]["wind"], 4.2)

    def test_correct_datetime(self):
        data = self.data
        expected_dt = get("2018-01-27T20:19:00-02:00").datetime
        self.assertEqual(data["datetime"], expected_dt)

    def test_source(self):
        data = self.data
        self.assertEqual(data["source"], "ons.org.br")

    def test_zoneKey_match(self):
        data = self.data
        self.assertEqual(data["zoneKey"], "BR-CS")

    def test_storage_type(self):
        data = self.data
        self.assertIsInstance(data["storage"], dict)


class ExchangeTestcase(unittest.TestCase):
    """
    Tests for fetch_exchange.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self):
        with open("parsers/test/mocks/BR.html") as f:
            self.fake_data = json.load(f)

        with patch("parsers.BR.get_data", return_value=self.fake_data) as gd:
            self.data = BR.fetch_exchange("BR-S", "UY")

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_key_match(self):
        data = self.data
        self.assertEqual(data["sortedZoneKeys"], "BR-S->UY")

    def test_correct_datetime(self):
        data = self.data
        expected_dt = get("2018-01-27T20:19:00-02:00").datetime
        self.assertEqual(data["datetime"], expected_dt)

    def test_flow(self):
        data = self.data
        self.assertEqual(data["netFlow"], 14.0)

    def test_source(self):
        data = self.data
        self.assertEqual(data["source"], "ons.org.br")


class RegionTestcase(unittest.TestCase):
    """
    Tests for fetch_region_exchange.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self):
        with open("parsers/test/mocks/BR.html") as f:
            self.fake_data = json.load(f)

        with patch("parsers.BR.get_data", return_value=self.fake_data) as gd:
            self.data = BR.fetch_region_exchange("BR-N", "BR-NE")

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_key_match(self):
        data = self.data
        self.assertEqual(data["sortedZoneKeys"], "BR-N->BR-NE")

    def test_correct_datetime(self):
        data = self.data
        expected_dt = get("2018-01-27T20:19:00-02:00").datetime
        self.assertEqual(data["datetime"], expected_dt)

    def test_flow(self):
        data = self.data
        self.assertEqual(data["netFlow"], 2967.768)

    def test_source(self):
        data = self.data
        self.assertEqual(data["source"], "ons.org.br")


if __name__ == "__main__":
    unittest.main()
