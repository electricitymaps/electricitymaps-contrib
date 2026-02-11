"""Tests for config/__init__.py."""

import pytest
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import emission_factors


@pytest.fixture
def emission_factor_result(zone_key):
    """Fixture to generate emission factor result in the expected format."""
    return {
        "emissionFactors": {
            "defaults": {
                key: {"value": value, "source": "IPCC 2014"}
                for key, value in emission_factors(zone_key).items()
            },
            "zoneOverrides": {},
        }
    }


@pytest.mark.parametrize("zone_key", ["KR", "FR"])
def test_snapshot_emission_factor(snapshot, zone_key, emission_factor_result):
    """Test emission factors configuration."""
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == emission_factor_result
