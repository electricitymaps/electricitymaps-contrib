import json
import re
from datetime import datetime, timedelta, timezone

import pytest
import requests_mock
from freezegun import freeze_time

from parsers.CR import (
    EXCHANGE_URL,
    PRODUCTION_URL,
    TIMEZONE,
    fetch_exchange,
    fetch_production,
)
from parsers.lib.exceptions import ParserException


@pytest.fixture()
def fixture_requests_mock():
    with requests_mock.Mocker() as mock_requests:
        yield mock_requests


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production_now(fixture_requests_mock, snapshot):
    """That we can fetch energy production values at the current time."""
    with open("parsers/test/mocks/CR/production_live.json") as f:
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

    historical_datetime = datetime(2021, 7, 16, tzinfo=TIMEZONE)
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


@freeze_time("2024-01-01 12:00:00")
def test_fetch_exchange_now(fixture_requests_mock, snapshot):
    """That we can fetch the last known power exchanges."""
    with open("parsers/test/mocks/CR/exchange_live.json") as f:
        mock_json_respose = json.load(f)
    fixture_requests_mock.get(EXCHANGE_URL, json=mock_json_respose)

    exchanges = fetch_exchange()

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "sortedZoneKeys": element["sortedZoneKeys"],
                "netFlow": element["netFlow"],
                "source": element["source"],
                "sourceType": element["sourceType"].value,
            }
            for element in exchanges
        ]
    )


def test_fetch_exchange_raises_parser_exception_on_historical_data(
    fixture_requests_mock,
):
    """That a ParserException is raised if requesting historical data (not supported yet)."""
    fixture_requests_mock.get(EXCHANGE_URL, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
        fetch_exchange(target_datetime=historical_datetime)
