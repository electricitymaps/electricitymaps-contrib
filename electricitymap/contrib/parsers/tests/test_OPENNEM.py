import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import ANY
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.OPENNEM import (
    _build_consumption_list,
    fetch_consumption,
    fetch_exchange,
    fetch_price,
    fetch_production,
)

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/OPENNEM")


@pytest.fixture(autouse=True)
def openelectricity_token_env():
    os.environ["OPENELECTRICITY_TOKEN"] = "token"


@pytest.mark.parametrize(
    "zone", ["AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"]
)
def test_production(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_{zone}.v4.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_production(zone, session, datetime.fromisoformat("2025-03-23"))


@pytest.mark.parametrize("zone", ["AU-SA"])
def test_price(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_price_{zone}.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_price(
        zone, session, datetime.fromisoformat("2020-01-01")
    )


@pytest.mark.parametrize("zone", ["AU-NSW", "AU-WA"])
def test_consumption(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_demand_{zone}.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_consumption(
        zone, session, datetime.fromisoformat("2025-03-23T10:00:00+00:00")
    )


@freeze_time("2026-07-22 10:12:00")
def test_build_consumption_list_skips_null_future_and_malformed():
    datasets = [
        {
            "metric": "demand",
            "results": [
                {
                    "data": [
                        ["2026-07-22T20:00:00+10:00", 1000.0],  # 10:00 UTC — keep
                        ["2026-07-22T20:05:00+10:00", None],  # null — skip
                        ["bad"],  # malformed — skip
                        ["2026-07-22T20:15:00+10:00", 1100.0],  # 10:15 UTC — future
                    ]
                }
            ],
        },
        {"metric": "price", "results": [{"data": [["2026-07-22T20:00:00+10:00", 50]]}]},
    ]

    events = _build_consumption_list(
        datasets, ZoneKey("AU-NSW"), logging.getLogger("test")
    ).to_list()

    assert len(events) == 1
    assert events[0]["consumption"] == 1000.0
    assert events[0]["datetime"] == datetime.fromisoformat("2026-07-22T20:00:00+10:00")


def test_au_nsw_au_qld_exchange(requests_mock, session, snapshot):
    # Exchange tests use the old v3 stats endpoint, so use v3 mock data
    mock_data = Path(base_path_to_mock, "OPENNEM_AU-QLD.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )

    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-QLD", session, datetime.fromisoformat("2025-07-17")
    )


def test_au_nsw_au_vic_exchange(requests_mock, session, snapshot):
    # Exchange tests use the old v3 stats endpoint, so use v3 mock data
    mock_data_qld = Path(base_path_to_mock, "OPENNEM_AU-QLD.json")
    mock_data_nsw = Path(base_path_to_mock, "OPENNEM_AU-NSW.json")

    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data_qld.read_text()),
    )

    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data_nsw.read_text()),
    )

    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-VIC", session, datetime.fromisoformat("2025-07-17")
    )
