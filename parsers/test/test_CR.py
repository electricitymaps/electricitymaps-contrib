import datetime
import json
import re

import pytest
import requests_mock
from freezegun import freeze_time

from parsers.CR import PRODUCTION_URL, TIMEZONE, fetch_production


@pytest.fixture()
def fixture_requests_mock():
    with requests_mock.Mocker() as mock_requests:
        yield mock_requests


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production_now(fixture_requests_mock, snapshot):
    """That we can fetch energy production values at the current time."""
    with open("parsers/test/mocks/CR/production_20240101.json") as f:
        mock_json_respose = json.load(f)
    fixture_requests_mock.get(re.compile(PRODUCTION_URL), json=mock_json_respose)

    production_breakdowns = fetch_production()

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
            for element in production_breakdowns
        ]
    )


def test_fetch_production_historical(fixture_requests_mock, snapshot):
    """That we can fetch historical energy production values."""
    with open("parsers/test/mocks/CR/production_20210716.json") as f:
        mock_json_respose = json.load(f)
    fixture_requests_mock.get(re.compile(PRODUCTION_URL), json=mock_json_respose)

    historical_datetime = datetime.datetime(2021, 7, 16, tzinfo=TIMEZONE)
    production_breakdowns = fetch_production(target_datetime=historical_datetime)

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
            for element in production_breakdowns
        ]
    )
