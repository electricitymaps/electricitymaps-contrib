import os
from datetime import datetime
from json import loads
from pathlib import Path

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers import NORDPOOL

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/NORDPOOL")


@pytest.fixture(autouse=True)
def emaps_env():
    os.environ["EMAPS_NORDPOOL_USERNAME"] = "username"
    os.environ["EMAPS_NORDPOOL_PASSWORD"] = "password"


def test_price_parser_se(adapter, session, snapshot):
    mock_token = Path(base_path_to_mock, "token.json")
    mock_data_current_day = Path(base_path_to_mock, "se_current_day_price.json")
    mock_data_next_day = Path(base_path_to_mock, "se_next_day_price.json")

    adapter.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(mock_token.read_text()),
    )
    adapter.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-08",
        json=loads(mock_data_current_day.read_text()),
    )
    adapter.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-09",
        json=loads(mock_data_next_day.read_text()),
    )

    assert snapshot == NORDPOOL.fetch_price(
        zone_key=ZoneKey("SE-SE4"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-07-08"),
    )


def test_exchange_parser_fi_se1(adapter, session, snapshot):
    mock_token = Path(base_path_to_mock, "token.json")
    mock_data_current_day = Path(base_path_to_mock, "fi_se1_current_day_exchange.json")
    mock_data_previous_day = Path(
        base_path_to_mock, "fi_se1_previous_day_exchange.json"
    )

    adapter.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(mock_token.read_text()),
    )
    adapter.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-12-01",
        json=loads(mock_data_current_day.read_text()),
    )
    adapter.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-11-30",
        json=loads(mock_data_previous_day.read_text()),
    )

    assert snapshot == NORDPOOL.fetch_exchange(
        zone_key1=ZoneKey("FI"),
        zone_key2=ZoneKey("SE-SE1"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-12-01"),
    )
