import json
import os
import re
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers.BE import fetch_production

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/BE")

TARGET_DATETIME = datetime.fromisoformat("2024-01-01T02:00:00+00:00")
ENTSOE_ONLY_HOUR = "2024-01-01T00:00:00+00:00"
ELIA_QUARTERS = [
    "2024-01-01T01:00:00+00:00",
    "2024-01-01T01:30:00+00:00",
    "2024-01-01T01:45:00+00:00",
]


@pytest.fixture(autouse=True)
def mock_apis(requests_mock):
    os.environ["ENTSOE_TOKEN"] = "token"
    requests_mock.register_uri(
        GET,
        re.compile(r"https://entsoe-proxy"),
        content=(base_path_to_mock / "entsoe_production.xml").read_bytes(),
    )
    requests_mock.register_uri(
        GET,
        re.compile(r"https://opendata\.elia\.be"),
        json=json.loads((base_path_to_mock / "production.json").read_text()),
    )


@pytest.fixture
def production(session):
    return fetch_production("BE", session, TARGET_DATETIME)


@pytest.fixture
def by_datetime(production):
    return {event["datetime"].isoformat(): event for event in production}


def test_fetch_production(production, snapshot):
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == production


def test_merges_entsoe_hours_with_elia_quarters(by_datetime):
    # ENTSOE covers hours 00 and 01; Elia covers hour 01 with 3 of 4 slots
    # (01:15 is missing from the mock).
    assert sorted(by_datetime) == [ENTSOE_ONLY_HOUR, *ELIA_QUARTERS]


def test_hour_without_elia_data_falls_back_to_entsoe(by_datetime):
    event = by_datetime[ENTSOE_ONLY_HOUR]
    assert event["source"] == "entsoe.eu"
    assert event["production"]["gas"] == 700.0
    assert event["storage"] == {"battery": -30.0, "hydro": -150.0}


def test_elia_quarters_keep_entsoe_storage(by_datetime):
    # The hourly ENTSOE storage is step-held onto each 15-min slot, incl. pumping
    # (715 MW) which only ENTSOE reports (Elia ods201 has no consumption side).
    for dt in ELIA_QUARTERS:
        assert by_datetime[dt]["source"] == "entsoe.eu, opendata.elia.be"
        assert by_datetime[dt]["storage"] == {"battery": -25.0, "hydro": 715.0}


def test_elia_quarters_take_production_from_elia(by_datetime):
    assert by_datetime["2024-01-01T01:30:00+00:00"]["production"]["gas"] == 560.96
