from datetime import datetime, timezone
from importlib import resources
from json import loads

import pytest
from freezegun import freeze_time
from requests_mock import GET

from electricitymap.contrib.parsers.CL import API_URL, fetch_production
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.CL")


@pytest.fixture(autouse=True)
def mock_response(requests_mock, monkeypatch):
    monkeypatch.setenv("CL_SEN_SIP_API_KEY", "token")
    for day, page in (("2026-11-07", 1), ("2026-11-08", 1), ("2026-11-08", 2)):
        requests_mock.register_uri(
            GET,
            f"{API_URL}?startDate={day}&endDate={day}&page={page}",
            json=loads(
                MOCKS.joinpath(
                    f"generacion_real_{day.replace('-', '')}_p{page}.json"
                ).read_text()
            ),
        )


def test_snapshot_historical_data(session, snapshot):
    assert snapshot == fetch_production(
        ZoneKey("CL-SEN"),
        session=session,
        target_datetime=datetime(2026, 11, 8, 12, tzinfo=timezone.utc),
    )


@freeze_time("2026-11-09 15:00:00")
def test_live_skips_today_as_it_is_incomplete(session, requests_mock):
    production = fetch_production(ZoneKey("CL-SEN"), session=session)

    assert {event["datetime"].date().isoformat() for event in production} == {
        "2026-11-07",
        "2026-11-08",
    }
    assert "2026-11-09" not in {
        r.qs["startdate"][0] for r in requests_mock.request_history
    }
