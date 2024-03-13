#!/usr/bin/python

"""Tests for quality.py."""

import unittest

from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.quality import (
    validate_consumption,
    validate_exchange,
    validate_production,
)
from parsers.test.mocks.quality_check import *  # noqa: F403


class ConsumptionTestCase(unittest.TestCase):
    """Tests for validate_consumption."""

    def test_positive_consumption(self):
        self.assertFalse(
            validate_consumption(c1, ZoneKey("FR")),  # noqa: F405
            msg="Positive consumption is fine!",
        )

    def test_negative_consumption(self):
        with self.assertRaises(ValueError, msg="Negative consumption is not allowed!"):
            validate_consumption(c2, ZoneKey("FR"))  # noqa: F405

    def test_None_consumption(self):
        self.assertFalse(
            validate_consumption(c3, ZoneKey("FR")),  # noqa: F405
            msg="Consumption can be undefined!",
        )


class ExchangeTestCase(unittest.TestCase):
    """Tests for validate_exchange"""

    def test_key_mismatch(self):
        with self.assertRaises(Exception, msg="Key mismatch must be caught!"):
            validate_exchange(e1, "DK->NA")  # noqa: F405

    def test_no_datetime(self):
        with self.assertRaises(Exception, msg="Datetime key must be present!"):
            validate_exchange(e2, "DK->NO")  # noqa: F405

    def test_bad_datetime(self):
        with self.assertRaises(Exception, msg="datetime object required!"):
            validate_exchange(e3, "DK->NO")  # noqa: F405

    def test_future_not_allowed(self):
        with self.assertRaises(
            Exception, msg="Datapoints from the future are not valid!"
        ):
            validate_exchange(e4, "DK->NO")  # noqa: F405


class ProductionTestCase(unittest.TestCase):
    """Tests for validate_production."""

    def test_no_datetime(self):
        with self.assertRaises(Exception, msg="Datetime key must be present!"):
            validate_production(p1, ZoneKey("FR"))  # noqa: F405

    def test_no_zoneKey(self):
        with self.assertRaises(Exception, msg="zoneKey is required!"):
            validate_production(p2, ZoneKey("FR"))  # noqa: F405

    def test_bad_datetime(self):
        with self.assertRaises(Exception, msg="datetime object is required!"):
            validate_production(p3, ZoneKey("FR"))  # noqa: F405

    def test_zoneKey_mismatch(self):
        with self.assertRaises(Exception, msg="zoneKey mismatch must be caught!"):
            validate_production(p4, ZoneKey("FR"))  # noqa: F405

    def test_future_not_allowed(self):
        with self.assertRaises(
            Exception, msg="Datapoints from the future are not valid!"
        ):
            validate_production(p5, ZoneKey("FR"))  # noqa: F405

    def test_missing_types(self):
        with self.assertRaises(Exception, msg="Coal/Oil/Unknown are required!"):
            validate_production(p6, ZoneKey("FR"))  # noqa: F405

    def test_missing_types_allowed(self):
        self.assertFalse(
            validate_production(p7, ZoneKey("CH")),  # noqa: F405
            msg="CH, NO, AU-TAS, US-NEISO don't require Coal/Oil/Unknown!",
        )

    def test_negative_production(self):
        with self.assertRaises(
            Exception, msg="Negative generation should be rejected!"
        ):
            validate_production(p8, ZoneKey("FR"))  # noqa: F405

    def test_good_datapoint(self):
        self.assertFalse(
            validate_production(p9, ZoneKey("FR")),  # noqa: F405
            msg="This datapoint is good!",
        )


if __name__ == "__main__":
    unittest.main()
