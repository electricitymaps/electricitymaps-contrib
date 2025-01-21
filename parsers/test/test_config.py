"""Tests for config/__init__.py."""

from electricitymap.contrib.config import emission_factors


def test_emission_factors():
    """Test that emission_factors handles yearly defaults correctly."""

    # KR - no override
    expected = {
        "battery charge": 0,
        "battery discharge": 421.94,
        "biomass": 230,
        "coal": 820,
        "gas": 490,
        "geothermal": 38,
        "hydro": 24,
        "hydro charge": 0,
        "hydro discharge": 421.94,
        "nuclear": 12,
        "oil": 650,
        "solar": 45,
        "unknown": 644,
        "wind": 11,
    }
    assert emission_factors("KR") == expected

    # FR - override
    expected = {
        "battery charge": 0,
        "battery discharge": 43.69,
        "biomass": 230.0,
        "coal": 983.04,
        "gas": 511.79,
        "geothermal": 38,
        "hydro": 10.7,
        "hydro charge": 0,
        "hydro discharge": 43.69,
        "nuclear": 5.13,
        "oil": 901.06,
        "solar": 30.075,
        "unknown": 700,
        "wind": 12.62,
    }
    assert emission_factors("FR") == expected
