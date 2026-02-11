import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import POST
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import TR
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/TR")


@pytest.fixture(autouse=True)
def tr_credentials_env():
    os.environ["TR_USERNAME"] = "test_username"
    os.environ["TR_PASSWORD"] = "test_password"


@pytest.mark.parametrize(
    "target_datetime",
    [
        None,
        datetime(2025, 7, 28, 10, 0),
    ],
)
def test_fetch_production(adapter, session, snapshot, target_datetime):
    # Mock the TGT ticket fetch - return a simple ticket string without newlines
    adapter.register_uri(
        POST,
        "https://giris.epias.com.tr/cas/v1/tickets",
        text="TGT-1234567890-abcdefghijklmnop-cas",
    )

    # Load mock production data from raw API response
    raw_response = json.loads(
        (base_path_to_mock / "raw_production_response.json").read_text()
    )

    # Mock the production data API response with empty items to end pagination
    adapter.register_uri(
        POST,
        "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/realtime-generation",
        [
            {"json": raw_response},
            {"json": {"items": []}},  # Empty response to end pagination
        ],
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == TR.fetch_production(
        ZoneKey("TR"), session, target_datetime=target_datetime
    )
