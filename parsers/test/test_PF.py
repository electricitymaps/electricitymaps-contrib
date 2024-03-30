from datetime import datetime, timedelta, timezone

import pytest
import requests_mock
from freezegun import freeze_time

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from parsers.PF import PRODUCTION_API_URL, fetch_production


@pytest.fixture()
def fixture_requests_mock():
    with requests_mock.Mocker() as mock_requests:
        yield mock_requests


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production_live(fixture_requests_mock, snapshot):
    """That we can fetch the production mix at the current time."""
    with open("parsers/test/mocks/PF/production_live.html") as f:
        mock_api_response = f.read()
    fixture_requests_mock.get(PRODUCTION_API_URL, text=mock_api_response)

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


def test_fetch_production_raises_parser_exception_on_historical_data(
    fixture_requests_mock,
):
    """That a ParserException is raised if requesting historical data (not supported yet)."""
    fixture_requests_mock.get(PRODUCTION_API_URL, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
        fetch_production(target_datetime=historical_datetime)
