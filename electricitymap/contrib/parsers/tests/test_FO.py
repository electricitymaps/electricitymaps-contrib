import json
from datetime import datetime, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.FO import fetch_production


@freeze_time("2024-05-16 12:04:00")
@pytest.mark.parametrize("zone", ["FO", "FO-MI", "FO-SI"])
def test_fetch_production_live(adapter, session, snapshot, zone):
    """That the parser fetches expected production values."""

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("electricitymap.contrib.parsers.tests.mocks.FO")
                    .joinpath(asset)
                    .read_text()
                )
            }
            for asset in ["sev_api_live_0.json", "sev_api_live_1.json"]
        ],
    )

    assert snapshot == fetch_production(ZoneKey(zone), session=session)


@pytest.mark.parametrize("zone", ["FO", "FO-MI", "FO-SI"])
@pytest.mark.parametrize("utc_offset", ["SDT", "DST"])
def test_fetch_production_historical(adapter, session, snapshot, zone, utc_offset):
    """That the parser fetches expected historical values.

    Given that API responses differ depending on whether SDT or DST apply for the target date, we also make sure
    that we handle both cases correctly.
    """

    month = 2 if utc_offset == "SDT" else 7
    target_datetime = datetime(2023, month, 16, 12, tzinfo=timezone.utc)

    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.FO")
            .joinpath(f"sev_api_historical_{target_datetime.strftime('%Y_%m_%d')}.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(
        ZoneKey(zone), target_datetime=target_datetime, session=session
    )
