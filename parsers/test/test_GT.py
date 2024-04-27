import json
from datetime import datetime
from importlib import resources

import pytest
import requests
import requests_mock
from freezegun import freeze_time
from requests_mock import ANY, GET

from parsers.GT import fetch_consumption, fetch_production


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, requests_mock.Adapter]:
    session = requests.Session()

    adapter = requests_mock.Adapter()
    session.mount("https://", adapter)

    return session, adapter


@freeze_time("2024-04-10 12:28:00")
def test_fetch_production_live(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("parsers.test.mocks.GT")
                    .joinpath(f"wl12_api_live_{i}.json")
                    .read_text()
                )
            }
            for i in range(2)
        ],
    )

    production = fetch_production(session=session)

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


def test_fetch_production_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("parsers.test.mocks.GT")
                    .joinpath(f"wl12_api_historical_20230716_{i}.json")
                    .read_text()
                )
            }
            for i in range(2)
        ],
    )

    historical_datetime = datetime.fromisoformat("2023-07-16T12:00:00+00:00")
    production = fetch_production(target_datetime=historical_datetime, session=session)

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


@freeze_time("2024-04-10 12:28:00")
def test_fetch_consumption_live(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("parsers.test.mocks.GT")
                    .joinpath(f"wl12_api_live_{i}.json")
                    .read_text()
                )
            }
            for i in range(2)
        ],
    )

    consumption = fetch_consumption(session=session)

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "consumption": element["consumption"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in consumption
        ]
    )


def test_fetch_consumption_historical(snapshot, fixture_session_mock):
    session, adapter = fixture_session_mock

    adapter.register_uri(
        GET,
        ANY,
        response_list=[
            {
                "json": json.loads(
                    resources.files("parsers.test.mocks.GT")
                    .joinpath(f"wl12_api_historical_20230716_{i}.json")
                    .read_text()
                )
            }
            for i in range(2)
        ],
    )

    historical_datetime = datetime.fromisoformat("2023-07-16T12:00:00+00:00")
    consumption = fetch_consumption(
        target_datetime=historical_datetime, session=session
    )

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "zoneKey": element["zoneKey"],
                "consumption": element["consumption"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in consumption
        ]
    )
