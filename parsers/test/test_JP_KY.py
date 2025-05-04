import zoneinfo
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from parsers import JP_KY

TIMEZONE = ZoneInfo("Asia/Tokyo")


@pytest.fixture
def mock_csv_response_at_night():
    mock = MagicMock()
    with open("parsers/test/mocks/JP_KY/solar_and_consumption.csv") as f:
        mock.text = f.read()
    mock.encoding = "utf-8"
    return mock


@pytest.fixture
def mock_csv_response_at_day():
    mock = MagicMock()
    with open("parsers/test/mocks/JP_KY/solar_and_consumption_day.csv") as f:
        mock.text = f.read()
    mock.encoding = "utf-8"
    return mock


@pytest.fixture
def mock_nuclear_responses():
    """Fixture to create mock responses for nuclear power data."""
    sendai_mock = MagicMock()
    with open("parsers/test/mocks/JP_KY/sendai.html") as f:
        sendai_mock.text = f.read()

    genkai_mock = MagicMock()
    with open("parsers/test/mocks/JP_KY/genkai.html") as f:
        genkai_mock.text = f.read()

    return sendai_mock, genkai_mock


@pytest.fixture
def mock_exchange_data_night():
    """Fixture to create mock exchange data."""
    return [
        {
            "datetime": datetime(
                2025, 4, 24, 22, 45, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -100.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 24, 22, 50, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -200.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 24, 22, 55, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -300.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 24, 23, 00, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -400.0,
            "source": "occtonet.occto.or.jp",
        },
    ]


@pytest.fixture
def mock_exchange_data_day():
    """Fixture to create mock exchange data."""
    return [
        {
            "datetime": datetime(
                2025, 4, 25, 16, 30, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -200.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 25, 16, 35, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -100.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 25, 16, 40, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -400.0,
            "source": "occtonet.occto.or.jp",
        },
        {
            "datetime": datetime(
                2025, 4, 25, 16, 45, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -500.0,
            "source": "occtonet.occto.or.jp",
        },
    ]


def test_fetch_production_success_without_solar(
    mock_csv_response_at_night,
    mock_nuclear_responses,
    mock_exchange_data_night,
):
    """Test successful data retrieval and processing."""
    with (
        patch(
            "parsers.JP_KY.get",
            side_effect=[
                mock_csv_response_at_night,
                mock_nuclear_responses[0],
                mock_nuclear_responses[1],
            ],
        ),
        patch(
            "parsers.JP_KY.occtonet.fetch_exchange",
            return_value=mock_exchange_data_night,
        ),
    ):
        result = JP_KY.fetch_production()

        nuclear = 3119  # (119.7 + 96.1 + 96.1) * 10
        unknown = 5091  # 8010 - (-200) - 0 - nuclear

        assert result["zoneKey"] == "JP-KY"
        assert result["datetime"] == datetime(2025, 4, 24, 22, 50, tzinfo=TIMEZONE)
        assert result["production"]["solar"] == 0
        assert result["production"]["nuclear"] == nuclear
        assert result["production"]["unknown"] == unknown


def test_fetch_production_success_with_solar(
    mock_csv_response_at_day,
    mock_nuclear_responses,
    mock_exchange_data_day,
):
    """Test successful data retrieval and processing."""
    with (
        patch(
            "parsers.JP_KY.get",
            side_effect=[
                mock_csv_response_at_day,
                mock_nuclear_responses[0],
                mock_nuclear_responses[1],
            ],
        ),
        patch(
            "parsers.JP_KY.occtonet.fetch_exchange",
            return_value=mock_exchange_data_day,
        ),
    ):
        result = JP_KY.fetch_production()

        nuclear = 3119  # (119.7 + 96.1 + 96.1) * 10
        unknown = 3861  #  8680 - (-400) - 2100 - nuclear

        assert result["zoneKey"] == "JP-KY"
        assert result["datetime"] == datetime(2025, 4, 25, 16, 40, tzinfo=TIMEZONE)
        assert result["production"]["solar"] == 2100
        assert result["production"]["nuclear"] == nuclear
        assert result["production"]["unknown"] == unknown


def test_fetch_production_with_past_date():
    """Test that past dates are not supported."""
    with pytest.raises(NotImplementedError):
        JP_KY.fetch_production(target_datetime=datetime(2023, 1, 1))


def test_fetch_production_with_distant_exchange_data(
    mock_csv_response_at_night, mock_nuclear_responses
):
    """When the exchange data is more than 15 minutes from the consumption data, then we should return an empty list"""
    distant_exchange = [
        {
            "datetime": datetime(
                2025, 4, 25, 23, 10, tzinfo=zoneinfo.ZoneInfo(key="Asia/Tokyo")
            ),
            "sortedZoneKeys": "JP-CG->JP-KY",
            "netFlow": -200.0,
            "source": "occtonet.occto.or.jp",
        }
    ]

    with (
        patch(
            "requests.get",
            side_effect=[
                mock_csv_response_at_night,
                mock_nuclear_responses[0],
                mock_nuclear_responses[1],
            ],
        ),
        patch("parsers.JP_KY.occtonet.fetch_exchange", return_value=distant_exchange),
    ):
        result = JP_KY.fetch_production()
        assert result == []


def test_snapshot_fetch_production(
    snapshot,
    mock_csv_response_at_day,
    mock_nuclear_responses,
    mock_exchange_data_day,
):
    """Test successful data retrieval and processing."""
    with (
        patch(
            "parsers.JP_KY.get",
            side_effect=[
                mock_csv_response_at_day,
                mock_nuclear_responses[0],
                mock_nuclear_responses[1],
            ],
        ),
        patch(
            "parsers.JP_KY.occtonet.fetch_exchange",
            return_value=mock_exchange_data_day,
        ),
    ):
        result = JP_KY.fetch_production()

        assert snapshot == result
