import json
from importlib import resources

import pytest
import requests
import requests_mock
from freezegun import freeze_time
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.FO import fetch_production


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, requests_mock.Adapter]:
    session = requests.Session()

    adapter = requests_mock.Adapter()
    session.mount("https://", adapter)

    return session, adapter


@freeze_time("2024-05-06 08:17:00")
@pytest.mark.parametrize("zone", ["FO", "FO-MI", "FO-SI"])
def test_fetch_production_live(snapshot, fixture_session_mock, zone):
    """That the parser fetches expected production values."""
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.FO")
            .joinpath("sev_api_live.json")
            .read_text()
        ),
    )

    production = fetch_production(ZoneKey(zone), session=session)

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "production": element["production"],
                "storage": element["storage"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
                "correctedModes": element["correctedModes"],
            }
            for element in production
        ]
    )
