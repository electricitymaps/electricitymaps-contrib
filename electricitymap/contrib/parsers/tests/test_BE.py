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


def test_fetch_production(adapter, session, snapshot):
    entsoe_data = base_path_to_mock / "entsoe_production.xml"
    elia_data = base_path_to_mock / "production.json"

    adapter.register_uri(
        GET,
        re.compile(r"https://entsoe-proxy"),
        content=entsoe_data.read_bytes(),
    )
    adapter.register_uri(
        GET,
        re.compile(r"https://opendata\.elia\.be"),
        json=json.loads(elia_data.read_text()),
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_production(
        "BE",
        session,
        datetime.fromisoformat("2024-01-01T02:00:00+00:00"),
    )
