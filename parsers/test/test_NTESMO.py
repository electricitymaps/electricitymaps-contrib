from datetime import datetime, timezone
from json import loads
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import requests
from requests_mock import ANY, GET, Adapter

from parsers.NTESMO import (
    fetch_consumption,
    fetch_consumption_forecast,
    fetch_price,
    fetch_production,
)

australia = ZoneInfo("Australia/Darwin")


@pytest.fixture()
def fixture_session_mock(adapter, session) -> tuple[requests.Session, Adapter]:
    # do not mount mock adapter on generic https:// prefix or the parser's @retry_policy decorator will overwrite it
    session.mount("https://ntesmo.com.au/", adapter)

    index_page = """<div class="smp-tiles-article__item">
            <a href="https://ntesmo.com.au/__data/assets/excel_doc/0013/116113/Market-Information_System-Control-daily-trading-day_220401.xlsx">
                <div class="smp-tiles-article__title">01 December 2022</div>

                <div class="smp-tiles-article__lower d-flex flex-nowrap justify-content-between align-content-center align-items-center">
                    <div class="col-9 no-padding">
                        <strong>Download</strong>
                        <span>MS Excel Document (115.5 KB)</span>
                    </div>
                    <div class="col-3 no-padding d-flex justify-content-end">
                        <svg xmlns="http://www.w3.org/2000/svg" width="33" height="34" viewBox="0 0 33 34">
                            <path fill="currentColor" d="M-1223.7-1933.8h.2l.6.6.6-.6h.2v-.2l8.6-8.5-1.2-1.2-7.4 7.5v-22.6h-1.6v22.6l-7.4-7.5-1.2 1.2 8.6 8.5z" transform="translate(1239 1959)"></path>
                            <path fill="currentColor" class="st0" d="M-1207.8-1938.1v11.3h-29.4v-11.3h-1.6v12.9h32.6v-12.9z" transform="translate(1239 1959)"></path>
                        </svg>
                    </div>
                </div>
            </a>
        </div>"""

    with open("parsers/test/mocks/AU/NTESMO.xlsx", "rb") as data:
        adapter.register_uri(
            ANY,
            ANY,
            response_list=[
                # mock first call scraping historical page of links
                {"text": index_page},
                # mock second call reading contents of link
                {"content": data.read()},
            ],
        )

    return session, adapter


def test_fetch_production(fixture_session_mock):
    session, adapter = fixture_session_mock

    historical_datetime = datetime(year=2022, month=12, day=1, tzinfo=timezone.utc)
    data_list = fetch_production(session=session, target_datetime=historical_datetime)
    assert data_list is not None

    data_list = data_list[:2]
    expected_data = [
        {
            "production": {"gas": 96, "biomass": 13, "unknown": 0},
            "storage": {},
        },
        {
            "production": {"gas": 96, "biomass": 13, "unknown": 0},
            "storage": {},
        },
    ]
    assert len(data_list) == len(expected_data)

    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == "AU-NT"
        assert actual["source"] == "ntesmo.com.au"
        for production_type, production in actual["production"].items():
            assert production == expected_data[index]["production"][production_type]


def test_fetch_price(fixture_session_mock):
    session, adapter = fixture_session_mock

    historical_datetime = datetime(year=2022, month=12, day=1, tzinfo=timezone.utc)
    data_list = fetch_price(session=session, target_datetime=historical_datetime)

    assert data_list is not None
    expected_data = [
        {
            "price": 500,
            "currency": "AUD",
        }
    ] * 48
    assert len(data_list) == len(expected_data)
    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == "AU-NT"
        assert actual["source"] == "ntesmo.com.au"
        assert actual["price"] == expected_data[index]["price"]
        assert actual["currency"] == expected_data[index]["currency"]

    # Check that the dates corresponds to two days:

    assert data_list[0]["datetime"] == datetime(
        year=2022, month=12, day=1, hour=4, minute=30, tzinfo=australia
    )

    assert data_list[-1]["datetime"] == datetime(
        year=2022, month=12, day=2, hour=4, minute=00, tzinfo=australia
    )


def test_fetch_consumption(fixture_session_mock):
    session, adapter = fixture_session_mock

    historical_datetime = datetime(year=2022, month=12, day=1, tzinfo=timezone.utc)
    data_list = fetch_consumption(session=session, target_datetime=historical_datetime)

    assert data_list is not None

    expected_data = [
        {
            "consumption": 30,
        },
    ] * 48
    assert len(data_list) == len(expected_data)

    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == "AU-NT"
        assert actual["source"] == "ntesmo.com.au"
        assert actual["consumption"] == expected_data[index]["consumption"]

    # Check that the dates corresponds to two days:
    assert data_list[0]["datetime"] == datetime(
        year=2022, month=12, day=1, hour=4, minute=30, tzinfo=australia
    )
    assert data_list[-1]["datetime"] == datetime(
        year=2022, month=12, day=2, hour=4, minute=00, tzinfo=australia
    )


BASE_PATH_TO_MOCK = Path("parsers/test/mocks/NTESMO")


def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot):
    # Define mock URLs
    base_url = (
        "https://ntesmo.com.au/data/data-dashboard/2024-enhancements/demand-forecast"
    )
    endpoints = [
        f"{base_url}/darwin-katherine/dk-7-days-forecast",
        f"{base_url}/alice-springs/as-7-days-forecast",
        f"{base_url}/tennant-creek/tc-7-days-forecast",
    ]

    # Register mock responses
    for endpoint in endpoints:
        # For each url there is a mock file. Map each endpoint to its mock file
        mock_file_name = endpoint.split("/")[-1] + ".json"
        mock_data = Path(BASE_PATH_TO_MOCK, mock_file_name)

        # Mock request
        adapter.register_uri(GET, endpoint, json=loads(mock_data.read_text()))

    # Call the function under test
    result = fetch_consumption_forecast(zone_key="AU-NT", session=session)

    # Compare to snapshot
    assert snapshot == result
