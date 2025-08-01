import json
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import ANY

from parsers.OPENNEM import (
    fetch_exchange,
    fetch_price,
    fetch_production,
)

base_path_to_mock = Path("parsers/test/mocks/OPENNEM")


@pytest.mark.parametrize(
    "zone", ["AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"]
)
def test_production(adapter, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_{zone}.json")
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot == fetch_production(
        zone, session, datetime.fromisoformat("2025-03-23")
    )


@pytest.mark.parametrize("zone", ["AU-VIC"])
def test_price(adapter, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_{zone}.json")
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot == fetch_price(zone, session, datetime.fromisoformat("2025-03-23"))


def test_au_nsw_au_qld_exchange(adapter, session, snapshot):
    mock_data = Path(base_path_to_mock, "OPENNEM_AU-QLD.json")
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )

    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-QLD", session, datetime.fromisoformat("2025-07-17")
    )


def test_au_nsw_au_vic_exchange(adapter, session, snapshot):
    mock_data_qld = Path(base_path_to_mock, "OPENNEM_AU-QLD.json")
    mock_data_nsw = Path(base_path_to_mock, "OPENNEM_AU-NSW.json")

    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data_qld.read_text()),
    )

    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data_nsw.read_text()),
    )

    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-VIC", session, datetime.fromisoformat("2025-07-17")
    )
