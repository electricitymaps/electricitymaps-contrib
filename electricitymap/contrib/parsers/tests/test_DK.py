from datetime import datetime
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import DK


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    requests_mock.register_uri(
        GET,
        DK.EXCHANGE_URL,
        json=loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.DK")
            .joinpath("ElectricityProdex5MinRealtime.json")
            .read_text()
        ),
    )

    requests_mock.register_uri(
        GET,
        DK.FORECAST_URL,
        json=loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.DK")
            .joinpath("Forecasts_5Min.json")
            .read_text()
        ),
    )


def test_fetch_exchange(session, snapshot):
    target_datetime = datetime(2025, 2, 21)

    assert snapshot == DK.fetch_exchange(
        "DK-DK2",
        "SE-SE4",
        session=session,
        target_datetime=target_datetime,
    )


def test_fetch_forecast(session, snapshot):
    target_datetime = datetime(2025, 2, 21)

    assert snapshot == DK.fetch_wind_solar_forecasts(
        "DK-DK1",
        session=session,
        target_datetime=target_datetime,
    )


def test_fetch_exchange_unsupported_pair():
    with pytest.raises(DK.ParserException) as exc_info:
        DK.fetch_exchange("DK-DK1", "FR")
    assert "Only able to fetch data for exchanges that are connected to Denmark" in str(
        exc_info.value
    )


def test_fetch_forecast_unsupported_zone():
    with pytest.raises(DK.ParserException) as exc_info:
        DK.fetch_wind_solar_forecasts("FR")
    assert "Only able to fetch forecasts for zones" in str(exc_info.value)


def test_fetch_data_no_records_none_datetime(requests_mock):
    requests_mock.register_uri(
        GET,
        DK.EXCHANGE_URL,
        json={"total": 0, "records": []},
    )
    with pytest.raises(DK.ParserException) as exc_info:
        DK.fetch_exchange("DK-DK2", "SE-SE4", target_datetime=None)
    assert "No exchange data was returned for" in str(exc_info.value)


def test_fetch_data_http_error_none_datetime(requests_mock):
    requests_mock.register_uri(
        GET,
        DK.EXCHANGE_URL,
        status_code=500,
    )
    with pytest.raises(DK.ParserException) as exc_info:
        DK.fetch_exchange("DK-DK2", "SE-SE4", target_datetime=None)
    assert "No exchange data was returned for" in str(exc_info.value)
