from datetime import datetime, timezone
from importlib import resources
from json import loads

import pytest
from freezegun import freeze_time
from requests import Session
from requests_mock import GET

from electricitymap.contrib.parsers import CL
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.CL")
TARGET_DATETIME = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
# The fixture has 34 rows for 2026-11-08 (one plant per technology, two hours).
PREVIOUS_DAY_COUNT_URL = (
    f"{CL.API_URL}?startDate=2026-11-07&endDate=2026-11-07&pageSize=1&page=1"
)


@pytest.fixture(autouse=True)
def mock_response(requests_mock, monkeypatch):
    monkeypatch.setenv("CL_SEN_SIP_API_KEY", "token")
    for page in (1, 2):
        requests_mock.register_uri(
            GET,
            f"{CL.API_URL}?startDate=2026-11-08&endDate=2026-11-08&pageSize=10000&page={page}",
            json=loads(
                MOCKS.joinpath(f"generacion_real_20261108_p{page}.json").read_text()
            ),
        )
    requests_mock.register_uri(GET, PREVIOUS_DAY_COUNT_URL, json={"totalPages": 35})


def test_snapshot_historical_data(session, snapshot):
    assert snapshot == CL.fetch_production(
        ZoneKey("CL-SEN"), session=session, target_datetime=TARGET_DATETIME
    )


@freeze_time("2026-11-09 15:00:00")
def test_live_fetches_yesterday_as_today_is_incomplete(session):
    production = CL.fetch_production(ZoneKey("CL-SEN"), session=session)

    assert {event["datetime"].date().isoformat() for event in production} == {
        "2026-11-08"
    }


def test_raises_when_the_day_has_far_fewer_rows_than_the_day_before(
    session, requests_mock
):
    requests_mock.register_uri(GET, PREVIOUS_DAY_COUNT_URL, json={"totalPages": 100})
    with pytest.raises(ParserException, match="looks incomplete"):
        CL.fetch_production(
            ZoneKey("CL-SEN"), session=session, target_datetime=TARGET_DATETIME
        )


def test_retries_on_429():
    # requests_mock bypasses the HTTP adapter, so check the retry config it would use.
    session = CL.mount_retry(Session(), CL.RETRY)
    assert 429 in session.adapters["https://"].max_retries.status_forcelist
