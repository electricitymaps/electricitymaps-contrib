from pathlib import Path

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers import HN

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/HN")


def test_fetch_production(adapter, session, snapshot):
    """Test production data parsing with snapshot testing."""
    # Mock all production CSV files
    production_files = [
        ("production_index_1_hydro.csv", 1),
        ("production_index_2_wind.csv", 2),
        ("production_index_3_solar.csv", 3),
        ("production_index_4_geothermal.csv", 4),
        ("production_index_5_biomass.csv", 5),
        ("production_index_6_coal.csv", 6),
        ("production_index_8_oil.csv", 8),
        ("production_index_9_oil.csv", 9),
        ("production_index_10_hydro.csv", 10),
    ]

    def mock_response(request, context):
        """Mock response based on the p8_indx parameter."""
        index = int(request.qs.get("p8_indx", [0])[0])

        for filename, file_index in production_files:
            if index == file_index:
                file_path = base_path_to_mock / filename
                return file_path.read_text(encoding="utf-8")

        return ""

    adapter.register_uri(
        GET,
        ANY,
        text=mock_response,
    )

    result = HN.fetch_production(ZoneKey("HN"), session)
    assert snapshot == result


@pytest.mark.parametrize(
    "zone_key1,zone_key2",
    [
        ("GT", "HN"),
        ("HN", "NI"),
        ("HN", "SV"),
        ("HN", "US"),  # Test case with no matching zone
    ],
)
def test_fetch_exchange(adapter, session, snapshot, zone_key1, zone_key2):
    """Test exchange data parsing with snapshot testing."""
    exchange_file = base_path_to_mock / "exchange_index_7.csv"

    adapter.register_uri(
        GET,
        ANY,
        text=exchange_file.read_text(encoding="utf-8"),
    )

    result = HN.fetch_exchange(zone_key1, zone_key2, session)
    assert snapshot == result
