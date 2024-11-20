import json
from datetime import datetime, timezone
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


@freeze_time("2024-05-16 12:04:00")
@pytest.mark.parametrize("zone", ["FO", "FO-MI", "FO-SI"])
def test_fetch_production_live(snapshot, fixture_session_mock, zone):
    """That the parser fetches expected production values."""
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("parsers.test.mocks.FO").joinpath(asset).read_text()
                )
            }
            for asset in ["sev_api_live_0.json", "sev_api_live_1.json"]
        ],
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


@pytest.mark.parametrize("zone", ["FO", "FO-MI", "FO-SI"])
@pytest.mark.parametrize("utc_offset", ["SDT", "DST"])
def test_fetch_production_historical(snapshot, fixture_session_mock, zone, utc_offset):
    """That the parser fetches expected historical values.

    Given that API responses differ depending on whether SDT or DST apply for the target date, we also make sure
    that we handle both cases correctly.
    """
    session, adapter = fixture_session_mock

    month = 2 if utc_offset == "SDT" else 7
    target_datetime = datetime(2023, month, 16, 12, tzinfo=timezone.utc)

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.FO")
            .joinpath(f"sev_api_historical_{target_datetime.strftime('%Y_%m_%d')}.json")
            .read_text()
        ),
    )

    production = fetch_production(
        ZoneKey(zone), target_datetime=target_datetime, session=session
    )

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
