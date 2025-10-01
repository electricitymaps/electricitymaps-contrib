from datetime import datetime
from zoneinfo import ZoneInfo

import freezegun
import pytest
from requests_mock import ANY

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.CENACE import fetch_consumption


@pytest.fixture(autouse=True)
def mock_response(adapter):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/DemandaRegional.html", "rb"
    ) as data:
        adapter.register_uri(ANY, ANY, content=data.read())


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_OC(session):
    data = fetch_consumption(ZoneKey("MX-OC"), session)
    assert data[0]["zoneKey"] == "MX-OC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Mexico_City"))
    assert data[0]["consumption"] == 8519.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_BC(session):
    data = fetch_consumption(ZoneKey("MX-BC"), session)
    assert data[0]["zoneKey"] == "MX-BC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Tijuana"))
    assert data[0]["consumption"] == 1587.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_BCS(session):
    data = fetch_consumption(ZoneKey("MX-BCS"), session)
    assert len(data) == 0
