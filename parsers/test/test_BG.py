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
def test_fetch_production(fixture_requests_mock):
    """That we can fetch the production mix at the current time."""
    mock_api_response = [
        ["АЕЦ 47,31%", 2118.06],
        ["Кондензационни ТЕЦ 17,04%", 762.85],
        ["Топлофикационни ТЕЦ 7,63%", 341.76],
        ["Заводски ТЕЦ 2,60%", 116.44],
        ["ВЕЦ 11,75%", 525.97],
        ["Малки ВЕЦ 5,65%", 252.82],
        ["ВяЕЦ 3,99%", 178.62],
        ["ФЕЦ 3,56%", 159.23],
        ["Био ЕЦ 0,48%", 21.58],
    ]
    fixture_requests_mock.get(SOURCE_API_URL, json=mock_api_response)

    expected_production_mix = {
        "biomass": 21.58,
        "coal": 762.85,
        "gas": 458.2,
        "geothermal": None,
        "hydro": 778.79,
        "nuclear": 2118.06,
        "oil": None,
        "solar": 159.23,
        "unknown": None,
        "wind": 178.62,
    }
    expected_storage_mix = {}

    production_breakdowns = fetch_production()

    assert len(production_breakdowns) == 1
    production_breakdown = production_breakdowns[0]
    assert production_breakdown["datetime"] == datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )
    assert production_breakdown["zoneKey"] == "BG"
    assert production_breakdown["production"] == expected_production_mix
    assert production_breakdown["storage"] == expected_storage_mix


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
