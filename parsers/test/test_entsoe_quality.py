#!/usr/bin/python

"""Tests for validation in ENTSOE parser."""
import logging
import unittest

from parsers.ENTSOE import validate_production
from parsers.test.mocks.quality_check import *


class ProductionTestCase(unittest.TestCase):
    """Tests for ENTSOE's validate_production."""

    test_logger = logging.getLogger()
    test_logger.setLevel(logging.ERROR)

    def test_missing_required_biomass_in_DE(self):
        validated = validate_production(p10, self.test_logger)
        self.assertEqual(validated, None)

    def test_production_too_low_in_PL(self):
        validated = validate_production(p11, self.test_logger)
        self.assertEqual(validated, None)

    def test_production_too_high_in_SI(self):
        validated = validate_production(p12, self.test_logger)
        self.assertEqual(validated, None)

    def test_missing_solar_in_DK1(self):
        validated = validate_production(p13, self.test_logger)
        self.assertEqual(validated, None)

    def test_valid_production_in_FI(self):
        validated = validate_production(p14, self.test_logger)
        self.assertNotEqual(validated, None)
        self.assertTrue("production" in validated)
        self.assertTrue("hydro" in validated["production"])


if __name__ == "__main__":
    unittest.main()
