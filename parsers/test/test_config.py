#!/usr/bin/python

"""Tests for config/__init__.py."""

import unittest

from electricitymap.contrib.config import emission_factors


class EmissionFactorTestCase(unittest.TestCase):
    """Tests for emission_factor."""

    def test_emission_factors(self):
        """Test that emission_factors handles yearly defaults correctly."""

        # KR - no override
        expected = {
            "battery charge": 0,
            "battery discharge": 490.50488607461506,
            "biomass": 230,
            "coal": 820,
            "gas": 490,
            "geothermal": 38,
            "hydro": 24,
            "hydro charge": 0,
            "hydro discharge": 490.50488607461506,
            "nuclear": 12,
            "oil": 650,
            "solar": 45,
            "unknown": 644,
            "wind": 11,
        }
        self.assertEqual(emission_factors("KR"), expected)  # type: ignore

        # FR - override
        expected = {
            "battery charge": 0,
            "battery discharge": 66.82067058776849,
            "biomass": 230.0,
            "coal": 968.9049130000001,
            "gas": 501.61,
            "geothermal": 38,
            "hydro": 10.7,
            "hydro charge": 0,
            "hydro discharge": 66.82067058776849,
            "nuclear": 5.13,
            "oil": 999.44,
            "solar": 30.075,
            "unknown": 700,
            "wind": 12.62,
        }
        self.assertEqual(emission_factors("FR"), expected)  # type: ignore


if __name__ == "__main__":
    unittest.main()
