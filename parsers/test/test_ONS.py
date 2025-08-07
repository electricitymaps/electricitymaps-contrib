import json
from pathlib import Path
from unittest.mock import patch

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ONS

# Base path for mock data files
MOCK_DATA_DIR = Path(__file__).parent / "mocks" / "ONS"


@pytest.fixture()
def mock_response():
    with open("parsers/test/mocks/ONS/BR.json") as f:
        mock_data = json.load(f)
    with patch("parsers.ONS.get_data", return_value=mock_data):
        yield


@pytest.mark.parametrize(
    "data_file", ["BR.json", "BR_negative_solar.json", "data.json"]
)
@pytest.mark.parametrize("zone_key", ["BR-NE", "BR-N", "BR-CS", "BR-S"])
def test_snapshot_fetch_production(zone_key, data_file, adapter, session, snapshot):
    """Test fetch_production with snapshot using different data files for all Brazilian subzones."""
    mock_data_path = MOCK_DATA_DIR / data_file
    mock_data = json.loads(mock_data_path.read_text())

    adapter.register_uri(
        GET,
        "http://tr.ons.org.br/Content/GetBalancoEnergetico/null",
        json=mock_data,
    )

    assert snapshot == ONS.fetch_production(
        zone_key=ZoneKey(zone_key),
        session=session,
    )


@pytest.mark.parametrize(
    "data_file", ["BR.json", "BR_negative_solar.json", "data.json"]
)
@pytest.mark.parametrize(
    "zone_key1,zone_key2",
    [
        ("BR-CS", "BR-S"),  # sud_sudeste
        ("BR-CS", "BR-NE"),  # sudeste_nordeste
        ("BR-CS", "BR-N"),  # sudeste_norteFic
        ("BR-N", "BR-NE"),  # norteFic_nordeste
        ("BR-S", "UY"),  # uruguai
        ("AR", "BR-S"),  # argentina
        ("BR-S", "PY"),  # paraguai
    ],
)
def test_snapshot_fetch_exchange(
    zone_key1, zone_key2, data_file, adapter, session, snapshot
):
    """Test fetch_exchange with snapshot using different data files for all exchanges."""
    mock_data_path = MOCK_DATA_DIR / data_file
    mock_data = json.loads(mock_data_path.read_text())

    adapter.register_uri(
        GET,
        "http://tr.ons.org.br/Content/GetBalancoEnergetico/null",
        json=mock_data,
    )

    assert snapshot == ONS.fetch_exchange(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
    )
