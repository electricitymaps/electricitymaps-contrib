from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest
from freezegun import freeze_time
from requests_mock import POST

from electricitymap.contrib.lib.types import ZoneKey
from parsers.PE import API_ENDPOINT, fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    with open("parsers/test/mocks/PE/response_20240205.json", "rb") as mock_file:
        adapter.register_uri(
            POST,
            API_ENDPOINT,
            response_list=[
                {"content": mock_file.read()},
            ],
        )


def test_fetch_production(session, snapshot):
    assert snapshot == fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
    )


@freeze_time("2024-02-06 10:00:00", tz_offset=-5)
def test_api_requests_are_sent_with_correct_dates(adapter, session):
    end_date = "06/02/2024"
    yesterday = "05/02/2024"
    expected_today_request_data = urlencode(
        {"fechaInicial": yesterday, "fechaFinal": end_date, "indicador": 0}
    )

    fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
        target_datetime=datetime(2024, 2, 6, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert adapter.called
    actual_today_request_data = adapter.request_history[0].text
    assert expected_today_request_data == actual_today_request_data
