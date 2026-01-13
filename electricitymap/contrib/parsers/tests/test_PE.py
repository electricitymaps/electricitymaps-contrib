import json
from datetime import datetime
from pathlib import Path

from requests_mock import POST

from electricitymap.contrib.parsers.PE import API_ENDPOINT, fetch_production
from electricitymap.types import ZoneKey

# Base path for mock data files
MOCK_DATA_DIR = Path(__file__).parent / "mocks" / "PE"


def test_fetch_production_with_target_datetime(adapter, session, snapshot):
    """Test production data parsing for specific target datetime 2025-09-10."""

    def mock_response(request, context):
        """Mock response based on the request data."""
        # Parse the request data to determine which date is being requested
        form_data = request.text

        # Extract fechaInicial from the form data
        if (
            "fechaInicial=09%2F09%2F2025" in form_data
            or "fechaInicial=09/09/2025" in form_data
        ):
            # Request for 2025-09-09 (yesterday)
            mock_file = MOCK_DATA_DIR / "response_20250909.json"
        elif (
            "fechaInicial=10%2F09%2F2025" in form_data
            or "fechaInicial=10/09/2025" in form_data
        ):
            # Request for 2025-09-10 (target date)
            mock_file = MOCK_DATA_DIR / "response_20250910.json"
        else:
            # Default fallback
            mock_file = MOCK_DATA_DIR / "response_20250910.json"

        # Load and return the appropriate mock data
        with open(mock_file, encoding="utf-8") as f:
            return json.load(f)

    # Register the mock adapter
    adapter.register_uri(
        POST,
        API_ENDPOINT,
        json=mock_response,
    )

    # Test with target_datetime = 2025-09-10
    target_datetime = datetime(2025, 9, 10, 12, 0, 0)
    result = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=target_datetime,
    )

    # Verify the result using snapshot testing
    assert snapshot == result


def test_fetch_production_data_structure(adapter, session):
    """Test that the production data has the expected structure and values."""

    def mock_response(request, context):
        """Mock response that returns consistent data."""
        mock_file = MOCK_DATA_DIR / "response_20250910.json"
        with open(mock_file, encoding="utf-8") as f:
            return json.load(f)

    adapter.register_uri(
        POST,
        API_ENDPOINT,
        json=mock_response,
    )

    target_datetime = datetime(2025, 9, 10, 12, 0, 0)
    result = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=target_datetime,
    )

    # Basic structure checks
    assert isinstance(result, list)
    assert len(result) > 0

    # Check first production breakdown
    first_item = result[0]
    assert "zoneKey" in first_item
    assert "datetime" in first_item
    assert "production" in first_item
    assert "source" in first_item

    # Check that we have the expected energy sources
    production = first_item["production"]
    expected_sources = {"biomass", "hydro", "gas", "solar", "wind", "coal", "oil"}

    # Check that at least some expected sources are present
    production_sources = set(production.keys())
    assert len(production_sources.intersection(expected_sources)) > 0

    # Check that all values are numeric
    for _, value in production.items():
        assert isinstance(value, int | float)
        assert value >= 0  # Production values should be non-negative
