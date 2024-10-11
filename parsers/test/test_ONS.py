#!/usr/bin/env python3

"""Tests for BR.py"""

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ONS


class ProductionTestcase(unittest.TestCase):
    """
    Tests for fetch_production.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self):
        with open("parsers/test/mocks/ONS/BR.json") as f:
            self.fake_data = json.load(f)

        with patch("parsers.ONS.get_data", return_value=self.fake_data):
            self.data = ONS.fetch_production(ZoneKey("BR-CS"))

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_hydro_merge(self):
        """Check that hydro keys correctly merge into one."""

        data = self.data
        self.assertEqual(data[0]["production"]["hydro"], 35888.05363)

    def test_wind(self):
        data = self.data
        self.assertEqual(data[0]["production"]["wind"], 4.2)

    def test_correct_datetime(self):
        data = self.data
        expected_dt = datetime.fromisoformat("2018-01-27T20:19:00-02:00")
        self.assertEqual(data[0]["datetime"], expected_dt)

    def test_source(self):
        data = self.data
        self.assertEqual(data[0]["source"], "ons.org.br")

    def test_zoneKey_match(self):
        data = self.data
        self.assertEqual(data[0]["zoneKey"], "BR-CS")

    def test_storage_type(self):
        data = self.data
        self.assertIsInstance(data[0]["storage"], dict)

    def test_negative_solar(self):
        with open("parsers/test/mocks/ONS/BR_negative_solar.json") as f:
            fake_data = json.load(f)

            with patch("parsers.ONS.get_data", return_value=fake_data):
                data = ONS.fetch_production(ZoneKey("BR-CS"))
                self.assertEqual(data[0]["production"]["solar"], 0)


class ExchangeTestcase(unittest.TestCase):
    """
    Tests for fetch_exchange.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self):
        with open("parsers/test/mocks/ONS/BR.json") as f:
            self.fake_data = json.load(f)

        with patch("parsers.ONS.get_data", return_value=self.fake_data):
            self.data = ONS.fetch_exchange("BR-S", "UY")[0]

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_key_match(self):
        data = self.data
        self.assertEqual(data["sortedZoneKeys"], "BR-S->UY")

    def test_correct_datetime(self):
        data = self.data
        expected_dt = datetime.fromisoformat("2018-01-27T20:19:00-02:00")
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
        with open("parsers/test/mocks/ONS/BR.json") as f:
            self.fake_data = json.load(f)

        with patch("parsers.ONS.get_data", return_value=self.fake_data):
            self.data = ONS.fetch_exchange("BR-N", "BR-NE")[0]

    def test_is_not_none(self):
        data = self.data
        self.assertIsNotNone(data)

    def test_key_match(self):
        data = self.data
        self.assertEqual(data["sortedZoneKeys"], "BR-N->BR-NE")

    def test_correct_datetime(self):
        data = self.data
        expected_dt = datetime.fromisoformat("2018-01-27T20:19:00-02:00")
        self.assertEqual(data["datetime"], expected_dt)

    def test_flow(self):
        data = self.data
        self.assertEqual(data["netFlow"], 2967.768)

    def test_source(self):
        data = self.data
        self.assertEqual(data["source"], "ons.org.br")


if __name__ == "__main__":
    unittest.main()
