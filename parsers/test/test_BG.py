from datetime import datetime, timedelta, timezone

import pytest
import requests_mock
from freezegun import freeze_time

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from parsers.BG import SOURCE_API_URL, fetch_production


@pytest.fixture()
def fixture_requests_mock():
    """A mocker for requests.

    TODO(amv213): replace with builtin pytest 'requests_mock' fixture when upgrading to requests-mock>=1.5.0

    References:
        https://requests-mock.readthedocs.io/en/latest/mocker.html#using-the-mocker
    """
    with requests_mock.Mocker() as mock_requests:
        yield mock_requests


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production(fixture_requests_mock, snapshot):
    """That we can fetch the production mix at the current time."""
    mock_api_response = [
        ["NPP 47,31%", 2118.06],
        ["CHP 17,04%", 762.85],
        ["Heating TPPs 7,63%", 341.76],
        ["Factory TPPs 2,60%", 116.44],
        ["HPP 11,75%", 525.97],
        ["Small HPPs 5,65%", 252.82],
        ["Wind 3,99%", 178.62],
        ["PV 3,56%", 159.23],
        ["Bio 0,48%", 21.58],
    ]
    fixture_requests_mock.get(SOURCE_API_URL, json=mock_api_response)

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
    fixture_requests_mock.get(SOURCE_API_URL, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
        fetch_production(target_datetime=historical_datetime)
