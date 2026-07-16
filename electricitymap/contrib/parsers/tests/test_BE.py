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


@pytest.fixture(autouse=True)
def entsoe_token_env():
    os.environ["ENTSOE_TOKEN"] = "token"


def test_fetch_production(requests_mock, session, snapshot):
    entsoe_data = base_path_to_mock / "entsoe_production.xml"
    elia_data = base_path_to_mock / "production.json"

    requests_mock.register_uri(
        GET,
        re.compile(r"https://entsoe-proxy"),
        content=entsoe_data.read_bytes(),
    )
    requests_mock.register_uri(
        GET,
        re.compile(r"https://opendata\.elia\.be"),
        json=json.loads(elia_data.read_text()),
    )

    production = fetch_production(
        "BE",
        session,
        datetime.fromisoformat("2024-01-01T02:00:00+00:00"),
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == production

    by_datetime = {event["datetime"].isoformat(): event for event in production}
    # ENTSOE covers hours 00 and 01; Elia covers hour 01 with 3 of 4 slots
    # (01:15 is missing from the mock).
    assert sorted(by_datetime) == [
        "2024-01-01T00:00:00+00:00",
        "2024-01-01T01:00:00+00:00",
        "2024-01-01T01:30:00+00:00",
        "2024-01-01T01:45:00+00:00",
    ]

    # An hour without any Elia data falls back to the full ENTSOE event.
    fallback = by_datetime["2024-01-01T00:00:00+00:00"]
    assert fallback["source"] == "entsoe.eu"
    assert fallback["production"]["gas"] == 700.0
    assert fallback["storage"] == {"battery": -30.0, "hydro": -150.0}

    # 15-min slots: production from Elia, with the hourly ENTSOE storage
    # step-held onto each slot, incl. pumping (715 MW) which only ENTSOE
    # reports (Elia ods201 has no consumption side).
    for dt in (
        "2024-01-01T01:00:00+00:00",
        "2024-01-01T01:30:00+00:00",
        "2024-01-01T01:45:00+00:00",
    ):
        event = by_datetime[dt]
        assert event["source"] == "entsoe.eu, opendata.elia.be"
        assert event["storage"] == {"battery": -25.0, "hydro": 715.0}
    assert by_datetime["2024-01-01T01:30:00+00:00"]["production"]["gas"] == 560.96
