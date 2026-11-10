import json
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import POST

from electricitymap.contrib.parsers.PE import API_ENDPOINT, fetch_production
from electricitymap.contrib.types import ZoneKey

# Base path for mock data files
MOCK_DATA_DIR = Path(__file__).parent / "mocks" / "PE"


def test_fetch_production_with_target_datetime(requests_mock, session, snapshot):
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

    # Register the mock requests_mock
    requests_mock.register_uri(
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


def test_fetch_production_data_structure(requests_mock, session):
    """Test that the production data has the expected structure and values."""

    def mock_response(request, context):
        """Mock response based on the requested date so the "yesterday" and
        "today" fetches return their own data instead of duplicating one day."""
        form_data = request.text
        if (
            "fechaInicial=09%2F09%2F2025" in form_data
            or "fechaInicial=09/09/2025" in form_data
        ):
            mock_file = MOCK_DATA_DIR / "response_20250909.json"
        else:
            mock_file = MOCK_DATA_DIR / "response_20250910.json"
        with open(mock_file, encoding="utf-8") as f:
            return json.load(f)

    requests_mock.register_uri(
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


def test_unknown_energy_source_is_skipped_with_a_warning(
    requests_mock, session, caplog
):
    with open(MOCK_DATA_DIR / "response_20250910.json", encoding="utf-8") as f:
        response = json.load(f)
    series = response["GraficoTipoCombustible"]["Series"]
    series.append({**series[0], "Name": "HIDRÓGENO"})
    requests_mock.register_uri(POST, API_ENDPOINT, json=response)

    result = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=datetime(2025, 9, 10, 12, 0, 0),
    )

    assert len(result) > 0
    assert "Unknown PE energy source 'HIDRÓGENO', skipped" in caplog.text


@pytest.mark.parametrize("swapped_labels", [True, False])
def test_solar_and_bagasse_are_told_apart_by_shape(
    requests_mock, session, swapped_labels
):
    # The fixtures have COES's current labels: solar under BAGAZO, bagasse under SOLAR.
    with open(MOCK_DATA_DIR / "response_20250910.json", encoding="utf-8") as f:
        response = json.load(f)
    if not swapped_labels:
        for series in response["GraficoTipoCombustible"]["Series"]:
            series["Name"] = {"BAGAZO": "SOLAR", "SOLAR": "BAGAZO"}.get(
                series["Name"], series["Name"]
            )
    requests_mock.register_uri(POST, API_ENDPOINT, json=response)

    result = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=datetime(2025, 9, 10, 12, 0, 0),
    )

    by_hour = {event["datetime"].hour: event["production"] for event in result}
    assert by_hour[2]["solar"] == 0
    assert by_hour[12]["solar"] > 500
    assert 0 < by_hour[12]["biomass"] < 200


def test_bagasse_is_not_taken_for_solar_before_peru_had_solar(requests_mock, session):
    # Before ~2012-10 the solar series (labelled BAGAZO) is 0 all day.
    with open(MOCK_DATA_DIR / "response_20250910.json", encoding="utf-8") as f:
        response = json.load(f)
    for series in response["GraficoTipoCombustible"]["Series"]:
        if series["Name"] == "BAGAZO":
            for point in series["Data"]:
                point["Valor"] = 0
    requests_mock.register_uri(POST, API_ENDPOINT, json=response)

    result = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=datetime(2025, 9, 10, 12, 0, 0),
    )

    assert all(event["production"]["solar"] == 0 for event in result)
    assert all(event["production"]["biomass"] > 0 for event in result)
