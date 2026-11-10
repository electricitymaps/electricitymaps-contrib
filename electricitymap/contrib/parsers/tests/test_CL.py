from collections import Counter
from datetime import datetime, timezone
from importlib import resources
from json import loads

import pytest
from freezegun import freeze_time
from requests import Session
from requests_mock import GET

from electricitymap.contrib.parsers import CL
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.CL")


@pytest.fixture(autouse=True)
def mock_response(requests_mock, monkeypatch):
    # One plant per technology. 2026-11-08 is complete, 2026-11-09 was still being
    # published when fetched on 2026-11-10 (no 23:00, few plants in the evening).
    monkeypatch.setenv("CL_SEN_SIP_API_KEY", "token")
    # Other days have no data (later registrations take precedence).
    requests_mock.register_uri(GET, CL.API_URL, json={"data": [], "totalPages": 0})
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


@freeze_time("2026-11-09 12:00:00")
def test_live_fetches_yesterday_and_today(session):
    production = CL.fetch_production(ZoneKey("CL-SEN"), session=session)

    hours_per_day = Counter(
        event["datetime"].date().isoformat() for event in production
    )
    assert hours_per_day == {"2026-11-08": 24, "2026-11-09": 23}


def test_returns_a_partially_published_day_as_it_is(session):
    production = CL.fetch_production(
        ZoneKey("CL-SEN"),
        session=session,
        target_datetime=datetime(2026, 11, 9, 12, tzinfo=timezone.utc),
    )

    # 2026-11-09's 23:00 is not published yet, so it is missing rather than zero.
    hours_per_day = Counter(
        event["datetime"].date().isoformat() for event in production
    )
    assert hours_per_day == {"2026-11-08": 24, "2026-11-09": 23}
    assert max(event["datetime"] for event in production).hour == 22


def test_refetch_fetches_the_week_up_to_the_target_day_one_day_at_a_time(
    session, requests_mock
):
    CL.fetch_production(
        ZoneKey("CL-SEN"),
        session=session,
        target_datetime=datetime(2026, 11, 8, 12, tzinfo=timezone.utc),
    )

    days = [request.qs["startdate"][0] for request in requests_mock.request_history]
    assert list(dict.fromkeys(days)) == [f"2026-11-0{day}" for day in range(2, 9)]


def test_retries_on_429():
    # requests_mock bypasses the HTTP adapter, so check the retry config it would use.
    session = CL.mount_retry(Session(), CL.RETRY)
    retry = session.adapters["https://"].max_retries
    assert 429 in retry.status_forcelist
    assert retry.backoff_jitter > 0
