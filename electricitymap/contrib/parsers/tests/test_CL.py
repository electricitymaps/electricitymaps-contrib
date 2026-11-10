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


@pytest.fixture(autouse=True)
def mock_response(requests_mock, monkeypatch):
    # One plant per technology. 2026-11-08 is complete, 2026-11-09 was still being
    # published when fetched on 2026-11-10 (no 23:00, few plants in the evening).
    monkeypatch.setenv("CL_SEN_SIP_API_KEY", "token")
    for day, page in (("2026-11-08", 1), ("2026-11-08", 2), ("2026-11-09", 1)):
        requests_mock.register_uri(
            GET,
            f"{CL.API_URL}?startDate={day}&endDate={day}&pageSize=10000&page={page}",
            json=loads(
                MOCKS.joinpath(
                    f"generacion_real_{day.replace('-', '')}_p{page}.json"
                ).read_text()
            ),
        )


def test_snapshot_historical_data(session, snapshot):
    assert snapshot == CL.fetch_production(
        ZoneKey("CL-SEN"),
        session=session,
        target_datetime=datetime(2026, 11, 8, 12, tzinfo=timezone.utc),
    )


@freeze_time("2026-11-10 12:00:00")
def test_live_falls_back_to_the_day_before_when_yesterday_is_incomplete(session):
    production = CL.fetch_production(ZoneKey("CL-SEN"), session=session)

    assert {event["datetime"].date().isoformat() for event in production} == {
        "2026-11-08"
    }


def test_raises_when_the_target_day_is_incomplete(session):
    with pytest.raises(ParserException, match="No completely published day"):
        CL.fetch_production(
            ZoneKey("CL-SEN"),
            session=session,
            target_datetime=datetime(2026, 11, 9, 12, tzinfo=timezone.utc),
        )


def test_retries_on_429():
    # requests_mock bypasses the HTTP adapter, so check the retry config it would use.
    session = CL.mount_retry(Session(), CL.RETRY)
    assert 429 in session.adapters["https://"].max_retries.status_forcelist
