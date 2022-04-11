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
            "battery discharge": 391.33,
            "biomass": 230,
            "coal": 820,
            "gas": 490,
            "geothermal": 38,
            "hydro": 24,
            "hydro charge": 0,
            "hydro discharge": 391.33,
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
            "battery discharge": 54.19088892903222,
            "biomass": 230,
            "coal": 820,
            "gas": 490,
            "geothermal": 38,
            "hydro": 24,
            "hydro charge": 0,
            "hydro discharge": 54.19088892903222,
            "nuclear": 12,
            "oil": 650,
            "solar": 45,
            "unknown": 700,
            "wind": 11,
        }
        self.assertEqual(emission_factors("FR"), expected)  # type: ignore


if __name__ == "__main__":
    unittest.main()
