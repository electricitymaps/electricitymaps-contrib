import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import POST

from electricitymap.contrib.lib.types import ZoneKey
from parsers import TR

base_path_to_mock = Path("parsers/test/mocks/TR")


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

    assert snapshot == TR.fetch_production(
        ZoneKey("TR"), session, target_datetime=target_datetime
    )
