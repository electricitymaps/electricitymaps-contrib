"""Tests for RU.py"""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers.RU import fetch_exchange, fetch_production

BASE_PATH_TO_MOCK = Path("electricitymap/contrib/parsers/tests/mocks/RU")


@pytest.mark.parametrize("zone_key", ["RU-1", "RU-2", "RU-AS"])
@freeze_time("2025-07-28 12:00:00")
def test_snapshot_fetch_production(adapter, session, snapshot, zone_key):
    """Test fetch_production for different Russian zones using mock data."""
    # Determine which zones need to be mocked based on the test zone
    zones_to_mock = ["RU-1", "RU-2", "RU-AS"] if zone_key == "RU" else [zone_key]

    for zone in zones_to_mock:
        mock_file = BASE_PATH_TO_MOCK / f"production_{zone}_2025_07_28.json"
        if zone in ["RU-1", "RU-2"]:
            price_zone = 1 if zone == "RU-1" else 2
            url_pattern = re.compile(
                rf".*CommonInfo/PowerGeneration.*priceZone.*={price_zone}.*"
            )
        else:  # RU-AS
            url_pattern = re.compile(r".*CommonInfo/GenEquipOptions_Z2.*")

        adapter.register_uri(
            GET,
            url_pattern,
            json=json.loads(mock_file.read_text()),
        )

    # Test target datetime corresponding to the mock data
    target_datetime = datetime(2025, 7, 28, 12, 0)

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_production(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
    )


@pytest.mark.parametrize(
    "zone_key1,zone_key2,hour",
    [
        # Test major exchange pairs with different zones
        ("CN", "RU-AS", 10),
        ("MN", "RU-2", 10),
        ("KZ", "RU-1", 10),
        ("KZ", "RU-2", 10),
        ("GE", "RU-1", 10),
        ("AZ", "RU-1", 10),
        ("BY", "RU-1", 10),
        ("RU-1", "FI", 10),
        ("RU-KGD", "LT", 10),
        ("RU-1", "UA-CR", 10),
        ("UA", "RU-1", 10),
        ("RU-1", "RU-2", 10),
        # Test different hour to verify temporal behavior
        ("CN", "RU-AS", 11),
        ("KZ", "RU-1", 11),
    ],
)
@freeze_time("2025-07-28 12:00:00")
def test_snapshot_fetch_exchange(
    adapter, session, snapshot, zone_key1, zone_key2, hour
):
    """Test fetch_exchange for different exchange pairs using mock data."""
    # Load the appropriate mock file based on hour
    mock_file = BASE_PATH_TO_MOCK / f"exchange_2025-07-28_{hour}.json"

    # Mock the exchange API endpoint with specific pattern
    url_pattern = re.compile(r".*flowDiagramm/GetData.*")
    adapter.register_uri(
        GET,
        url_pattern,
        json=json.loads(mock_file.read_text()),
    )

    # Test target datetime corresponding to the mock data
    target_datetime = datetime(2025, 7, 28, hour, 0)

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_exchange(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
    )


@freeze_time("2025-07-28 12:00:00")
def test_snapshot_fetch_exchange_live(adapter, session, snapshot):
    """Test fetch_exchange without target_datetime (live mode) using mock data."""
    # Mock both hours 10 and 11 for live mode (last 2 hours)
    for hour in [10, 11]:
        mock_file = BASE_PATH_TO_MOCK / f"exchange_2025-07-28_{hour}.json"
        url_pattern = re.compile(r".*flowDiagramm/GetData.*")
        adapter.register_uri(
            GET,
            url_pattern,
            json=json.loads(mock_file.read_text()),
        )

    # Test without target_datetime (live mode) - using a pair not already tested above
    assert snapshot == fetch_exchange(
        zone_key1="MN",
        zone_key2="RU",
        session=session,
    )


@freeze_time("2025-07-28 12:00:00")
def test_snapshot_fetch_production_live(adapter, session, snapshot):
    """Test fetch_production without target_datetime (live mode) using mock data."""
    # Mock all zone endpoints for live mode with specific URL patterns
    for zone in ["RU-1", "RU-2", "RU-AS"]:
        mock_file = BASE_PATH_TO_MOCK / f"production_{zone}_2025_07_28.json"
        if zone in ["RU-1", "RU-2"]:
            price_zone = 1 if zone == "RU-1" else 2
            url_pattern = re.compile(
                rf".*CommonInfo/PowerGeneration.*priceZone.*={price_zone}.*"
            )
        else:  # RU-AS
            url_pattern = re.compile(r".*CommonInfo/GenEquipOptions_Z2.*")

        adapter.register_uri(
            GET,
            url_pattern,
            json=json.loads(mock_file.read_text()),
        )

    # Test without target_datetime (live mode) - using RU-2 since RU-1 is already tested above
    assert snapshot == fetch_production(
        zone_key="RU-2",
        session=session,
    )
