from datetime import datetime
from importlib import resources
from urllib.parse import parse_qs

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.parsers import occtonet
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.occtonet")
TARGET_DATETIME = datetime(2026, 10, 7, 12, tzinfo=occtonet.ZONE_INFO)


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    def respond(request, context):
        form = parse_qs(request.text)
        line = form["tgtRkl"][0]
        step = form["fwExtention.actionSubType"][0]
        extension = "csv" if step == "download" else "json"
        return MOCKS.joinpath(f"{line}_{step}.{extension}").read_bytes()

    requests_mock.register_uri(
        GET,
        "http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login",
        text="",
    )
    requests_mock.register_uri(
        POST,
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        content=respond,
    )


@pytest.mark.parametrize(
    "zone_key1, zone_key2",
    [
        # single line
        ("JP-CG", "JP-KY"),
        # two lines summed together
        ("JP-CB", "JP-HR"),
        # flow direction reverted
        ("JP-TK", "JP-CB"),
    ],
)
def test_snapshot_fetch_exchange(session, snapshot, zone_key1, zone_key2):
    assert snapshot == occtonet.fetch_exchange(
        ZoneKey(zone_key1),
        ZoneKey(zone_key2),
        session=session,
        target_datetime=TARGET_DATETIME,
    )


def test_snapshot_fetch_exchange_forecast(session, snapshot):
    assert snapshot == occtonet.fetch_exchange_forecast(
        ZoneKey("JP-CG"),
        ZoneKey("JP-KY"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )
