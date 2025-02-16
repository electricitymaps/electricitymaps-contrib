import json
from datetime import datetime
from unittest.mock import patch

import pytest

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ONS


@pytest.fixture(autouse=True)
def mock_response():
    with open("parsers/test/mocks/ONS/BR.json") as f:
        mock_data = json.load(f)
    with patch("parsers.ONS.get_data", return_value=mock_data):
        yield


def test_fetch_production():
    production = ONS.fetch_production(ZoneKey("BR-CS"))[0]
    assert production

    # Check that hydro keys correctly merge into one
    assert production["production"]["hydro"] == 35888.05363
    assert production["production"]["wind"] == 4.2
    assert production["datetime"] == datetime.fromisoformat("2018-01-27T20:19:00-02:00")
    assert production["source"] == "ons.org.br"
    assert production["zoneKey"] == "BR-CS"
    assert isinstance(production["storage"], dict)


def test_fetch_production_negative_solar():
    with open("parsers/test/mocks/ONS/BR_negative_solar.json") as f:
        mock_data = json.load(f)
    with patch("parsers.ONS.get_data", return_value=mock_data):
        production = ONS.fetch_production(ZoneKey("BR-CS"))[0]

    assert production["production"]["solar"] == 0


def test_fetch_exchange_UY():
    exchange = ONS.fetch_exchange("BR-S", "UY")[0]
    assert exchange
    assert exchange["sortedZoneKeys"] == "BR-S->UY"
    assert exchange["datetime"] == datetime.fromisoformat("2018-01-27T20:19:00-02:00")
    assert exchange["netFlow"] == 14.0
    assert exchange["source"] == "ons.org.br"


def test_fetch_exchange_BR_NE():
    exchange = ONS.fetch_exchange("BR-N", "BR-NE")[0]
    assert exchange
    assert exchange["sortedZoneKeys"] == "BR-N->BR-NE"
    assert exchange["datetime"] == datetime.fromisoformat("2018-01-27T20:19:00-02:00")
    assert exchange["netFlow"] == 2967.768
    assert exchange["source"] == "ons.org.br"
